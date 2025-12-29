"""
TrialHook - FLAML Trial Hook for MLflow Logging

使用 FLAML 的 log 文件 + helper API 获取所有 trials 的详细信息，
为每个 trial 创建 MLflow 子 run，记录完整的参数和指标信息。

数据来源优先级：
1. FLAML log 文件（包含所有 trials 的完整信息）
2. AutoML.config_history（只包含改进的配置）
3. AutoML._search_states（每个估计器的最佳状态）
4. AutoML 的其他属性（best_estimator, best_config, best_loss 等）

这种方法不需要 monkey patching，更加稳定可靠。
"""
import mlflow
import time
import os
from typing import Any, Dict, List, Optional
from wedata_automl.utils.print_utils import safe_print


class TrialHook:
    """
    FLAML Trial Hook - 使用 log 文件 + helper API 获取所有 trials

    在 FLAML 训练完成后，使用以下数据源提取所有 trials 的信息：
    1. FLAML log 文件（最完整，包含所有 trials）
    2. AutoML.config_history（改进的配置）
    3. AutoML._search_states（每个估计器的最佳状态）
    4. AutoML 的其他属性（best_estimator, best_config, best_loss 等）

    为每个 trial 创建 MLflow 子 run 并记录完整的参数和指标。

    适用于所有任务类型（分类、回归、时序预测）。

    注意: 这个实现不使用 monkey patching，而是在训练完成后批量创建子 runs。
    """
    
    def __init__(
        self,
        parent_run_id: str,
        features: List[str],
        task: str,
        metric: str,
        enable_logging: bool = True
    ):
        """
        初始化 TrialHook

        Args:
            parent_run_id: 父 run 的 ID
            features: 特征列表
            task: 任务类型 (classification, regression, forecast)
            metric: 评估指标
            enable_logging: 是否启用日志记录（默认 True）
        """
        self.parent_run_id = parent_run_id
        self.features = features
        self.task = task
        self.metric = metric
        self.enable_logging = enable_logging

        # 存储所有 trial 的信息
        self.trial_runs: List[Dict[str, Any]] = []

        # 存储最佳 trial 信息
        self.best_trial_run_id: Optional[str] = None
        self.best_trial_run_name: Optional[str] = None
        self.best_trial_val_loss: float = float('inf')

        # 统计信息
        self.total_trials = 0
        self.trials_per_estimator: Dict[str, int] = {}
    
    def log_trials_from_automl(
        self,
        automl_instance,
        log_file_path: Optional[str] = None,
        feature_names: Optional[List[str]] = None,
        time_budget: Optional[int] = None,
        train_time: Optional[float] = None
    ):
        """
        从 AutoML 实例中提取所有 trials 的信息，并创建 MLflow 子 runs

        使用多种数据源（按优先级）：
        1. FLAML log 文件（最完整）
        2. AutoML.config_history（改进的配置）
        3. AutoML._search_states（每个估计器的最佳状态）

        同时使用 AutoML 的 helper API 获取额外信息：
        - best_estimator: 最佳估计器名称
        - best_config: 最佳配置
        - best_loss: 最佳损失
        - feature_names_in_: 特征名称（如果 AutoML 没有，则使用传入的 feature_names）
        - classes_: 分类任务的类别（如果有）

        Args:
            automl_instance: FLAML AutoML 实例（训练完成后）
            log_file_path: FLAML 训练日志文件路径（可选）
            feature_names: 特征名称列表（可选，如果 AutoML 没有 feature_names_in_ 时使用）
            time_budget: 时间预算（秒），可选
            train_time: 实际训练时间（秒），可选
        """
        if not self.enable_logging:
            safe_print("⚠️  TrialHook logging is disabled")
            return

        safe_print("", show_timestamp=False, show_level=False)
        safe_print("🔍 Extracting trials from FLAML AutoML using log + helper API...")

        # 首先从 AutoML 实例获取全局信息（使用 helper API）
        self._extract_global_info_from_automl(automl_instance, feature_names, time_budget, train_time)

        # 方法 1: 从日志文件读取（最完整，包含所有 trials）
        if log_file_path and os.path.exists(log_file_path):
            all_trials = self._extract_trials_from_log_file(log_file_path)
            if all_trials:
                safe_print(f"✅ Found {len(all_trials)} trials from log file")
                # 使用 AutoML helper API 增强 trial 信息
                all_trials = self._enrich_trials_with_automl_info(all_trials, automl_instance)
                self._create_trial_runs(all_trials, automl_instance)
                return

        # 方法 2: 从 config_history 读取（只包含改进的配置）
        if hasattr(automl_instance, 'config_history'):
            config_history = automl_instance.config_history
            if config_history:
                all_trials = []
                for iter_num, (estimator, config, time_stamp) in config_history.items():
                    trial_info = {
                        'estimator': estimator,
                        'trial_idx': iter_num,
                        'config': config,
                        'wall_clock_time': time_stamp,
                        'validation_loss': None,  # 不可用
                        'trial_time': None,  # 不可用
                    }
                    all_trials.append(trial_info)

                safe_print(f"✅ Found {len(all_trials)} improvement trials from config_history")
                # 使用 AutoML helper API 增强 trial 信息
                all_trials = self._enrich_trials_with_automl_info(all_trials, automl_instance)
                self._create_trial_runs(all_trials, automl_instance)
                return

        # 方法 3: 从 _search_states 读取（每个估计器的最佳状态）
        if hasattr(automl_instance, '_search_states'):
            all_trials = self._extract_trials_from_search_states(automl_instance)
            if all_trials:
                safe_print(f"✅ Found {len(all_trials)} best trials from _search_states")
                # 使用 AutoML helper API 增强 trial 信息
                all_trials = self._enrich_trials_with_automl_info(all_trials, automl_instance)
                self._create_trial_runs(all_trials, automl_instance)
                return

        safe_print("⚠️  WARNING: No trials found. Consider setting log_file_name in FLAML settings.")
        return

    def _extract_global_info_from_automl(
        self,
        automl_instance,
        feature_names: Optional[List[str]] = None,
        time_budget: Optional[int] = None,
        train_time: Optional[float] = None
    ):
        """
        从 AutoML 实例中提取全局信息（使用 helper API）

        Args:
            automl_instance: FLAML AutoML 实例
            feature_names: 特征名称列表（可选，如果 AutoML 没有 feature_names_in_ 时使用）
            time_budget: 时间预算（秒），可选
            train_time: 实际训练时间（秒），可选
        """
        # 提取全局信息
        self.automl_best_estimator = getattr(automl_instance, 'best_estimator', None)
        self.automl_best_config = getattr(automl_instance, 'best_config', {})
        self.automl_best_loss = getattr(automl_instance, 'best_loss', None)

        # 安全获取 feature_names_in_（可能不存在或为 None）
        # 优先使用 AutoML 的 feature_names_in_，如果没有则使用传入的 feature_names
        automl_feature_names = getattr(automl_instance, 'feature_names_in_', None)
        if automl_feature_names is not None:
            self.automl_feature_names = automl_feature_names
        elif feature_names is not None:
            self.automl_feature_names = feature_names
        else:
            self.automl_feature_names = []

        self.automl_classes = getattr(automl_instance, 'classes_', None)

        # 优先使用传入的 time_budget，否则尝试从 AutoML 实例获取
        if time_budget is not None:
            self.automl_time_budget = time_budget
        else:
            self.automl_time_budget = (
                getattr(automl_instance, '_time_budget', None) or
                getattr(automl_instance, 'time_budget', None) or
                getattr(automl_instance, '_state', {}).get('time_budget', None)
            )

        # 优先使用传入的 train_time，否则尝试从 AutoML 实例获取
        if train_time is not None:
            self.automl_train_time = train_time
        else:
            self.automl_train_time = (
                getattr(automl_instance, '_train_time', None) or
                getattr(automl_instance, 'train_time', None) or
                getattr(automl_instance, '_state', {}).get('train_time', None) or
                getattr(automl_instance, '_state', {}).get('total_time_used', None)
            )

        safe_print(f"📊 AutoML Global Info (from helper API):")
        safe_print(f"  - Best estimator: {self.automl_best_estimator}")
        safe_print(f"  - Best loss: {self.automl_best_loss}")
        safe_print(f"  - Time budget: {self.automl_time_budget}s")
        safe_print(f"  - Total train time: {self.automl_train_time:.2f}s" if self.automl_train_time else "  - Total train time: N/A")

        # 显示特征数量
        # 注意：feature_names 可能是 numpy array，不能直接用在 if 语句中
        if self.automl_feature_names is not None and len(self.automl_feature_names) > 0:
            safe_print(f"  - Feature count: {len(self.automl_feature_names)}")
        else:
            safe_print(f"  - Feature count: N/A")

        # 显示类别
        if self.automl_classes is not None:
            safe_print(f"  - Classes: {list(self.automl_classes)}")

    def _enrich_trials_with_automl_info(
        self,
        trials: List[Dict[str, Any]],
        automl_instance
    ) -> List[Dict[str, Any]]:
        """
        使用 AutoML helper API 增强 trial 信息

        Args:
            trials: 原始 trials 列表
            automl_instance: FLAML AutoML 实例

        Returns:
            增强后的 trials 列表
        """
        # 从 _search_states 获取每个估计器的详细信息
        search_states = getattr(automl_instance, '_search_states', {})

        for trial in trials:
            estimator = trial.get('estimator')

            # 标记是否为最佳 trial
            trial['is_best'] = (estimator == self.automl_best_estimator and
                               trial.get('config') == self.automl_best_config)

            # 从 search_states 获取估计器的详细信息
            if estimator in search_states:
                state = search_states[estimator]
                trial['search_state_info'] = {
                    'sample_size': getattr(state, 'sample_size', None),
                    'ls_ever_converged': getattr(state, 'ls_ever_converged', None),
                    'trained_estimator': getattr(state, 'trained_estimator', None),
                }

        return trials

    def _extract_trials_from_search_states(self, automl_instance) -> List[Dict[str, Any]]:
        """
        从 AutoML._search_states 中提取每个估计器的最佳 trial

        Args:
            automl_instance: FLAML AutoML 实例

        Returns:
            trials 列表
        """
        search_states = getattr(automl_instance, '_search_states', {})
        if not search_states:
            return []

        all_trials = []
        for estimator_name, state in search_states.items():
            # 获取最佳配置
            best_config = getattr(state, 'best_config', {})
            best_loss = getattr(state, 'best_loss', None)

            trial_info = {
                'estimator': estimator_name,
                'trial_idx': 0,  # 只有一个最佳配置
                'config': best_config,
                'validation_loss': best_loss,
                'trial_time': getattr(state, 'total_time_used', None),
                'wall_clock_time': None,
                'sample_size': getattr(state, 'sample_size', None),
                'is_best_for_estimator': True,
            }
            all_trials.append(trial_info)

        return all_trials

    def _extract_trials_from_log_file(self, log_file_path: str) -> List[Dict[str, Any]]:
        """
        从 FLAML 训练日志文件中提取所有 trials

        Args:
            log_file_path: 日志文件路径

        Returns:
            trials 列表
        """
        import json

        all_trials = []
        try:
            with open(log_file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        # 跳过 checkpoint 记录（只有一个字段）
                        if len(data) == 1:
                            continue

                        # 提取 trial 信息
                        trial_info = {
                            'estimator': data.get('learner'),
                            'trial_idx': data.get('record_id'),
                            'iter_per_learner': data.get('iter_per_learner'),
                            'config': data.get('config'),
                            'validation_loss': data.get('validation_loss'),
                            'trial_time': data.get('trial_time'),
                            'wall_clock_time': data.get('wall_clock_time'),
                            'logged_metric': data.get('logged_metric'),
                            'sample_size': data.get('sample_size'),
                        }
                        all_trials.append(trial_info)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            safe_print(f"⚠️  WARNING: Failed to read log file: {e}")
            return []

        return all_trials

    def _create_trial_runs(self, all_trials: List[Dict[str, Any]], automl_instance=None):
        """
        为所有 trials 创建 MLflow 子 runs（使用增强的信息）

        Args:
            all_trials: 所有 trials 的信息列表（已通过 helper API 增强）
            automl_instance: FLAML AutoML 实例（可选，用于获取额外信息）
        """
        safe_print(f"📝 Creating MLflow child runs for {len(all_trials)} trials...")

        # 按估计器分组统计
        estimator_counts: Dict[str, int] = {}

        # 全局计数器
        global_count = 0

        for trial in all_trials:
            estimator = trial['estimator']
            config = trial['config']

            # 更新计数器
            global_count += 1
            if estimator not in estimator_counts:
                estimator_counts[estimator] = 0
            estimator_counts[estimator] += 1
            local_count = estimator_counts[estimator]

            # 生成 run 名称（使用优化后的命名规范：补零）
            run_name = f"trial_{global_count:03d}_{estimator}"

            # 提取指标信息（支持两种数据源）
            val_loss = trial.get('validation_loss') or config.get('val_loss', float('inf'))
            train_time = trial.get('trial_time') or config.get('time_total_s', 0.0)

            try:
                # 创建嵌套 run
                with mlflow.start_run(run_name=run_name, nested=True) as trial_run:
                    trial_run_id = trial_run.info.run_id

                    # 记录基本参数
                    mlflow.log_param("estimator", estimator)
                    mlflow.log_param("trial_number_global", global_count)
                    mlflow.log_param("trial_number_local", local_count)
                    mlflow.log_param("parent_run_id", self.parent_run_id)
                    mlflow.log_param("task", self.task)

                    # 记录是否为最佳 trial（从增强信息中获取）
                    is_best = trial.get('is_best', False)
                    mlflow.log_param("is_best_trial", is_best)

                    # 记录超参数配置
                    for key, value in config.items():
                        # 跳过内部字段和指标字段
                        if key in ["val_loss", "time_total_s", "trained_estimator", "learner", "FLAML_sample_size"]:
                            continue
                        try:
                            mlflow.log_param(f"hp_{key}", value)
                        except Exception:
                            # 某些值可能无法序列化，转换为字符串
                            try:
                                mlflow.log_param(f"hp_{key}", str(value))
                            except Exception:
                                pass  # 忽略无法记录的参数

                    # 记录指标
                    if val_loss != float('inf'):
                        mlflow.log_metric("val_loss", val_loss)
                    if train_time > 0:
                        mlflow.log_metric("train_time", train_time)

                    # 记录额外的 trial 信息（从 log 文件或 search_states 获取）
                    if 'logged_metric' in trial and trial['logged_metric'] is not None:
                        # logged_metric 可能是 dict，需要展开记录
                        logged_metric = trial['logged_metric']
                        if isinstance(logged_metric, dict):
                            # 如果是 dict，展开记录每个指标
                            for metric_name, metric_value in logged_metric.items():
                                try:
                                    if isinstance(metric_value, (int, float)):
                                        mlflow.log_metric(f"logged_{metric_name}", metric_value)
                                    else:
                                        mlflow.log_param(f"logged_{metric_name}", str(metric_value))
                                except Exception:
                                    pass  # 忽略无法记录的指标
                        elif isinstance(logged_metric, (int, float)):
                            # 如果是数字，直接记录
                            mlflow.log_metric("logged_metric", logged_metric)

                    if 'sample_size' in trial and trial['sample_size'] is not None:
                        mlflow.log_param("sample_size", trial['sample_size'])
                    if 'iter_per_learner' in trial and trial['iter_per_learner'] is not None:
                        mlflow.log_param("iter_per_learner", trial['iter_per_learner'])
                    if 'wall_clock_time' in trial and trial['wall_clock_time'] is not None:
                        mlflow.log_metric("wall_clock_time", trial['wall_clock_time'])

                    # 记录从 search_states 获取的额外信息
                    if 'search_state_info' in trial:
                        state_info = trial['search_state_info']
                        if state_info.get('sample_size') is not None:
                            mlflow.log_param("search_state_sample_size", state_info['sample_size'])
                        if state_info.get('ls_ever_converged') is not None:
                            mlflow.log_param("ls_ever_converged", state_info['ls_ever_converged'])

                    # 记录 tags
                    mlflow.set_tag("trial_type", "best" if is_best else "regular")
                    mlflow.set_tag("estimator_family", estimator)
                    # 🆕 标记子 run 没有注册模型（用于后端返回空数组而不是 null）
                    mlflow.set_tag("wedata.has_registered_model", "false")
                    # 🆕 设置 datascience.type 为 MACHINE_LEARNING，否则后续操作子 run 会被服务器拒绝
                    mlflow.set_tag("wedata.datascience.type", "MACHINE_LEARNING")

                    # 🆕 设置 wedata.project（必须设置，否则 DLC 环境中 run 可能无法持久化）
                    project_id = os.environ.get("WEDATA_PROJECT_ID", "")
                    if project_id:
                        mlflow.set_tag("wedata.project", project_id)

                    # 🆕 设置 mlflow.user（必须设置，否则 DLC 环境中 run 可能无法持久化）
                    user_uin = os.environ.get("QCLOUD_SUBUIN") or os.environ.get("QCLOUD_UIN", "")
                    if user_uin:
                        mlflow.set_tag("mlflow.user", user_uin)

                    # 存储 trial 信息
                    trial_info = {
                        "run_id": trial_run_id,
                        "run_name": run_name,
                        "trial_number_global": global_count,
                        "trial_number_local": local_count,
                        "estimator": estimator,
                        "val_loss": val_loss,
                        "train_time": train_time,
                        "is_best": is_best,
                    }
                    self.trial_runs.append(trial_info)

                # 🆕 在子 run 结束后，删除 mlflow.source.name tag
                # 这样只有最佳子 run 会保留 source.name（通过 set_best_trial_tags 设置）
                try:
                    client = mlflow.tracking.MlflowClient()
                    client.delete_tag(trial_run_id, "mlflow.source.name")
                except Exception:
                    pass  # tag 可能不存在或删除失败，忽略错误

                # 更新最佳 trial 信息
                if val_loss < self.best_trial_val_loss:
                    self.best_trial_val_loss = val_loss
                    self.best_trial_run_id = trial_run_id
                    self.best_trial_run_name = run_name

                # 打印进度信息（每 10 个 trial 打印一次）
                if global_count % 10 == 0 or global_count == len(all_trials):
                    safe_print(
                        f"  Progress: {global_count}/{len(all_trials)} trials logged"
                    )

            except Exception as e:
                safe_print(f"❌ ERROR: Failed to create MLflow run for trial {global_count} ({estimator}): {e}")
                import traceback
                safe_print(f"   Traceback: {traceback.format_exc()}")
                # 继续处理下一个 trial
                continue

        # 更新统计信息
        self.total_trials = global_count
        self.trials_per_estimator = estimator_counts

        safe_print(f"✅ Successfully created {len(self.trial_runs)} MLflow child runs")

    def get_summary(self) -> Dict[str, Any]:
        """
        获取 hook 的统计摘要

        Returns:
            包含统计信息的字典
        """
        return {
            "total_trials": self.total_trials,
            "trials_per_estimator": dict(self.trials_per_estimator),
            "best_trial_run_id": self.best_trial_run_id,
            "best_trial_run_name": self.best_trial_run_name,
            "best_trial_val_loss": self.best_trial_val_loss,
        }

    def print_summary(self):
        """
        打印 hook 的统计摘要
        """
        summary = self.get_summary()

        safe_print("", show_timestamp=False, show_level=False)
        safe_print("=" * 80, show_timestamp=False, show_level=False)
        safe_print("📊 TrialHook Summary", show_timestamp=False, show_level=False)
        safe_print("=" * 80, show_timestamp=False, show_level=False)
        safe_print(f"Total trials logged: {summary['total_trials']}")
        safe_print(f"Trials per estimator:")
        for estimator, count in summary['trials_per_estimator'].items():
            safe_print(f"  - {estimator}: {count} trials")
        safe_print(f"Best trial:")
        safe_print(f"  - Run ID: {summary['best_trial_run_id']}")
        safe_print(f"  - Run Name: {summary['best_trial_run_name']}")
        safe_print(f"  - Val Loss: {summary['best_trial_val_loss']:.6f}")
        safe_print("=" * 80, show_timestamp=False, show_level=False)

    def set_best_trial_tags(
        self,
        source_name: Optional[str] = "wedata-automl",
        project_id: Optional[str] = None,
        task: Optional[str] = None,
        workflow_id: Optional[str] = None,
        user_uin: Optional[str] = None,
        total_trials_run: Optional[int] = None,
    ) -> bool:
        """
        为最佳子 run 设置所有必要的 tag

        设置的 tag 包括：
        - mlflow.source.name: 来源标识（如果 source_name 为 None 则不设置）
        - wedata.project: 项目 ID
        - wedata.datascience.type: 任务类型
        - wedata.workflowId: 工作流 ID
        - mlflow.user: 用户 UIN
        - wedata.total_trials_run: 总运行次数
        - wedata.best_run_id: 最佳子 run ID（指向自己）
        - wedata.best_run_name: 最佳子 run 名称
        - wedata.is_best_trial: 是否为最佳 trial（标记为 true）

        Args:
            source_name: 要设置的 source.name 值，默认为 "wedata-automl"。
                如果为 None 则不设置 mlflow.source.name（用于 forecast 任务）
            project_id: 项目 ID，如果为 None 则从环境变量 WEDATA_PROJECT_ID 读取
            task: 任务类型，如果为 None 则使用 self.task
            workflow_id: 工作流 ID，如果为 None 则从环境变量 WEDATA_WORKFLOW_ID 读取
            user_uin: 用户 UIN，如果为 None 则从环境变量读取
            total_trials_run: 总运行次数，如果为 None 则使用 self.total_trials

        Returns:
            是否设置成功
        """
        if not self.best_trial_run_id:
            safe_print("⚠️  No best trial run ID available")
            return False

        try:
            client = mlflow.tracking.MlflowClient()

            # 准备要设置的 tags
            tags_to_set = {}

            # 1. mlflow.source.name（如果 source_name 为 None 则不设置）
            if source_name is not None:
                tags_to_set["mlflow.source.name"] = source_name

            # 2. wedata.project
            project = project_id or os.environ.get("WEDATA_PROJECT_ID", "")
            if project:
                tags_to_set["wedata.project"] = project

            # 3. wedata.datascience.type - 必须设置为 MACHINE_LEARNING，否则服务器会拒绝操作
            tags_to_set["wedata.datascience.type"] = "MACHINE_LEARNING"

            # 4. wedata.workflowId
            workflow = workflow_id or os.environ.get("WEDATA_WORKFLOW_ID", "")
            if workflow:
                tags_to_set["wedata.workflowId"] = workflow

            # 5. mlflow.user
            user = user_uin or os.environ.get("WEDATA_USER_UIN") or os.environ.get("USER_UIN", "")
            if user:
                tags_to_set["mlflow.user"] = user

            # 6. wedata.total_trials_run - 总运行次数
            total_trials = total_trials_run if total_trials_run is not None else self.total_trials
            tags_to_set["wedata.total_trials_run"] = str(total_trials)

            # 7. wedata.best_run_id - 最佳子 run ID（指向自己）
            tags_to_set["wedata.best_run_id"] = self.best_trial_run_id

            # 8. wedata.best_run_name - 最佳子 run 名称
            if self.best_trial_run_name:
                tags_to_set["wedata.best_run_name"] = self.best_trial_run_name

            # 9. wedata.is_best_trial - 标记为最佳 trial
            tags_to_set["wedata.is_best_trial"] = "true"

            # 设置所有 tags
            for tag_key, tag_value in tags_to_set.items():
                try:
                    client.set_tag(self.best_trial_run_id, tag_key, tag_value)
                except Exception as tag_err:
                    safe_print(f"⚠️  Failed to set tag '{tag_key}': {tag_err}")

            safe_print(f"✅ Set tags on best trial run: {self.best_trial_run_id}")
            for tag_key, tag_value in tags_to_set.items():
                safe_print(f"   {tag_key}: {tag_value or '(empty)'}")

            return True
        except Exception as e:
            safe_print(f"⚠️  Failed to set tags on best trial: {e}")
            return False

    def set_best_trial_source_name(self, source_name: str = "wedata-automl") -> bool:
        """
        为最佳子 run 设置 mlflow.source.name tag（简化版本）

        注意：推荐使用 set_best_trial_tags() 方法设置所有必要的 tag

        Args:
            source_name: 要设置的 source.name 值，默认为 "wedata-automl"

        Returns:
            是否设置成功
        """
        # 调用完整的 tag 设置方法
        return self.set_best_trial_tags(source_name=source_name)

    def cleanup_child_runs_source_name(self, experiment_id: str, preserve_best: bool = True) -> int:
        """
        清理子 run 的 mlflow.source.name tag，保留最佳子 run 的 tag

        在训练完成后调用此方法，删除非最佳子 run 的 mlflow.source.name tag。
        最佳子 run 会保留或设置正确的 source.name。

        Args:
            experiment_id: MLflow 实验 ID
            preserve_best: 是否保留最佳子 run 的 source.name（默认 True）

        Returns:
            成功清理的子 run 数量
        """
        if not self.parent_run_id:
            return 0

        cleaned_count = 0
        try:
            client = mlflow.tracking.MlflowClient()

            # 使用已记录的子 run IDs（从 TrialHook 内部记录）
            # 这样可以避免 search_runs API 的兼容性问题
            # trial_runs 是一个列表，每个元素包含 run_id
            child_run_ids = [t.get("run_id") for t in self.trial_runs if t.get("run_id")] if self.trial_runs else []

            if not child_run_ids:
                # 如果没有记录，尝试通过 search_runs 查找（备用方案）
                try:
                    child_runs = client.search_runs(
                        experiment_ids=[experiment_id],
                        filter_string=f"tags.`mlflow.parentRunId` = '{self.parent_run_id}'",
                        max_results=1000
                    )
                    child_run_ids = [run.info.run_id for run in child_runs]
                except Exception as search_err:
                    # 某些 MLflow 服务器可能不支持复杂的 filter
                    safe_print(f"⚠️  search_runs failed: {search_err}")
                    # 尝试不使用 filter，获取所有 runs 再过滤
                    try:
                        all_runs = client.search_runs(
                            experiment_ids=[experiment_id],
                            max_results=1000
                        )
                        child_run_ids = [
                            run.info.run_id for run in all_runs
                            if run.data.tags.get("mlflow.parentRunId") == self.parent_run_id
                        ]
                    except Exception:
                        pass

            # 删除非最佳子 run 的 mlflow.source.name tag
            for run_id in child_run_ids:
                # 如果是最佳子 run 且需要保留，跳过删除
                if preserve_best and run_id == self.best_trial_run_id:
                    continue

                try:
                    run = client.get_run(run_id)
                    if "mlflow.source.name" in run.data.tags:
                        client.delete_tag(run_id, "mlflow.source.name")
                        cleaned_count += 1
                except Exception:
                    pass  # 忽略单个删除失败

            if cleaned_count > 0:
                safe_print(f"🧹 Cleaned mlflow.source.name from {cleaned_count} non-best child runs")
        except Exception as e:
            safe_print(f"⚠️  Failed to cleanup child runs source.name: {e}")

        return cleaned_count

    def register_best_model_to_catalog(
        self,
        model_uri: str,
        model_name: str,
        region: str = "ap-beijing",
        description: Optional[str] = None,
        run_link: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        将最佳子 run 的模型注册到 TencentCloud Catalog

        Args:
            model_uri: 模型 URI，如 "runs:/{run_id}/model"
            model_name: 模型名称，格式为 "catalog.schema.model_name"
            region: 地域，默认 "ap-beijing"
            description: 模型描述
            run_link: MLflow run 链接

        Returns:
            注册结果字典，失败返回 None
        """
        if not self.best_trial_run_id:
            safe_print("⚠️  Catalog 注册跳过：没有最佳子 run")
            return None

        try:
            from .catalog_registry import register_model_to_catalog, is_catalog_registry_enabled

            if not is_catalog_registry_enabled():
                safe_print("⚠️  Catalog 注册跳过：未配置必要的环境变量")
                return None

            # 构建模型 URI（使用最佳子 run 的 ID）
            best_model_uri = model_uri or f"runs:/{self.best_trial_run_id}/model"

            # 额外的 tags
            tags = {
                "task": self.task,
                "metric": self.metric,
                "best_trial_run_name": self.best_trial_run_name or "",
            }

            result = register_model_to_catalog(
                model_uri=best_model_uri,
                model_name=model_name,
                run_id=self.best_trial_run_id,
                run_link=run_link,
                description=description,
                region=region,
                tags=tags,
            )

            return result

        except Exception as e:
            safe_print(f"⚠️  Catalog 注册失败: {e}")
            return None

