"""
FLAMLTrainer - FLAML 训练器

封装 FLAML 训练逻辑，支持 Databricks 风格的参数
"""
import traceback
from typing import Any, Dict, List, Optional, Union
import logging
import time
import os
import uuid
import tempfile
from datetime import datetime
import pandas as pd
import numpy as np

# 禁用 MLflow 2.15+ 的 LoggedModel 功能（避免与旧版 MLflow 服务器不兼容）
# 必须在 import mlflow 之前设置
os.environ.setdefault("MLFLOW_ENABLE_LOGGED_MODELS", "false")

import mlflow
from sklearn.pipeline import Pipeline as SkPipe

# Robust import for FLAML
try:
    from flaml import AutoML
    import flaml as flaml_pkg
except ImportError:
    try:
        from flaml.automl.automl import AutoML
        import flaml as flaml_pkg
    except ImportError as e:
        raise ImportError(
            "Cannot import AutoML from flaml. "
            "Please install flaml with AutoML support: pip install 'flaml[automl]==2.3.6'"
        ) from e

from wedata_automl.summary import AutoMLSummary
from wedata_automl.utils.sk_pipeline import build_numeric_preprocessor
from wedata_automl.utils.spark_utils import compute_split_and_weights
from wedata_automl.utils.print_utils import safe_print, print_separator, print_header
from wedata_automl.engines.trial_hook import TrialHook

logger = logging.getLogger(__name__)


# ============================================================================
# Log 文件管理辅助函数
# ============================================================================

def generate_log_file_path(
    base_dir: Optional[str] = None,
    run_id: Optional[str] = None,
    use_timestamp: bool = True,
    use_uuid: bool = True
) -> str:
    """
    生成唯一的 FLAML log 文件路径

    解决的问题：
    1. 避免重复 fit() 时 log 被覆盖
    2. 支持多进程/多节点环境
    3. 便于日志管理和清理

    Args:
        base_dir: 基础目录，默认使用系统临时目录
        run_id: MLflow run ID，用于关联 log 文件
        use_timestamp: 是否在文件名中包含时间戳
        use_uuid: 是否在文件名中包含 UUID

    Returns:
        log 文件的完整路径

    Example:
        >>> path = generate_log_file_path()
        >>> # /tmp/wedata_automl/flaml_20251125_143022_abc123_run456.log
    """
    # 确定基础目录
    if base_dir is None:
        # 使用系统临时目录 + wedata_automl 子目录
        base_dir = os.path.join(tempfile.gettempdir(), "wedata_automl", "flaml_logs")

    # 确保目录存在
    os.makedirs(base_dir, exist_ok=True)

    # 构建文件名
    parts = ["flaml"]

    if use_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts.append(timestamp)

    if use_uuid:
        short_uuid = str(uuid.uuid4())[:8]
        parts.append(short_uuid)

    if run_id:
        parts.append(f"run{run_id[:8]}")

    filename = "_".join(parts) + ".log"

    return os.path.join(base_dir, filename)


def cleanup_old_log_files(
    base_dir: Optional[str] = None,
    max_age_hours: int = 24,
    max_files: int = 100,
    dry_run: bool = False
) -> int:
    """
    清理旧的 FLAML log 文件

    解决的问题：
    1. 防止 log 文件累积过多
    2. 自动清理过期的 log 文件

    Args:
        base_dir: 基础目录，默认使用系统临时目录
        max_age_hours: 最大保留时间（小时），超过此时间的文件将被删除
        max_files: 最大保留文件数，超过此数量的旧文件将被删除
        dry_run: 是否只模拟运行（不实际删除）

    Returns:
        删除的文件数量

    Example:
        >>> # 删除 24 小时前的 log 文件
        >>> count = cleanup_old_log_files(max_age_hours=24)
        >>> print(f"Deleted {count} old log files")
    """
    if base_dir is None:
        base_dir = os.path.join(tempfile.gettempdir(), "wedata_automl", "flaml_logs")

    if not os.path.exists(base_dir):
        return 0

    import glob

    # 获取所有 log 文件
    log_files = glob.glob(os.path.join(base_dir, "flaml_*.log"))

    if not log_files:
        return 0

    # 按修改时间排序（最新的在前）
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for i, log_file in enumerate(log_files):
        should_delete = False
        reason = ""

        # 检查是否超过最大文件数
        if i >= max_files:
            should_delete = True
            reason = f"exceeds max_files ({max_files})"

        # 检查是否超过最大保留时间
        file_age = current_time - os.path.getmtime(log_file)
        if file_age > max_age_seconds:
            should_delete = True
            reason = f"older than {max_age_hours} hours"

        if should_delete:
            if dry_run:
                safe_print(f"[DRY RUN] Would delete: {log_file} ({reason})")
            else:
                try:
                    os.remove(log_file)
                    deleted_count += 1
                    safe_print(f"Deleted old log file: {log_file} ({reason})")
                except Exception as e:
                    safe_print(f"Failed to delete {log_file}: {e}")

    return deleted_count


# ============================================================================
# MLflow Artifact 日志记录辅助函数
# ============================================================================

def setup_mlflow_user_id() -> str:
    """
    设置 MLflow Run 的 user_id

    从环境变量 QCLOUD_UIN 获取用户 UIN，并设置到 MLFLOW_TRACKING_USERNAME 环境变量。
    MLflow 在创建 Run 时会自动使用此环境变量作为 RunInfo.user_id。

    Returns:
        用户 UIN 字符串
    """
    user_uin = os.environ.get("QCLOUD_SUBUIN", "")
    if user_uin:
        # 设置 MLFLOW_TRACKING_USERNAME，MLflow 会使用它作为 RunInfo.user_id
        os.environ["MLFLOW_TRACKING_USERNAME"] = user_uin
        safe_print(f"✅ Set MLFLOW_TRACKING_USERNAME (user_id): {user_uin}")
    else:
        safe_print("⚠️  QCLOUD_SUBUIN not found, user_id will be empty")
    return user_uin


def _get_wedata_tags(task: str = "classification") -> Dict[str, str]:
    """
    获取 WeData 平台相关的 tags

    从环境变量读取以下信息:
    - WEDATA_PROJECT_ID: 项目 ID
    - QCLOUD_UIN: 用户 UIN
    - KERNEL_SUBMIT_FORM_WORKFLOW: 工作流 ID

    Args:
        task: 任务类型 (classification/regression/forecast)

    Returns:
        WeData tags 字典
    """
    # 从环境变量获取 WeData 信息
    project_id = os.environ.get("WEDATA_PROJECT_ID", "")
    user_uin = os.environ.get("QCLOUD_SUBUIN", "")
    workflow_id = os.environ.get("KERNEL_SUBMIT_FORM_WORKFLOW", "")

    # 任务类型映射
    # datascience_type_map = {
    #     "classification": "AUTOML_CLASSIFICATION",
    #     "regression": "AUTOML_REGRESSION",
    #     "forecast": "AUTOML_PREDICTION",
    # }
    datascience_type = "MACHINE_LEARNING"

    return {
        "wedata.project": project_id,
        "wedata.datascience.type": datascience_type,
        "wedata.workflowId": workflow_id,
        "mlflow.user": user_uin,
    }


def set_run_wedata_tags(task: str = "classification") -> None:
    """
    为当前 MLflow Run 设置 WeData 平台相关的 tags

    Args:
        task: 任务类型 (classification/regression/forecast)
    """
    try:
        tags = _get_wedata_tags(task)
        mlflow.set_tags(tags)

        safe_print(f"✅ Set WeData tags on Run:")
        safe_print(f"   wedata.project: {tags['wedata.project'] or '(empty)'}")
        safe_print(f"   wedata.datascience.type: {tags['wedata.datascience.type']}")
        safe_print(f"   wedata.workflowId: {tags['wedata.workflowId'] or '(empty)'}")
        safe_print(f"   mlflow.user: {tags['mlflow.user'] or '(empty)'}")

    except Exception as e:
        logger.warning(f"Failed to set Run WeData tags: {e}")
        safe_print(f"⚠️  Failed to set WeData tags on Run: {e}")


def set_model_version_wedata_tags(
    registered_model_name: str,
    model_version: str,
    task: str = "classification"
) -> None:
    """
    为注册的模型版本设置 WeData 平台相关的 tags

    Args:
        registered_model_name: 注册模型名称
        model_version: 模型版本号
        task: 任务类型 (classification/regression/forecast)
    """
    try:
        client = mlflow.tracking.MlflowClient()
        tags = _get_wedata_tags(task)

        for tag_key, tag_value in tags.items():
            try:
                client.set_model_version_tag(
                    name=registered_model_name,
                    version=str(model_version),
                    key=tag_key,
                    value=tag_value or ""
                )
            except Exception as e:
                logger.warning(f"Failed to set model version tag {tag_key}: {e}")

        safe_print(f"✅ Set WeData tags on model version: {registered_model_name} v{model_version}")
        safe_print(f"   wedata.project: {tags['wedata.project'] or '(empty)'}")
        safe_print(f"   wedata.datascience.type: {tags['wedata.datascience.type']}")
        safe_print(f"   mlflow.user: {tags['mlflow.user'] or '(empty)'}")

    except Exception as e:
        logger.warning(f"Failed to set model version WeData tags: {e}")
        safe_print(f"⚠️  Failed to set WeData tags on model version: {e}")


def log_feature_list(features: List[str]):
    """记录特征列表到 MLflow"""
    import json
    mlflow.log_dict({"features": features}, "feature_list.json")


def log_best_config_overall(config: Dict[str, Any]):
    """记录最佳配置到 MLflow"""
    import json
    mlflow.log_dict(config, "best_config_overall.json")


def log_best_config_per_estimator(config: Dict[str, Any]):
    """记录每个估计器的最佳配置到 MLflow"""
    import json
    mlflow.log_dict(config, "best_config_per_estimator.json")


def log_engine_meta(meta: Dict[str, Any]):
    """记录引擎元数据到 MLflow"""
    import json
    mlflow.log_dict(meta, "engine_meta.json")


class TrialLogger:
    """
    FLAML Trial 日志记录器

    用于记录每个 trial 的详细信息到 MLflow
    """

    def __init__(self, parent_run_id: str, features: List[str], task: str, metric: str):
        """
        初始化 Trial Logger

        Args:
            parent_run_id: 父 run 的 ID
            features: 特征列表
            task: 任务类型
            metric: 评估指标
        """
        self.parent_run_id = parent_run_id
        self.features = features
        self.task = task
        self.metric = metric
        self.trial_count = 0
        self.trial_runs = []  # 存储所有 trial 的信息

    def log_trial(self, config: Dict[str, Any], estimator: str, val_loss: float, train_time: float):
        """
        记录单个 trial 到 MLflow

        Args:
            config: 超参数配置
            estimator: 估计器名称
            val_loss: 验证集损失
            train_time: 训练时间
        """
        self.trial_count += 1

        try:
            # 创建嵌套 run
            with mlflow.start_run(run_name=f"trial_{self.trial_count}_{estimator}", nested=True) as trial_run:
                trial_run_id = trial_run.info.run_id

                # 🆕 删除子 run 的 mlflow.source.name tag（不需要记录文件路径）
                try:
                    mlflow.delete_tag("mlflow.source.name")
                except Exception:
                    pass  # tag 可能不存在，忽略错误

                # 记录参数
                mlflow.log_param("estimator", estimator)
                mlflow.log_param("trial_number", self.trial_count)
                mlflow.log_param("parent_run_id", self.parent_run_id)
                mlflow.log_param("primaryMetric", self.metric)  # 🆕 记录用户指定的主要评估指标

                # 记录超参数
                for key, value in config.items():
                    try:
                        mlflow.log_param(f"hp_{key}", value)
                    except Exception as e:
                        # 某些值可能无法序列化
                        safe_print(f"⚠️  DEBUG: Failed to log param hp_{key}={value}: {e}")
                        mlflow.log_param(f"hp_{key}", str(value))

                # 记录指标 - 同时记录 val_loss 和用户指定的 metric
                mlflow.log_metric("val_loss", val_loss)
                mlflow.log_metric("train_time", train_time)

                # 🆕 将 val_loss 转换为用户指定的 metric 值
                metric_value = self._convert_val_loss_to_metric(val_loss)
                mlflow.log_metric(self.metric, metric_value)

                # 记录特征列表
                log_feature_list(self.features)

                # 🆕 标记子 run 没有注册模型（用于后端返回空数组而不是 null）
                mlflow.set_tag("wedata.has_registered_model", "false")

                # 存储 trial 信息
                trial_info = {
                    "run_id": trial_run_id,
                    "trial_number": self.trial_count,
                    "estimator": estimator,
                    "val_loss": val_loss,
                    "train_time": train_time,
                    "config": config,
                }
                self.trial_runs.append(trial_info)

                safe_print(f"  Trial {self.trial_count:3d} | {estimator:15s} | val_loss={val_loss:.6f} | time={train_time:.2f}s")
        except Exception as e:
            safe_print(f"❌ DEBUG: Exception in log_trial for trial {self.trial_count}: {e}")
            import traceback
            safe_print(f"   Traceback: {traceback.format_exc()}")
            # 重新抛出异常，让外层捕获
            raise

    def _convert_val_loss_to_metric(self, val_loss: float) -> float:
        """
        将 FLAML 的 val_loss 转换为用户指定的 metric 值

        FLAML 内部统一使用 val_loss（越小越好）：
        - 对于"越小越好"的指标（如 log_loss, mse）: val_loss = metric_value
        - 对于"越大越好"的指标（如 accuracy, f1）: val_loss = 1 - metric_value

        Args:
            val_loss: FLAML 的 val_loss 值

        Returns:
            用户指定的 metric 值
        """
        # "越大越好"的指标列表
        maximize_metrics = [
            "accuracy", "f1", "macro_f1", "micro_f1", "weighted_f1",
            "roc_auc", "roc_auc_ovr", "roc_auc_ovo", "roc_auc_weighted",
            "precision", "recall", "ap",
            "r2",
        ]

        # 如果是"越大越好"的指标，需要转换回来
        if self.metric in maximize_metrics:
            return 1.0 - val_loss
        else:
            # "越小越好"的指标，直接返回
            return val_loss

    def get_best_trial(self) -> Dict[str, Any]:
        """
        获取最佳 trial

        Returns:
            最佳 trial 的信息字典
        """
        if not self.trial_runs:
            return None

        # 按 val_loss 排序（越小越好）
        best_trial = min(self.trial_runs, key=lambda x: x["val_loss"])
        return best_trial


# ============================================================================
# Forecast 模型 MLflow PythonModel 包装器
# ============================================================================

class ForecastModelWrapper(mlflow.pyfunc.PythonModel):
    """
    时序预测模型的 MLflow PythonModel 包装器

    将 FLAML 训练的时序预测模型包装为标准的 MLflow pyfunc 模型，
    支持通过 mlflow.pyfunc.load_model() 加载和预测。

    Attributes:
        model: FLAML 训练的时序预测模型（或 Pipeline）
        horizon: 预测时间范围
        frequency: 时间频率（D/W/M/H 等）
        time_col: 时间列名
        target_col: 目标列名
        estimator: 最佳估计器名称

    Example:
        >>> # 加载模型
        >>> model = mlflow.pyfunc.load_model("runs:/xxx/model")
        >>> # 预测
        >>> future_dates = pd.DataFrame({"ds": pd.date_range("2024-01-01", periods=6, freq="D")})
        >>> predictions = model.predict(future_dates)
    """

    def __init__(
        self,
        model=None,
        horizon: int = 1,
        frequency: str = "D",
        time_col: str = "ds",
        target_col: str = "y",
        estimator: str = "unknown",
    ):
        """
        初始化 ForecastModelWrapper

        Args:
            model: FLAML 训练的时序预测模型
            horizon: 预测时间范围
            frequency: 时间频率
            time_col: 时间列名
            target_col: 目标列名
            estimator: 最佳估计器名称
        """
        self.model = model
        self.horizon = horizon
        self.frequency = frequency
        self.time_col = time_col
        self.target_col = target_col
        self.estimator = estimator

    def predict(self, context, model_input: pd.DataFrame) -> pd.DataFrame:
        """
        执行预测

        Args:
            context: MLflow 模型上下文（包含 artifacts 路径等）
            model_input: 输入数据，应包含时间列

        Returns:
            预测结果 DataFrame，包含时间列和预测值列
        """
        if self.model is None:
            raise ValueError("Model not loaded. Please load the model first.")

        # 获取输入的时间列
        if self.time_col in model_input.columns:
            future_dates = pd.to_datetime(model_input[self.time_col])
        else:
            # 如果没有时间列，使用默认的未来日期
            future_dates = pd.date_range(
                start=pd.Timestamp.now(),
                periods=self.horizon,
                freq=self.frequency
            )

        # 构造预测输入
        future_X = pd.DataFrame({self.time_col: future_dates})

        # 执行预测
        try:
            predictions = self.model.predict(future_X)
        except Exception as e:
            # 某些模型可能不支持传入时间列，尝试直接预测
            try:
                predictions = self.model.predict(model_input)
            except Exception:
                raise ValueError(f"Prediction failed: {e}")

        # 确保预测结果长度与输入一致
        n_predictions = len(future_dates)
        if len(predictions) > n_predictions:
            predictions = predictions[:n_predictions]
        elif len(predictions) < n_predictions:
            # 填充不足的部分
            predictions = np.pad(
                predictions,
                (0, n_predictions - len(predictions)),
                mode='edge'
            )

        # 构造输出 DataFrame
        result = pd.DataFrame({
            self.time_col: future_dates,
            f"predicted_{self.target_col}": predictions
        })

        return result


class FLAMLTrainer:
    """
    FLAML 训练器
    
    封装 FLAML 训练逻辑，支持 Databricks 风格的参数
    """
    
    def __init__(
        self,
        task: str,
        target_col: str,
        timeout_minutes: int = 5,
        max_trials: Optional[int] = None,
        metric: str = "auto",
        exclude_cols: Optional[List[str]] = None,
        exclude_frameworks: Optional[List[str]] = None,
        estimator_list: Optional[List[str]] = None,
        sample_weight_col: Optional[str] = None,
        pos_label: Optional[Union[str, int]] = None,
        data_split_col: Optional[str] = None,
        experiment_name: Optional[str] = None,
        experiment_id: Optional[str] = None,
        run_name: Optional[str] = None,
        register_model: bool = True,
        model_name: Optional[str] = None,
        max_concurrent_trials: int = 1,
        use_spark: bool = False,
        custom_hp: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        log_file_dir: Optional[str] = None,
        auto_cleanup_logs: bool = True,
        log_max_age_hours: int = 24,
        log_max_files: int = 100,
        imputers: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
        country_code: Optional[str] = "US",
        feature_store_lookups: Optional[List[Dict[str, Any]]] = None,
        # Catalog 注册参数
        register_to_catalog: bool = False,
        catalog_model_name: Optional[str] = None,
        catalog_region: str = "ap-beijing",
        **kwargs
    ):
        """
        初始化 FLAML 训练器

        Args:
            task: 任务类型 ("classification" 或 "regression")
            target_col: 目标列名
            timeout_minutes: 超时时间（分钟）
            max_trials: 最大试验次数
            metric: 评估指标，用于选择最佳模型
                分类任务可选:
                    - 'log_loss': 对数损失（默认，推荐用于多分类）
                    - 'accuracy': 准确率（适合类别平衡的数据）
                    - 'roc_auc': ROC AUC（二分类）
                    - 'f1': F1 分数（二分类或 macro/micro F1）
                    - 'macro_f1': Macro-averaged F1（多分类，类别不平衡）
                    - 'micro_f1': Micro-averaged F1（多分类）
                    - 'roc_auc_ovr': One-vs-Rest ROC AUC（多分类）
                    - 'roc_auc_ovo': One-vs-One ROC AUC（多分类）
                    - 'precision': 精确率
                    - 'recall': 召回率
                    - 'ap': Average Precision
                回归任务可选:
                    - 'r2': R² 分数
                    - 'mse': 均方误差
                    - 'rmse': 均方根误差
                    - 'mae': 平均绝对误差
                    - 'mape': 平均绝对百分比误差
                注意: FLAML 内部会将指标转换为 val_loss（损失值，越小越好）
                      - 对于"越小越好"的指标（如 log_loss, mse）: val_loss = metric_value
                      - 对于"越大越好"的指标（如 accuracy, f1）: val_loss = 1 - metric_value
            exclude_cols: 排除的列
            exclude_frameworks: 排除的框架（已弃用，请使用 estimator_list）
            estimator_list: 估计器列表，默认 None（使用所有可用估计器）
                可选值: ["lgbm", "xgboost", "rf", "extra_tree", "lrl1"]
                例如: ["lgbm", "xgboost"] 只使用 LightGBM 和 XGBoost
                注意: lrl1 仅适用于分类任务
            sample_weight_col: 样本权重列
            pos_label: 正类标签（二分类）
            data_split_col: 数据划分列
            experiment_name: MLflow 实验名称
            experiment_id: MLflow 实验 ID
            run_name: MLflow run 名称
            register_model: 是否注册模型
            model_name: 模型名称
            max_concurrent_trials: 并发 trials 数量，默认 1（顺序执行）
                - 设置 > 1 时，FLAML 会并行执行多个 trials
                - 本地模式：使用多线程并行
                - Spark 模式：使用 Spark 分布式并行（需要设置 use_spark=True）
                - 注意：并发会增加内存和 CPU 使用
            use_spark: 是否使用 Spark 作为并行后端，默认 False
                - True: 使用 Spark 分布式执行 trials（需要 Spark 集群）
                - False: 使用本地多线程并行
                - 注意：Spark 模式不支持 GPU 训练
            custom_hp: 自定义超参数搜索空间，格式为 {estimator_name: {param_name: search_space}}
                例如: {"lgbm": {"n_estimators": {"domain": range(100, 1000), "init_value": 100}}}
            project_id: 项目 ID，用于多租户隔离（设置为实验标签 'wedata.project'）
                - 优先使用传入的 project_id 参数
                - 如果未传入，则从环境变量 WEDATA_PROJECT_ID 读取
                - 如果都未配置，则抛出 ValueError 异常
            log_file_dir: FLAML log 文件存储目录，默认 None（使用系统临时目录）
                - 建议在 DLC Spark 环境下设置为共享存储路径（如 HDFS、COS）
                - 例如: "/tmp/wedata_automl/logs" 或 "hdfs:///user/wedata/logs"
            auto_cleanup_logs: 是否自动清理旧的 log 文件，默认 True
                - True: 每次训练前自动清理过期的 log 文件
                - False: 不清理，需要手动管理
            log_max_age_hours: log 文件最大保留时间（小时），默认 24
                - 超过此时间的 log 文件将被自动清理
            log_max_files: log 文件最大保留数量，默认 100
                - 超过此数量的旧 log 文件将被自动清理
            imputers: 缺失值填充策略字典，格式为 {列名: 填充策略}，默认 None
                - 填充策略可以是字符串：
                    - "auto": 自动选择（默认使用 median）
                    - "mean": 均值填充
                    - "median": 中位数填充
                    - "most_frequent": 众数填充
                - 或者字典（用于常量填充）：
                    - {"strategy": "constant", "fill_value": <value>}
                - 示例：
                    imputers={
                        "age": "mean",
                        "income": "median",
                        "status": {"strategy": "constant", "fill_value": 0}
                    }
            country_code: 节假日国家代码，默认 "US"（仅 Prophet 时序预测使用）
                - 双字母国家/地区代码，指定使用哪个国家的节假日
                - 设置为空字符串 "" 可忽略节假日
                - 示例: "US"（美国）, "CN"（中国）, "JP"（日本）
            feature_store_lookups: 特征存储查找配置，默认 None（仅时序预测使用）
                - 格式: [{"table_name": str, "lookup_key": str/list, "timestamp_lookup_key": str}]
                - 用于从特征存储中查找协变量数据
            prediction_result_storage: 预测结果存储路径，默认 None（仅时序预测使用）
                - DLC 两段式路径，如 "/DataLake/data/"
                - 如果提供，训练完成后会自动执行预测并保存到 DLC 表
            storage_data_source_id: 存储数据源 ID，默认 None
            storage_data_source_name: 存储数据源名称，默认 None
            register_to_catalog: 是否将最佳模型注册到 TencentCloud Catalog，默认 False
                - True: 训练完成后自动将最佳模型注册到 Catalog
                - 需要设置相关环境变量（TENCENTCLOUD_SECRET_ID/KEY, TENCENTCLOUD_ENDPOINT）
            catalog_model_name: Catalog 模型名称，格式为 "catalog.schema.model_name"
                - 如果未设置，将自动生成
            catalog_region: Catalog 地域，默认 "ap-beijing"
            **kwargs: 其他参数

        Raises:
            ValueError: 如果 project_id 未配置（既未传入参数，也未设置环境变量）
        """
        self.task = task
        self.target_col = target_col
        self.timeout_minutes = timeout_minutes
        self.max_trials = max_trials
        self.metric = metric if metric != "auto" else self._get_default_metric(task)
        self.exclude_cols = exclude_cols or []
        self.exclude_frameworks = exclude_frameworks or []
        self.estimator_list = estimator_list
        self.sample_weight_col = sample_weight_col
        self.pos_label = pos_label
        self.data_split_col = data_split_col
        self.experiment_name = experiment_name or "wedata_automl"
        self.experiment_id = experiment_id
        self.run_name = run_name or f"flaml_automl_{task}"
        self.register_model = register_model
        self.model_name = model_name
        self.max_concurrent_trials = max_concurrent_trials
        self.use_spark = use_spark
        self.custom_hp = custom_hp
        self.imputers = imputers
        self.country_code = country_code
        self.feature_store_lookups = feature_store_lookups or []

        # 预测结果存储参数（仅时序预测使用）
        self.prediction_result_storage = kwargs.pop("prediction_result_storage", None)
        self.storage_data_source_id = kwargs.pop("storage_data_source_id", None)
        self.storage_data_source_name = kwargs.pop("storage_data_source_name", None)

        # Catalog 注册参数
        self.register_to_catalog = register_to_catalog
        self.catalog_model_name = catalog_model_name
        self.catalog_region = catalog_region or os.getenv("QCLOUD_REGION")

        # Log 文件管理配置
        self.log_file_dir = log_file_dir
        self.auto_cleanup_logs = auto_cleanup_logs
        self.log_max_age_hours = log_max_age_hours
        self.log_max_files = log_max_files

        # 处理 project_id：优先使用用户传入的值，否则从环境变量读取
        self.project_id = project_id or os.environ.get("WEDATA_PROJECT_ID")

        # 验证 project_id 是否存在
        if not self.project_id:
            raise ValueError(
                "❌ 未配置 Project ID！\n"
                "请通过以下任一方式配置 Project ID：\n"
                "1. 传递 project_id 参数：classify(..., project_id='your_project_id')\n"
                "2. 设置环境变量：export WEDATA_PROJECT_ID='your_project_id'\n"
                "\n"
                "Project ID 用于多租户隔离，确保实验可以通过后端 API 正确查询。"
            )

        self.kwargs = kwargs

        # 内部状态
        self.automl = None
        self.pipeline = None
        self.features = None
        self.preprocessor = None
        self.data_source_table = None  # 记录数据源表名（如果用户传入表名）
    
    # 支持的指标配置
    SUPPORTED_METRICS = {
        "forecast": {
            "default": "smape",
            "supported": ["smape", "mse", "rmse", "mae", "mdape"]
        },
        "regression": {
            "default": "deviance",
            "supported": ["deviance", "rmse", "mae", "r2", "mse"]
        },
        "classification": {
            "default": "log_loss",
            "supported": ["f1", "log_loss", "precision", "accuracy", "roc_auc", "rmse", "mae"]
        }
    }

    # 支持的估计器配置
    # sklearn 映射为 FLAML 的具体估计器: rf (随机森林), extra_tree, lrl1 (L1正则化逻辑回归)
    SUPPORTED_ESTIMATORS = {
        "forecast": {
            # 默认使用统计模型 + 树模型
            "default": ["prophet", "arima", "sarimax"],
            # FLAML ts_forecast 支持的所有估计器
            "supported": [
                # 统计模型
                "prophet",       # Facebook Prophet
                "arima",         # ARIMA
                "sarimax",       # SARIMAX (带季节性的 ARIMA)
                "holt-winters",  # Holt-Winters 三次指数平滑
                # 树模型
                "lgbm",          # LightGBM
                "xgboost",       # XGBoost
                "xgb_limitdepth",# XGBoost (限制深度)
                "rf",            # 随机森林
                "extra_tree",    # ExtraTrees
                "histgb",        # HistGradientBoosting
            ],
        },
        "regression": {
            "default": ["lgbm", "xgboost", "rf", "extra_tree"],
            "supported": ["lgbm", "xgboost", "rf", "extra_tree"],
            # sklearn 映射: rf, extra_tree
            # lightgbm 映射: lgbm
            # xgboost 映射: xgboost
        },
        "classification": {
            "default": ["lgbm", "xgboost", "rf", "extra_tree", "lrl1"],
            "supported": ["lgbm", "xgboost", "rf", "extra_tree", "lrl1"],
            # sklearn 映射: rf, extra_tree, lrl1
            # lightgbm 映射: lgbm
            # xgboost 映射: xgboost
        }
    }

    def _get_default_metric(self, task: str) -> str:
        """获取默认指标"""
        if task in self.SUPPORTED_METRICS:
            return self.SUPPORTED_METRICS[task]["default"]
        return "accuracy"

    def _validate_metric(self, task: str, metric: str) -> str:
        """验证指标是否支持"""
        if task not in self.SUPPORTED_METRICS:
            return metric

        supported = self.SUPPORTED_METRICS[task]["supported"]
        if metric.lower() not in [m.lower() for m in supported]:
            safe_print(f"⚠️  Metric '{metric}' is not in supported list for {task}: {supported}")
            safe_print(f"   Using default metric: {self.SUPPORTED_METRICS[task]['default']}")
            return self.SUPPORTED_METRICS[task]["default"]
        return metric.lower()

    def _get_estimator_list(self) -> List[str]:
        """获取估计器列表"""
        # 用户可能使用的别名映射到 FLAML 估计器名称
        estimator_alias_map = {
            "sklearn": ["rf", "extra_tree", "lrl1"],  # sklearn 的模型映射
            "lightgbm": ["lgbm"],
            "xgboost": ["xgboost"],
            "deep-ar": [],  # 暂不支持
            "deepar": [],   # 暂不支持
        }

        # 如果用户指定了 estimator_list，进行处理
        if self.estimator_list:
            expanded_estimators = []
            for est in self.estimator_list:
                est_lower = est.lower()
                if est_lower in estimator_alias_map:
                    expanded_estimators.extend(estimator_alias_map[est_lower])
                    if not estimator_alias_map[est_lower]:
                        safe_print(f"⚠️  Estimator '{est}' is not currently supported, skipping")
                else:
                    expanded_estimators.append(est)

            # 对于 forecast 任务，过滤掉不支持的估计器
            if self.task == "forecast":
                supported = self.SUPPORTED_ESTIMATORS["forecast"]["supported"]
                filtered = [e for e in expanded_estimators if e in supported]
                if len(filtered) < len(expanded_estimators):
                    unsupported = [e for e in expanded_estimators if e not in supported]
                    safe_print(f"⚠️  Filtered out unsupported forecast estimators: {unsupported}")
                    safe_print(f"   Supported: {supported}")
                return filtered if filtered else self.SUPPORTED_ESTIMATORS["forecast"]["default"]
            return expanded_estimators if expanded_estimators else self.SUPPORTED_ESTIMATORS.get(
                self.task, {"default": ["lgbm", "xgboost"]}
            )["default"]

        # 否则使用默认列表（排除 exclude_frameworks）
        if self.task in self.SUPPORTED_ESTIMATORS:
            all_estimators = self.SUPPORTED_ESTIMATORS[self.task]["default"].copy()
        else:
            all_estimators = ["lgbm", "xgboost", "rf", "extra_tree"]

        # 排除指定的框架（向后兼容）
        estimators = [e for e in all_estimators if e not in self.exclude_frameworks]
        return estimators

    def _evaluate_model(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_val: pd.DataFrame,
        y_val: np.ndarray,
        X_test: pd.DataFrame,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """
        评估模型

        Returns:
            评估指标字典
        """
        metrics = {}

        if self.task == "classification":
            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

            for name, X, y_true in [
                ("train", X_train, y_train),
                ("val", X_val, y_val),
                ("test", X_test, y_test),
            ]:
                pred = self.pipeline.predict(X)

                acc = float(accuracy_score(y_true, pred))
                f1 = float(f1_score(y_true, pred, average='weighted', zero_division=0))
                precision = float(precision_score(y_true, pred, average='weighted', zero_division=0))
                recall = float(recall_score(y_true, pred, average='weighted', zero_division=0))

                metrics[f"{name}_accuracy"] = acc
                metrics[f"{name}_f1"] = f1
                metrics[f"{name}_precision"] = precision
                metrics[f"{name}_recall"] = recall

                mlflow.log_metric(f"{name}_accuracy", acc)
                mlflow.log_metric(f"{name}_f1", f1)
                mlflow.log_metric(f"{name}_precision", precision)
                mlflow.log_metric(f"{name}_recall", recall)

                safe_print(f"{name.capitalize():5s} Set - Accuracy: {acc:.4f} | F1: {f1:.4f} | Precision: {precision:.4f} | Recall: {recall:.4f}")

        elif self.task == "regression":
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

            for name, X, y_true in [
                ("train", X_train, y_train),
                ("val", X_val, y_val),
                ("test", X_test, y_test),
            ]:
                pred = self.pipeline.predict(X)

                r2 = float(r2_score(y_true, pred))
                mse = float(mean_squared_error(y_true, pred))
                mae = float(mean_absolute_error(y_true, pred))
                rmse = float(np.sqrt(mse))

                metrics[f"{name}_r2"] = r2
                metrics[f"{name}_mse"] = mse
                metrics[f"{name}_mae"] = mae
                metrics[f"{name}_rmse"] = rmse

                mlflow.log_metric(f"{name}_r2", r2)
                mlflow.log_metric(f"{name}_mse", mse)
                mlflow.log_metric(f"{name}_mae", mae)
                mlflow.log_metric(f"{name}_rmse", rmse)

                safe_print(f"{name.capitalize():5s} Set - R²: {r2:.4f} | MSE: {mse:.4f} | MAE: {mae:.4f} | RMSE: {rmse:.4f}")

        return metrics
    
    def _prepare_data(
        self,
        pdf: pd.DataFrame
    ) -> tuple:
        """
        准备数据

        Returns:
            (X_train, y_train, X_val, y_val, X_test, y_test, sample_weight_train)
        """
        # 确定特征列
        disable_cols = set(self.exclude_cols) | {self.target_col}
        if self.sample_weight_col:
            disable_cols.add(self.sample_weight_col)
        if self.data_split_col:
            disable_cols.add(self.data_split_col)

        self.features = [c for c in pdf.columns if c not in disable_cols]

        safe_print(f"Target column: '{self.target_col}'")
        safe_print(f"Feature columns: {len(self.features)} columns")
        if len(self.features) <= 20:
            safe_print(f"  Features: {', '.join(self.features)}")
        else:
            safe_print(f"  First 10 features: {', '.join(self.features[:10])}")
            safe_print(f"  ... and {len(self.features) - 10} more")

        # 数据划分
        safe_print("", show_timestamp=False, show_level=False)
        if self.data_split_col and self.data_split_col in pdf.columns:
            # 使用用户提供的划分列
            pdf["_automl_split_col"] = pdf[self.data_split_col]
            safe_print(f"✅ Using user-provided split column: '{self.data_split_col}'")
        else:
            # 自动划分
            safe_print(f"Auto-generating train/val/test split (60%/20%/20%)")
            if self.task == "classification":
                safe_print(f"  Using stratified split for classification")
            split_col, sample_weights = compute_split_and_weights(
                y=pdf[self.target_col].values,
                task=self.task,
                train_ratio=0.6,
                val_ratio=0.2,
                test_ratio=0.2,
                stratify=True if self.task == "classification" else False,
                random_state=42,
            )
            pdf["_automl_split_col"] = split_col.values
            pdf["_automl_sample_weight"] = sample_weights.values
            safe_print("✅ Split generated successfully")

        # 分割数据
        train_df = pdf[pdf["_automl_split_col"] == 0]
        val_df = pdf[pdf["_automl_split_col"] == 1]
        test_df = pdf[pdf["_automl_split_col"] == 2]

        X_train = train_df[self.features]
        y_train = train_df[self.target_col].values

        X_val = val_df[self.features]
        y_val = val_df[self.target_col].values

        X_test = test_df[self.features]
        y_test = test_df[self.target_col].values

        # 获取样本权重
        sample_weight_train = None
        if self.sample_weight_col and self.sample_weight_col in train_df.columns:
            # 使用用户提供的样本权重列
            sample_weight_train = train_df[self.sample_weight_col].values
            safe_print(f"✅ Using user-provided sample weights from column: '{self.sample_weight_col}'")
        elif "_automl_sample_weight" in train_df.columns:
            # 使用自动生成的样本权重（用于类别不平衡）
            sample_weight_train = train_df["_automl_sample_weight"].values

        safe_print("", show_timestamp=False, show_level=False)
        safe_print(f"Data split summary:")
        safe_print(f"  Train: {len(train_df):,} samples ({len(train_df)/len(pdf)*100:.1f}%)")
        safe_print(f"  Val:   {len(val_df):,} samples ({len(val_df)/len(pdf)*100:.1f}%)")
        safe_print(f"  Test:  {len(test_df):,} samples ({len(test_df)/len(pdf)*100:.1f}%)")
        safe_print(f"  Total: {len(pdf):,} samples")

        # 显示目标变量分布（分类任务）
        if self.task == "classification":
            safe_print("", show_timestamp=False, show_level=False)
            safe_print(f"Target distribution in training set:")
            train_dist = pd.Series(y_train).value_counts().sort_index()
            for label, count in train_dist.items():
                safe_print(f"  Class {label}: {count:,} samples ({count/len(y_train)*100:.1f}%)")

        return X_train, y_train, X_val, y_val, X_test, y_test, sample_weight_train

    def _apply_feature_store_lookups(
        self,
        pdf: pd.DataFrame,
        spark=None
    ) -> pd.DataFrame:
        """
        使用 wedata-feature-engineering 的 FeatureStoreClient 从特征存储中查找特征并合并到数据集

        Args:
            pdf: 原始数据集
            spark: Spark session

        Returns:
            合并特征后的数据集

        Note:
            feature_store_lookups 格式:
            [
                {
                    "table_name": "feature_store.sales_features",
                    "lookup_key": ["store_id", "product_id"],  # 或单个字符串
                    "feature_names": ["feature1", "feature2"],  # 可选，指定要查找的特征
                    "timestamp_lookup_key": "date"  # 可选，用于时序特征表
                }
            ]
        """
        # 初始化特征存储相关的实例变量
        self._fs_client = None
        self._feature_lookups = None
        self._training_set = None

        if not self.feature_store_lookups:
            return pdf

        if spark is None:
            safe_print("⚠️  Spark session not available, skipping feature store lookups")
            return pdf

        try:
            # 使用 wedata-feature-engineering 的 FeatureStoreClient
            from wedata.feature_store.client import FeatureStoreClient
            from wedata.feature_store.entities.feature_lookup import FeatureLookup

            self._fs_client = FeatureStoreClient(spark=spark)

            # 构建 FeatureLookup 列表
            self._feature_lookups = []
            for lookup in self.feature_store_lookups:
                table_name = lookup.get("table_name")
                lookup_key = lookup.get("lookup_key")
                feature_names = lookup.get("feature_names")  # 可选
                timestamp_lookup_key = lookup.get("timestamp_lookup_key")

                if not table_name or not lookup_key:
                    safe_print(f"⚠️  Skipping invalid feature store lookup: {lookup}")
                    continue

                safe_print(f"Looking up features from: {table_name}")
                safe_print(f"  Lookup key: {lookup_key}")
                if feature_names:
                    safe_print(f"  Feature names: {feature_names}")
                if timestamp_lookup_key:
                    safe_print(f"  Timestamp key: {timestamp_lookup_key}")

                # 创建 FeatureLookup 对象
                fl = FeatureLookup(
                    table_name=table_name,
                    lookup_key=lookup_key,
                    feature_names=feature_names,
                    timestamp_lookup_key=timestamp_lookup_key
                )
                self._feature_lookups.append(fl)

            if not self._feature_lookups:
                safe_print("⚠️  No valid feature lookups configured")
                return pdf

            # 将 pandas DataFrame 转换为 Spark DataFrame
            spark_df = spark.createDataFrame(pdf)
            original_cols = set(pdf.columns)

            # 使用 FeatureStoreClient 创建 training set
            # 保存 training_set 供后续模型注册使用
            self._training_set = self._fs_client.create_training_set(
                df=spark_df,
                feature_lookups=self._feature_lookups,
                label=self.target_col,  # 指定标签列，用于后续 log_model
                exclude_columns=[]
            )

            # 加载合并后的数据并转换回 pandas
            augmented_df = self._training_set.load_df()
            pdf = augmented_df.toPandas()

            new_cols = set(pdf.columns) - original_cols
            safe_print(f"✅ Feature store lookup completed")
            safe_print(f"   Added {len(new_cols)} new columns")
            if new_cols:
                safe_print(f"   New columns: {', '.join(sorted(new_cols)[:5])}" +
                          (f"... (+{len(new_cols) - 5} more)" if len(new_cols) > 5 else ""))

        except ImportError as e:
            safe_print(f"⚠️  wedata-feature-engineering not available: {e}")
            safe_print("   Falling back to manual feature lookup...")
            # 回退到手动查找
            pdf = self._apply_feature_store_lookups_fallback(pdf, spark)
        except Exception as e:
            safe_print(f"⚠️  Feature store lookup failed: {e}")
            logger.warning(f"Feature store lookup failed: {e}")

        safe_print(f"Dataset shape after feature lookups: {pdf.shape}")
        return pdf

    def _apply_feature_store_lookups_fallback(
        self,
        pdf: pd.DataFrame,
        spark
    ) -> pd.DataFrame:
        """
        手动特征查找的回退方法（当 wedata-feature-engineering 不可用时使用）
        """
        for lookup in self.feature_store_lookups:
            table_name = lookup.get("table_name")
            lookup_key = lookup.get("lookup_key")

            if not table_name or not lookup_key:
                continue

            try:
                feature_df = spark.read.table(table_name).toPandas()

                if isinstance(lookup_key, str):
                    lookup_key = [lookup_key]

                missing_in_pdf = [k for k in lookup_key if k not in pdf.columns]
                missing_in_feature = [k for k in lookup_key if k not in feature_df.columns]

                if missing_in_pdf or missing_in_feature:
                    continue

                original_cols = set(pdf.columns)
                pdf = pdf.merge(feature_df, on=lookup_key, how="left")
                new_cols = set(pdf.columns) - original_cols

                safe_print(f"✅ Added {len(new_cols)} features from {table_name} (fallback)")

            except Exception as e:
                safe_print(f"⚠️  Failed to lookup features from {table_name}: {e}")

        return pdf

    def _log_model_with_mlflow(
        self,
        parent_run_id: str,
        registered_model_name: Optional[str] = None,
        X_sample: Optional[pd.DataFrame] = None,
        y_sample: Optional[np.ndarray] = None
    ) -> tuple:
        """
        使用标准 MLflow 方式记录和注册模型

        Args:
            parent_run_id: 父 run 的 ID
            registered_model_name: 注册模型的名称（可选）
            X_sample: 用于推断签名的输入样本（可选）
            y_sample: 用于推断签名的输出样本（可选）

        Returns:
            (model_uri, model_version) 元组
        """
        from mlflow.models import infer_signature

        # 时序预测任务使用不同的日志方式
        if self.task == "forecast":
            return self._log_forecast_model(parent_run_id, registered_model_name)

        # 推断模型签名（分类/回归任务）
        signature = None
        if X_sample is not None:
            try:
                # 使用样本数据推断签名
                if y_sample is not None:
                    # 使用模型预测来推断输出签名
                    y_pred = self.pipeline.predict(X_sample)
                    signature = infer_signature(X_sample, y_pred)
                else:
                    signature = infer_signature(X_sample)
                safe_print(f"✅ Model signature inferred successfully")
            except Exception as e:
                safe_print(f"⚠️  Failed to infer model signature: {e}")
                signature = None

        # 记录模型到 MLflow
        # 注意：这里记录的是完整的 Pipeline（预处理器 + 模型），而不是单独的模型
        # 这样在推理时可以直接处理原始数据，无需额外的预处理步骤
        mlflow.sklearn.log_model(
            sk_model=self.pipeline,
            artifact_path="model",
            signature=signature,
        )
        model_uri = f"runs:/{parent_run_id}/model"
        safe_print(f"✅ Model logged to MLflow: {model_uri}")

        # 🆕 不再在父 run 中注册模型，只记录模型 artifact
        # 模型注册由用户在训练完成后手动进行，或通过 Catalog 注册
        model_version = None
        safe_print(f"ℹ️  Model not registered in parent run (artifact only)")
        mlflow.set_tag("wedata.has_registered_model", "false")

        return model_uri, model_version

    def _log_forecast_model(
        self,
        parent_run_id: str,
        registered_model_name: Optional[str] = None,
    ) -> tuple:
        """
        使用 mlflow.pyfunc.log_model 方式记录时序预测模型

        时序预测模型（如 ARIMA, Prophet）不兼容 sklearn，需要使用 pyfunc 方式记录
        使用标准 MLflow pyfunc 格式，生成完整的 MLmodel 结构

        Args:
            parent_run_id: 父 run 的 ID
            registered_model_name: 注册模型的名称（可选）

        Returns:
            (model_uri, model_version) 元组
        """
        from mlflow.models import infer_signature

        # 获取模型元数据
        best_estimator = self.automl.best_estimator if hasattr(self.automl, 'best_estimator') else "unknown"
        horizon = self.kwargs.get("horizon", 1)
        frequency = self.kwargs.get("frequency", "D")
        time_col = self.kwargs.get("time_col")
        target_col = self.kwargs.get("target_col") or self.target_col

        # 创建 ForecastModelWrapper 实例
        forecast_wrapper = ForecastModelWrapper(
            model=self.pipeline,
            horizon=horizon,
            frequency=frequency,
            time_col=time_col,
            target_col=target_col,
            estimator=best_estimator,
        )

        # 创建输入示例和签名
        # 输入：包含时间列的 DataFrame
        # 输出：预测值数组
        input_example = pd.DataFrame({
            time_col: pd.date_range(start="2024-01-01", periods=3, freq=frequency)
        })

        # 推断签名
        signature = None
        try:
            # 使用简单的输出示例
            output_example = pd.DataFrame({
                f"predicted_{target_col}": [0.0] * horizon,
                f"{time_col}": pd.date_range(start="2024-01-01", periods=horizon, freq=frequency)
            })
            signature = infer_signature(input_example, output_example)
            safe_print(f"✅ Forecast model signature inferred successfully")
        except Exception as e:
            safe_print(f"⚠️  Failed to infer forecast model signature: {e}")

        # 根据实际使用的估计器动态生成依赖列表
        pip_requirements = self._get_forecast_pip_requirements(best_estimator)

        # 使用 mlflow.pyfunc.log_model 记录模型
        # 这会生成标准的 MLflow 模型结构
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=forecast_wrapper,
            signature=signature,
            input_example=input_example,
            pip_requirements=pip_requirements,
            metadata={
                "task": self.task,
                "estimator": best_estimator,
                "horizon": horizon,
                "frequency": frequency,
                "time_col": time_col,
                "target_col": target_col,
            }
        )

        model_uri = f"runs:/{parent_run_id}/model"
        safe_print(f"✅ Forecast model logged to MLflow (pyfunc): {model_uri}")

        # 🆕 不再在父 run 中注册模型，只记录模型 artifact
        # 模型注册由用户在训练完成后手动进行，或通过 Catalog 注册
        model_version = None
        safe_print(f"ℹ️  Model not registered in parent run (artifact only)")
        mlflow.set_tag("wedata.has_registered_model", "false")

        return model_uri, model_version

    def _get_forecast_pip_requirements(self, estimator: str) -> List[str]:
        """
        根据使用的估计器动态生成 pip 依赖列表

        不同的时序预测模型需要不同的依赖：
        - Prophet: prophet
        - ARIMA/SARIMAX: statsmodels
        - LightGBM: lightgbm
        - XGBoost: xgboost
        - CatBoost: catboost
        - RandomForest/ExtraTrees: scikit-learn

        Args:
            estimator: 最佳估计器名称

        Returns:
            pip 依赖列表
        """
        # 基础依赖（所有模型都需要）
        base_requirements = [
            "pandas",
            "numpy",
            "scikit-learn",
            "mlflow",
        ]

        # 估计器到依赖的映射
        estimator_requirements = {
            "prophet": ["prophet"],
            "arima": ["statsmodels"],
            "sarimax": ["statsmodels"],
            "lgbm": ["lightgbm"],
            "xgboost": ["xgboost"],
            "xgb_limitdepth": ["xgboost"],
            "catboost": ["catboost"],
            "rf": [],  # scikit-learn 已在基础依赖中
            "extra_tree": [],  # scikit-learn 已在基础依赖中
            "kneighbor": [],  # scikit-learn 已在基础依赖中
        }

        # 获取估计器特定依赖
        estimator_lower = estimator.lower() if estimator else ""
        extra_requirements = estimator_requirements.get(estimator_lower, [])

        # 合并依赖
        all_requirements = base_requirements + extra_requirements

        # 添加 FLAML（用于加载模型时的兼容性）
        all_requirements.append("flaml[forecast]")

        safe_print(f"📦 Forecast model pip requirements: {all_requirements}")

        return all_requirements

    def _save_forecast_predictions(
        self,
        parent_run_id: str,
        pdf: pd.DataFrame,
        spark=None
    ):
        """
        保存时序预测结果到 DLC 表

        支持预测区间（prediction interval）：
        - Prophet: 原生支持 yhat_lower, yhat_upper
        - ARIMA/SARIMAX: 通过 get_forecast 支持置信区间
        - 其他模型: 仅返回点预测

        Args:
            parent_run_id: 父 run ID
            pdf: 原始数据
            spark: Spark session
        """
        safe_print("", show_timestamp=False, show_level=False)
        print_separator()
        safe_print(f"📤 Saving Forecast Predictions")
        print_separator()

        if spark is None:
            safe_print("⚠️  Spark session not available, skipping prediction save")
            return

        try:
            from datetime import datetime

            # 获取时间列和预测参数
            time_col = self.kwargs.get("time_col")
            target_col = self.kwargs.get("target_col") or self.target_col
            horizon = self.kwargs.get("horizon", 1)
            frequency = self.kwargs.get("frequency", "D")
            best_estimator = self.automl.best_estimator if hasattr(self.automl, 'best_estimator') else "unknown"

            safe_print(f"Best estimator: {best_estimator}")
            safe_print(f"Generating predictions for {horizon} periods...")

            # 生成未来时间序列
            future_dates = pd.date_range(
                start=pdf[time_col].max() + pd.Timedelta(1, unit=frequency[0].lower()),
                periods=horizon,
                freq=frequency
            )

            # 获取预测值和预测区间
            predictions = None
            predictions_lower = None
            predictions_upper = None

            # Prophet 原生支持预测区间
            if best_estimator == "prophet" and hasattr(self.automl, 'model'):
                try:
                    model = self.automl.model
                    # 检查是否是 Prophet 模型
                    if hasattr(model, 'model') and hasattr(model.model, 'predict'):
                        prophet_model = model.model
                        # 创建 future dataframe
                        future_df = prophet_model.make_future_dataframe(periods=horizon, freq=frequency)
                        # 获取完整预测（包含预测区间）
                        forecast_df = prophet_model.predict(future_df)
                        # 取最后 horizon 行
                        forecast_tail = forecast_df.tail(horizon)
                        predictions = forecast_tail['yhat'].values
                        predictions_lower = forecast_tail['yhat_lower'].values
                        predictions_upper = forecast_tail['yhat_upper'].values
                        safe_print(f"✅ Prophet prediction interval obtained (80% confidence)")
                except Exception as e:
                    safe_print(f"⚠️  Failed to get Prophet prediction interval: {e}")

            # ARIMA/SARIMAX 支持预测区间
            elif best_estimator in ["arima", "sarimax"] and hasattr(self.automl, 'model'):
                try:
                    model = self.automl.model
                    if hasattr(model, 'model') and hasattr(model.model, 'get_forecast'):
                        arima_model = model.model
                        forecast_result = arima_model.get_forecast(steps=horizon)
                        predictions = forecast_result.predicted_mean.values
                        conf_int = forecast_result.conf_int(alpha=0.2)  # 80% confidence
                        predictions_lower = conf_int.iloc[:, 0].values
                        predictions_upper = conf_int.iloc[:, 1].values
                        safe_print(f"✅ ARIMA/SARIMAX prediction interval obtained (80% confidence)")
                except Exception as e:
                    safe_print(f"⚠️  Failed to get ARIMA prediction interval: {e}")

            # 如果没有获取到预测区间，使用普通预测
            if predictions is None:
                try:
                    # 对于纯时序模型，只传入未来时间点
                    # FLAML 的 predict 方法期望 X_test 第一列是时间列
                    future_X = pd.DataFrame({time_col: future_dates})
                    predictions = self.automl.predict(future_X)
                    safe_print(f"ℹ️  Using point predictions (no prediction interval for {best_estimator})")
                except Exception as e:
                    # 对于使用外生变量的模型，可能会失败
                    # 因为我们没有未来时间点的外生变量
                    safe_print(f"⚠️  Failed to predict with future time only: {e}")
                    safe_print(f"   This model may require exogenous features for prediction.")
                    safe_print(f"   Skipping prediction save for {best_estimator}.")
                    return

            # 创建预测结果 DataFrame
            pred_df = pd.DataFrame({
                time_col: future_dates,
                f"predicted_{target_col}": predictions,
                "run_id": parent_run_id,
                "predicted_at": datetime.now()
            })

            # 添加预测区间（如果有）
            if predictions_lower is not None and predictions_upper is not None:
                pred_df[f"predicted_{target_col}_lower"] = predictions_lower
                pred_df[f"predicted_{target_col}_upper"] = predictions_upper
                safe_print(f"✅ Prediction interval columns added: predicted_{target_col}_lower, predicted_{target_col}_upper")

            # 解析三段式表路径: catalog.database.table_prefix -> catalog.database.table_name
            # 例如: DataLake.automl_test.sales_predictions -> DataLake.automl_test.sales_predictions_xxx
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id_short = parent_run_id[:8]
            storage_path = self.prediction_result_storage.strip()

            # 解析三段式路径 (catalog.database.table)
            path_parts = storage_path.split(".")
            if len(path_parts) == 3:
                # catalog.database.table_prefix 格式
                catalog, database, table_prefix = path_parts
                table_name = f"{catalog}.{database}.{table_prefix}_{run_id_short}_{timestamp}"
            elif len(path_parts) == 2:
                # database.table_prefix 格式
                database, table_prefix = path_parts
                table_name = f"{database}.{table_prefix}_{run_id_short}_{timestamp}"
            else:
                # 单个名称，使用 default 数据库
                table_name = f"default.{storage_path}_{run_id_short}_{timestamp}"

            safe_print(f"Saving to table: {table_name}")

            # 转换为 Spark DataFrame 并保存
            spark_df = spark.createDataFrame(pred_df)
            spark_df.write.mode("overwrite").saveAsTable(table_name)

            # 记录存储位置到 MLflow
            mlflow.log_param("prediction_table", table_name)
            mlflow.set_tag("wedata.prediction_table", table_name)

            safe_print(f"✅ Predictions saved to: {table_name}")
            safe_print(f"   Rows: {len(pred_df)}")

        except Exception as e:
            safe_print(f"⚠️  Failed to save predictions: {e}")
            import traceback
            safe_print(f"   {traceback.format_exc()}")

    # ========================================================================
    # 私有方法：安全的 toPandas 转换（处理时区问题）
    # ========================================================================
    def _safe_to_pandas(self, spark_df, spark=None) -> pd.DataFrame:
        """
        安全地将 Spark DataFrame 转换为 Pandas DataFrame

        处理时区格式不兼容问题（如 'GMT+08:00' pytz 不识别）

        Args:
            spark_df: Spark DataFrame
            spark: SparkSession（可选，用于修改时区配置）

        Returns:
            Pandas DataFrame
        """
        try:
            return spark_df.toPandas()
        except Exception as e:
            error_msg = str(e)
            # 检查是否是时区格式问题
            if "UnknownTimeZoneError" in error_msg or "GMT" in error_msg:
                safe_print(f"⚠️  Timezone format issue detected, attempting fix...")

                # 方案 1: 尝试修改 Spark session 时区配置
                if spark is not None:
                    try:
                        # 获取当前时区
                        current_tz = spark.conf.get("spark.sql.session.timeZone", "UTC")
                        safe_print(f"   Current timezone: {current_tz}")

                        # 将 GMT+XX:XX 格式转换为标准时区名
                        new_tz = self._normalize_timezone(current_tz)
                        if new_tz != current_tz:
                            safe_print(f"   Converting timezone to: {new_tz}")
                            spark.conf.set("spark.sql.session.timeZone", new_tz)

                            try:
                                result = spark_df.toPandas()
                                # 恢复原始时区设置
                                spark.conf.set("spark.sql.session.timeZone", current_tz)
                                safe_print(f"✅ Successfully converted with timezone fix")
                                return result
                            except Exception:
                                # 恢复原始时区设置
                                spark.conf.set("spark.sql.session.timeZone", current_tz)
                    except Exception as tz_error:
                        safe_print(f"   Timezone fix failed: {tz_error}")

                # 方案 2: 将 timestamp 列转换为 string 再转换
                safe_print("   Trying alternative: convert timestamps to strings first...")
                try:
                    from pyspark.sql.functions import col
                    from pyspark.sql.types import TimestampType, DateType

                    # 找出所有 timestamp 类型的列
                    ts_cols = [
                        field.name for field in spark_df.schema.fields
                        if isinstance(field.dataType, (TimestampType,))
                    ]

                    if ts_cols:
                        safe_print(f"   Timestamp columns found: {ts_cols}")
                        # 将 timestamp 列转换为 string
                        for ts_col in ts_cols:
                            spark_df = spark_df.withColumn(
                                ts_col,
                                col(ts_col).cast("string")
                            )

                        # 转换为 Pandas
                        pdf = spark_df.toPandas()

                        # 将 string 转回 datetime
                        for ts_col in ts_cols:
                            pdf[ts_col] = pd.to_datetime(pdf[ts_col])

                        safe_print(f"✅ Successfully converted using string intermediary")
                        return pdf
                    else:
                        # 没有 timestamp 列，直接抛出原始错误
                        raise e
                except Exception as alt_error:
                    safe_print(f"   Alternative method failed: {alt_error}")
                    raise e
            else:
                # 不是时区问题，直接抛出
                raise e

    def _normalize_timezone(self, tz_str: str) -> str:
        """
        将非标准时区格式转换为 pytz 兼容格式

        Args:
            tz_str: 时区字符串，如 'GMT+08:00'

        Returns:
            标准时区名，如 'Asia/Shanghai' 或 'Etc/GMT-8'
        """
        import re

        # 完整的 GMT 偏移到标准时区映射（优先使用常用城市时区）
        # 格式: (sign, hours, minutes) -> timezone_name
        gmt_to_tz_mapping = {
            # UTC / GMT+0
            ('+', 0, 0): 'UTC',
            ('-', 0, 0): 'UTC',
            # GMT+1 ~ GMT+14
            ('+', 1, 0): 'Europe/Paris',
            ('+', 2, 0): 'Europe/Helsinki',
            ('+', 3, 0): 'Europe/Moscow',
            ('+', 3, 30): 'Asia/Tehran',
            ('+', 4, 0): 'Asia/Dubai',
            ('+', 4, 30): 'Asia/Kabul',
            ('+', 5, 0): 'Asia/Karachi',
            ('+', 5, 30): 'Asia/Kolkata',
            ('+', 5, 45): 'Asia/Kathmandu',
            ('+', 6, 0): 'Asia/Dhaka',
            ('+', 6, 30): 'Asia/Yangon',
            ('+', 7, 0): 'Asia/Bangkok',
            ('+', 8, 0): 'Asia/Shanghai',
            ('+', 8, 45): 'Australia/Eucla',
            ('+', 9, 0): 'Asia/Tokyo',
            ('+', 9, 30): 'Australia/Adelaide',
            ('+', 10, 0): 'Australia/Sydney',
            ('+', 10, 30): 'Australia/Lord_Howe',
            ('+', 11, 0): 'Pacific/Guadalcanal',
            ('+', 12, 0): 'Pacific/Auckland',
            ('+', 12, 45): 'Pacific/Chatham',
            ('+', 13, 0): 'Pacific/Tongatapu',
            ('+', 14, 0): 'Pacific/Kiritimati',
            # GMT-1 ~ GMT-12
            ('-', 1, 0): 'Atlantic/Azores',
            ('-', 2, 0): 'Atlantic/South_Georgia',
            ('-', 3, 0): 'America/Sao_Paulo',
            ('-', 3, 30): 'America/St_Johns',
            ('-', 4, 0): 'America/Halifax',
            ('-', 5, 0): 'America/New_York',
            ('-', 6, 0): 'America/Chicago',
            ('-', 7, 0): 'America/Denver',
            ('-', 8, 0): 'America/Los_Angeles',
            ('-', 9, 0): 'America/Anchorage',
            ('-', 9, 30): 'Pacific/Marquesas',
            ('-', 10, 0): 'Pacific/Honolulu',
            ('-', 11, 0): 'Pacific/Midway',
            ('-', 12, 0): 'Etc/GMT+12',
        }

        # GMT+XX:XX 或 GMT-XX:XX 格式
        match = re.match(r'GMT([+-])(\d{1,2}):?(\d{2})?', tz_str)
        if match:
            sign = match.group(1)
            hours = int(match.group(2))
            minutes = int(match.group(3)) if match.group(3) else 0

            # 尝试从映射表查找
            key = (sign, hours, minutes)
            if key in gmt_to_tz_mapping:
                return gmt_to_tz_mapping[key]

            # 对于整小时偏移，使用 Etc/GMT 格式
            # 注意：Etc 时区的符号是反的！GMT+8 对应 Etc/GMT-8
            if minutes == 0:
                etc_sign = '-' if sign == '+' else '+'
                return f"Etc/GMT{etc_sign}{hours}"

            # 对于非整小时且不在映射表中的，返回 UTC（降级处理）
            safe_print(f"⚠️  Unknown timezone offset: {tz_str}, falling back to UTC")
            return 'UTC'

        # UTC / Z 格式
        if tz_str.upper() in ('UTC', 'Z'):
            return 'UTC'

        # 已经是标准格式（如 Asia/Shanghai），直接返回
        return tz_str

    # ========================================================================
    # 私有方法：数据加载
    # ========================================================================
    def _load_data(self, dataset: Union[pd.DataFrame, Any], spark=None) -> pd.DataFrame:
        """
        加载数据并转换为 Pandas DataFrame

        Args:
            dataset: 数据集（表名、Spark DataFrame 或 Pandas DataFrame）
            spark: Spark session（如果 dataset 是表名）

        Returns:
            Pandas DataFrame
        """
        if isinstance(dataset, str):
            if spark is None:
                raise ValueError("Spark session is required when dataset is a table name")
            pdf = self._safe_to_pandas(spark.read.table(dataset), spark)
        elif hasattr(dataset, "toPandas"):
            # 尝试获取 SparkSession
            try:
                from pyspark.sql import SparkSession
                spark_session = SparkSession.getActiveSession()
            except Exception:
                spark_session = None
            pdf = self._safe_to_pandas(dataset, spark_session)
        else:
            pdf = dataset

        print_separator()
        safe_print("📊 Data Loading", show_timestamp=False, show_level=False)
        print_separator()
        if self.data_source_table:
            safe_print(f"Data source: {self.data_source_table}")
        safe_print(f"Dataset shape: {pdf.shape} (rows × columns)")
        safe_print(f"Memory usage: {pdf.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        # 时序预测任务：自动转换时间列为 datetime 类型
        if self.task == "forecast":
            time_col = self.kwargs.get("time_col")
            if time_col and time_col in pdf.columns:
                if not pd.api.types.is_datetime64_any_dtype(pdf[time_col]):
                    safe_print(f"Converting time column '{time_col}' to datetime...")
                    try:
                        pdf[time_col] = pd.to_datetime(pdf[time_col])
                        safe_print(f"✅ Time column '{time_col}' converted to datetime64")
                    except Exception as e:
                        safe_print(f"⚠️  Failed to convert time column: {e}")

        return pdf

    # ========================================================================
    # 私有方法：MLflow 实验设置
    # ========================================================================
    def _setup_mlflow_experiment(self) -> tuple:
        """
        设置 MLflow 实验

        Returns:
            (experiment, experiment_name, experiment_id)
        """
        safe_print("", show_timestamp=False, show_level=False)
        print_separator()
        safe_print(f"📝 MLflow Experiment Setup")
        print_separator()

        tracking_uri = mlflow.get_tracking_uri()
        safe_print(f"MLflow Tracking URI: {tracking_uri}")

        if tracking_uri.startswith('file://') and self.project_id:
            warning_msg = (
                f"⚠️  WARNING: Using local file system MLflow tracking ('{tracking_uri}')\n"
                f"   Local MLflow does not support project ID validation.\n"
                f"   For production use, please set MLflow tracking URI to a remote server:\n"
                f"   Example: mlflow.set_tracking_uri('http://your-mlflow-server:5000')"
            )
            safe_print(warning_msg)
            logger.warning(warning_msg)

        if self.experiment_id:
            experiment = mlflow.get_experiment(self.experiment_id)
            experiment_name = experiment.name
            safe_print(f"Using experiment by ID: {self.experiment_id}")
            safe_print(f"Experiment name: '{experiment_name}'")
        else:
            experiment_name = self.experiment_name

        try:
            mlflow.set_experiment(experiment_name)
        except Exception as e:
            error_msg = (
                f"❌ Failed to set experiment '{experiment_name}'. Error: {traceback.format_exc()}\n\n"
                f"This may be due to:\n"
                f"  1. MLflow backend permission issues\n"
                f"  2. Project ID '{self.project_id}' not found or invalid\n"
                f"  3. MLflow tracking server connection issues\n"
                f"  4. Backend API restrictions (e.g., project validation)\n\n"
                f"Configuration:\n"
                f"  - MLflow tracking URI: {mlflow.get_tracking_uri()}\n"
                f"  - Project ID: {self.project_id}\n"
                f"  - Experiment name: {experiment_name}\n\n"
                f"Please verify:\n"
                f"  - The project ID '{self.project_id}' exists in the backend\n"
                f"  - You have permission to create experiments in this project\n"
                f"  - The MLflow tracking server is accessible"
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            error_msg = (
                f"❌ Failed to create or get experiment '{experiment_name}'. "
                f"This may be due to:\n"
                f"  1. MLflow backend permission issues\n"
                f"  2. Project ID '{self.project_id}' validation failed\n"
                f"  3. MLflow tracking server connection issues\n"
                f"  4. Backend API restrictions\n\n"
                f"Please check:\n"
                f"  - MLflow tracking URI: {mlflow.get_tracking_uri()}\n"
                f"  - Project ID: {self.project_id}\n"
                f"  - Backend server logs for more details"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        experiment_id = experiment.experiment_id

        if experiment.creation_time == experiment.last_update_time:
            safe_print(f"✅ Created new experiment: '{experiment_name}' (ID: {experiment_id})")
        else:
            safe_print(f"✅ Using existing experiment: '{experiment_name}' (ID: {experiment_id})")

        if self.project_id:
            try:
                mlflow.set_experiment_tag("wedata.project", self.project_id)
                safe_print(f"✅ Set project ID tag: 'wedata.project' = '{self.project_id}'")
            except Exception as e:
                safe_print(f"⚠️  Failed to set project ID tag: {e}")
                logger.warning(f"Failed to set project ID tag: {e}")

        return experiment, experiment_name, experiment_id

    # ========================================================================
    # 私有方法：构建 FLAML 设置
    # ========================================================================
    def _build_flaml_settings(self, log_file_path: str) -> dict:
        """
        构建 FLAML AutoML 配置

        Args:
            log_file_path: 日志文件路径

        Returns:
            FLAML settings 字典
        """
        estimator_list = self._get_estimator_list()

        # FLAML 任务类型映射：我们的 "forecast" -> FLAML 的 "ts_forecast"
        flaml_task = "ts_forecast" if self.task == "forecast" else self.task

        # 获取指标（可能是自定义指标函数）
        metric = self._get_flaml_metric()

        settings = {
            "task": flaml_task,
            "metric": metric,
            "time_budget": int(self.timeout_minutes * 60),
            "eval_method": "holdout",
            "ensemble": False,
            "verbose": 0,
            "estimator_list": estimator_list,
            "seed": 42,
            "log_file_name": log_file_path,
            "mlflow_logging": False,
            "early_stop": False,
            "log_type": "all",
            "n_concurrent_trials": self.max_concurrent_trials,
            "use_spark": self.use_spark,
        }

        if self.max_trials:
            settings["max_iter"] = self.max_trials

        if self.use_spark:
            settings["force_cancel"] = True

        if self.custom_hp:
            settings["custom_hp"] = self.custom_hp
            safe_print(f"Custom hyperparameter search space provided for: {', '.join(self.custom_hp.keys())}")

        if self.task == "forecast" and self.country_code is not None:
            if "prophet" not in settings.get("custom_hp", {}):
                settings.setdefault("custom_hp", {})["prophet"] = {}
            safe_print(f"Country code for holidays: '{self.country_code}' (Prophet only)")

        # 打印配置信息
        safe_print(f"Task: {self.task} (FLAML task: {flaml_task})")
        safe_print(f"Metric: {self.metric}")
        safe_print(f"Time budget: {self.timeout_minutes} minutes ({int(self.timeout_minutes * 60)} seconds)")
        safe_print(f"Max trials: {self.max_trials if self.max_trials else 'unlimited'}")
        safe_print(f"Concurrent trials: {self.max_concurrent_trials}")
        safe_print(f"Parallel backend: {'Spark' if self.use_spark else 'Local (multi-thread)'}")
        safe_print(f"Estimators: {', '.join(estimator_list)}")
        safe_print(f"Evaluation method: holdout")
        if self.custom_hp:
            safe_print(f"Custom search space: Yes ({len(self.custom_hp)} estimator(s))")

        return settings

    def _get_flaml_metric(self):
        """
        获取 FLAML 兼容的指标

        FLAML 内置支持: rmse, mse, mae, mape, r2, accuracy, log_loss, f1, roc_auc
        自定义支持: smape, mdape, deviance, precision

        注意：对于时序预测任务 (ts_forecast)，FLAML 的自定义指标接口与分类/回归不同，
        因此某些自定义指标需要映射到 FLAML 内置指标。

        Returns:
            指标字符串或自定义指标函数
        """
        # FLAML 内置支持的指标直接返回
        flaml_builtin_metrics = ["rmse", "mse", "mae", "mape", "r2", "accuracy", "log_loss", "f1", "roc_auc"]
        if self.metric in flaml_builtin_metrics:
            return self.metric

        # 对于时序预测任务，某些自定义指标需要映射到 FLAML 内置指标
        # 因为 ts_forecast 的评估接口与分类/回归不同，自定义指标可能无法正常工作
        if self.task == "forecast":
            forecast_metric_mapping = {
                "smape": "mape",  # SMAPE 映射到 MAPE (FLAML 内置)
                "mdape": "mape",  # MDAPE 映射到 MAPE (FLAML 内置)
            }
            if self.metric in forecast_metric_mapping:
                mapped_metric = forecast_metric_mapping[self.metric]
                safe_print(f"ℹ️  For forecast task, metric '{self.metric}' is mapped to FLAML built-in '{mapped_metric}'")
                return mapped_metric

        # 非时序预测任务的自定义指标
        custom_metrics = {
            "smape": self._smape_metric,
            "mdape": self._mdape_metric,
            "deviance": self._deviance_metric,
            "precision": self._precision_metric,
        }

        if self.metric in custom_metrics:
            return custom_metrics[self.metric]
        else:
            # 未知指标，尝试直接使用
            safe_print(f"⚠️  Metric '{self.metric}' is not a known metric, using as-is")
            return self.metric

    @staticmethod
    def _smape_metric(X_val, y_val, estimator, labels=None, X_train=None, y_train=None,
                      weight_val=None, weight_train=None, *args, **kwargs):
        """
        SMAPE (Symmetric Mean Absolute Percentage Error) 自定义指标

        SMAPE = (1/n) * Σ(|y_pred - y_true| / ((|y_true| + |y_pred|) / 2)) * 100
        范围: 0% - 200%
        """
        import numpy as np
        y_pred = estimator.predict(X_val)
        y_true = np.array(y_val)
        y_pred = np.array(y_pred)

        # 避免除零
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        denominator = np.where(denominator == 0, 1e-10, denominator)

        smape = np.mean(np.abs(y_pred - y_true) / denominator) * 100
        return smape, {"smape": smape}

    @staticmethod
    def _mdape_metric(X_val, y_val, estimator, labels=None, X_train=None, y_train=None,
                      weight_val=None, weight_train=None, *args, **kwargs):
        """
        MDAPE (Median Absolute Percentage Error) 自定义指标

        MDAPE = median(|y_pred - y_true| / |y_true|) * 100
        """
        import numpy as np
        y_pred = estimator.predict(X_val)
        y_true = np.array(y_val)
        y_pred = np.array(y_pred)

        # 避免除零
        y_true_safe = np.where(y_true == 0, 1e-10, y_true)

        ape = np.abs(y_pred - y_true) / np.abs(y_true_safe) * 100
        mdape = np.median(ape)
        return mdape, {"mdape": mdape}

    @staticmethod
    def _deviance_metric(X_val, y_val, estimator, labels=None, X_train=None, y_train=None,
                         weight_val=None, weight_train=None, *args, **kwargs):
        """
        Deviance (偏差) 自定义指标 - 用于回归任务

        对于高斯分布，Deviance 等于 MSE
        Deviance = (1/n) * Σ(y_pred - y_true)^2

        注意：FLAML 优化时会最小化这个值
        """
        import numpy as np
        y_pred = estimator.predict(X_val)
        y_true = np.array(y_val)
        y_pred = np.array(y_pred)

        # 计算 MSE (均方误差) 作为 deviance
        deviance = np.mean((y_pred - y_true) ** 2)
        return deviance, {"deviance": deviance}

    @staticmethod
    def _precision_metric(X_val, y_val, estimator, labels=None, X_train=None, y_train=None,
                          weight_val=None, weight_train=None, *args, **kwargs):
        """
        Precision (精确率) 自定义指标 - 用于分类任务

        Precision = TP / (TP + FP)

        注意：FLAML 优化时会最小化 loss，所以返回 1 - precision
        """
        import numpy as np
        from sklearn.metrics import precision_score

        y_pred = estimator.predict(X_val)
        y_true = np.array(y_val)

        # 计算 precision (多分类使用 weighted 平均)
        if len(np.unique(y_true)) > 2:
            precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        else:
            precision = precision_score(y_true, y_pred, zero_division=0)

        # 返回 1 - precision 以便 FLAML 最小化
        return 1 - precision, {"precision": precision}

    # ========================================================================
    # 私有方法：准备时序预测数据
    # ========================================================================
    def _prepare_forecast_data(self, settings: dict) -> dict:
        """
        准备时序预测任务的数据和 fit 参数

        自动进行以下预处理：
        1. 转换时间列为 datetime 类型
        2. 按时间排序
        3. 自动推断频率（如果设置为 "auto" 或未识别）
        4. 填充缺失时间点
        5. 设置规则频率索引

        Args:
            settings: FLAML 设置

        Returns:
            fit_kwargs 字典
        """
        time_col = self.kwargs.get("time_col")
        horizon = self.kwargs.get("horizon", 1)
        frequency = self.kwargs.get("frequency", "auto")  # 默认改为 auto

        # 使用完整的连续数据
        train_df = self._pdf.copy()

        # 确保时间列是 datetime 类型
        if time_col and time_col in train_df.columns:
            if not pd.api.types.is_datetime64_any_dtype(train_df[time_col]):
                safe_print(f"Converting time column '{time_col}' to datetime...")
                train_df[time_col] = pd.to_datetime(train_df[time_col])

        # 选择需要的列（排除内部列）
        internal_cols = {"_automl_split_col", "_automl_sample_weight"}
        forecast_cols = [time_col, self.target_col] + [
            f for f in self.features if f not in internal_cols and f != time_col
        ]
        forecast_cols = list(dict.fromkeys(forecast_cols))
        train_df_for_flaml = train_df[forecast_cols].copy()

        # 按时间排序并去重（保留最后一个重复时间点）
        train_df_for_flaml = train_df_for_flaml.sort_values(by=time_col)
        if train_df_for_flaml[time_col].duplicated().any():
            dup_count = train_df_for_flaml[time_col].duplicated().sum()
            safe_print(f"⚠️  Found {dup_count} duplicate timestamps, keeping last occurrence...")
            train_df_for_flaml = train_df_for_flaml.drop_duplicates(subset=[time_col], keep='last')
        train_df_for_flaml = train_df_for_flaml.reset_index(drop=True)

        # 缺失时间点补充 + 设置规则频率
        train_df_for_flaml = self._fill_missing_timestamps(train_df_for_flaml, time_col, frequency)

        # 获取实际使用的频率（可能是自动推断的）
        actual_freq = frequency
        if hasattr(self, '_inferred_frequency'):
            actual_freq = self._inferred_frequency

        safe_print(f"Forecast task: using dataframe + label mode")
        safe_print(f"  Time column: {time_col}")
        safe_print(f"  Horizon: {horizon}")
        safe_print(f"  Frequency: {actual_freq}")
        safe_print(f"  DataFrame shape: {train_df_for_flaml.shape}")
        safe_print(f"  Date range: {train_df_for_flaml[time_col].min()} to {train_df_for_flaml[time_col].max()}")

        return {
            "dataframe": train_df_for_flaml,
            "label": self.target_col,
            "time_col": time_col,
            "period": horizon,
            **settings,
        }

    def _infer_frequency(self, df: pd.DataFrame, time_col: str) -> str:
        """
        自动推断时间序列的频率

        Args:
            df: 时序数据 DataFrame
            time_col: 时间列名

        Returns:
            推断出的频率字符串（pandas freq 格式）
        """
        if len(df) < 2:
            safe_print("⚠️  Not enough data points to infer frequency, defaulting to 'D'")
            return "D"

        # 计算时间差
        time_diffs = df[time_col].diff().dropna()

        if len(time_diffs) == 0:
            return "D"

        # 获取最常见的时间差
        mode_diff = time_diffs.mode()
        if len(mode_diff) == 0:
            median_diff = time_diffs.median()
        else:
            median_diff = mode_diff.iloc[0]

        # 转换为秒
        total_seconds = median_diff.total_seconds()

        # 推断频率
        if total_seconds < 60:  # 秒级
            freq = "S"
        elif total_seconds < 3600:  # 分钟级
            freq = "T"
        elif total_seconds < 86400:  # 小时级
            freq = "H"
        elif total_seconds < 86400 * 7:  # 天级
            freq = "D"
        elif total_seconds < 86400 * 28:  # 周级
            freq = "W"
        elif total_seconds < 86400 * 90:  # 月级
            freq = "MS"
        elif total_seconds < 86400 * 365:  # 季度级
            freq = "QS"
        else:  # 年级
            freq = "YS"

        safe_print(f"📊 Inferred frequency: {freq} (median interval: {median_diff})")
        return freq

    def _fill_missing_timestamps(self, df: pd.DataFrame, time_col: str, frequency: str) -> pd.DataFrame:
        """
        填充缺失的时间点并设置规则频率（参考 Databricks/Azure AutoML 策略）

        Args:
            df: 时序数据 DataFrame
            time_col: 时间列名
            frequency: 时间频率

        Returns:
            填充后的 DataFrame（带有规则频率的时间索引）
        """
        freq_map = {
            "D": "D", "days": "D", "day": "D",
            "W": "W", "weeks": "W", "week": "W",
            "M": "MS", "month": "MS", "months": "MS",
            "Q": "QS", "quarter": "QS", "quarters": "QS",
            "Y": "YS", "year": "YS", "years": "YS",
            "H": "H", "hours": "H", "hour": "H", "hr": "H", "h": "H",
            "T": "T", "min": "T", "minute": "T", "minutes": "T", "m": "T",
            "S": "S", "sec": "S", "second": "S", "seconds": "S",
        }

        # 如果 frequency 是 "auto" 或无法识别，自动推断
        if frequency.lower() == "auto" or frequency not in freq_map:
            safe_print(f"ℹ️  Frequency '{frequency}' not recognized or set to auto, inferring from data...")
            pd_freq = self._infer_frequency(df, time_col)
        else:
            pd_freq = freq_map.get(frequency, "D")

        date_min = df[time_col].min()
        date_max = df[time_col].max()

        # 创建完整的日期范围（带有 freq 属性）
        full_date_range = pd.date_range(start=date_min, end=date_max, freq=pd_freq)

        existing_dates = set(df[time_col])
        missing_dates = set(full_date_range) - existing_dates

        if missing_dates:
            safe_print(f"⚠️  Found {len(missing_dates)} missing time points, filling with forward fill...")

        # 设置时间列为索引
        df = df.set_index(time_col)

        # 重建索引为完整的日期范围（这会自动设置 freq 属性）
        df = df.reindex(full_date_range)
        df.index.name = time_col

        # 确保索引有 freq 属性
        if df.index.freq is None:
            df.index = pd.DatetimeIndex(df.index, freq=pd_freq)
            safe_print(f"✅ Set time index frequency to: {pd_freq}")

        # 前向填充 + 后向填充
        df = df.ffill().bfill()

        # 重置索引
        df = df.reset_index()

        if missing_dates:
            safe_print(f"✅ Missing time points filled. New shape: {df.shape}")
        else:
            safe_print(f"✅ Time series regularized with frequency: {pd_freq}")

        return df

    # ========================================================================
    # 私有方法：执行 AutoML 训练
    # ========================================================================
    def _run_automl_training(self, fit_kwargs: dict) -> float:
        """
        执行 FLAML AutoML 训练

        Args:
            fit_kwargs: FLAML fit 参数

        Returns:
            训练耗时（秒）
        """
        import logging as py_logging

        # 抑制日志
        flaml_logger = py_logging.getLogger("flaml.automl.logger")
        flaml_automl_logger = py_logging.getLogger("flaml.automl")
        mlflow_logger = py_logging.getLogger("mlflow.tracking._tracking_service.client")
        mlflow_utils_logger = py_logging.getLogger("mlflow.utils")

        original_levels = {
            "flaml": flaml_logger.level,
            "flaml_automl": flaml_automl_logger.level,
            "mlflow": mlflow_logger.level,
            "mlflow_utils": mlflow_utils_logger.level,
        }

        flaml_logger.setLevel(py_logging.WARNING)
        flaml_automl_logger.setLevel(py_logging.WARNING)
        mlflow_logger.setLevel(py_logging.WARNING)
        mlflow_utils_logger.setLevel(py_logging.WARNING)

        safe_print("Training in progress... (FLAML debug logs suppressed)")

        start_time = time.time()
        try:
            self.automl.fit(**fit_kwargs)
        finally:
            flaml_logger.setLevel(original_levels["flaml"])
            flaml_automl_logger.setLevel(original_levels["flaml_automl"])
            mlflow_logger.setLevel(original_levels["mlflow"])
            mlflow_utils_logger.setLevel(original_levels["mlflow_utils"])

        return time.time() - start_time

    # ========================================================================
    # 私有方法：上传日志文件
    # ========================================================================
    def _upload_log_file(self, log_file_path: str):
        """上传 FLAML 日志文件到 MLflow"""
        safe_print("", show_timestamp=False, show_level=False)
        safe_print("📤 Uploading FLAML log file to MLflow...")
        try:
            if os.path.exists(log_file_path):
                mlflow.log_artifact(log_file_path, artifact_path="flaml_logs")
                safe_print(f"✅ Log file uploaded: {os.path.basename(log_file_path)}")

                if self.auto_cleanup_logs:
                    try:
                        os.remove(log_file_path)
                        safe_print(f"✅ Local log file cleaned up: {log_file_path}")
                    except Exception as e:
                        safe_print(f"⚠️  Failed to cleanup local log file: {e}")
            else:
                safe_print(f"⚠️  Log file not found: {log_file_path}")
        except Exception as e:
            safe_print(f"⚠️  Failed to upload log file: {e}")
            if self.auto_cleanup_logs:
                try:
                    if os.path.exists(log_file_path):
                        os.remove(log_file_path)
                except Exception:
                    pass

    # ========================================================================
    # 私有方法：模型记录和注册
    # ========================================================================
    def _log_and_register_model(
        self,
        parent_run_id: str,
        X_train: pd.DataFrame
    ) -> tuple:
        """
        记录和注册模型

        Args:
            parent_run_id: 父 run ID
            X_train: 训练特征数据

        Returns:
            (model_uri, model_version)
        """
        safe_print("", show_timestamp=False, show_level=False)
        print_separator()
        safe_print(f"💾 Model Logging & Registration")
        print_separator()

        # 自动生成模型名称：实验名称_projectid_任务类型_datetime
        registered_model_name = None
        if self.register_model:
            if self.model_name:
                registered_model_name = self.model_name
            else:
                # 自动生成模型名称
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # 清理实验名称（移除特殊字符）
                exp_name = self.experiment_name or "automl"
                exp_name_clean = "".join(c if c.isalnum() or c == "_" else "_" for c in exp_name)
                project_id = self.project_id or "default"
                task_type = self.task or "model"
                registered_model_name = f"{exp_name_clean}_{project_id}_{task_type}_{timestamp}"
                safe_print(f"ℹ️  Auto-generated model name: {registered_model_name}")

        model_version = None
        model_uri = None

        # 时序预测任务使用专用方法记录模型
        if self.task == "forecast":
            safe_print(f"Using forecast model logging (pickle + artifact)")
            model_uri, model_version = self._log_model_with_mlflow(
                parent_run_id, registered_model_name, X_sample=X_train
            )
            return model_uri, model_version

        has_training_set = hasattr(self, '_training_set') and self._training_set is not None

        if has_training_set:
            safe_print(f"Using FeatureStoreClient.log_model (with feature lineage)")
            try:
                from wedata.feature_store.client import FeatureStoreClient
                from mlflow.models import infer_signature

                signature = None
                try:
                    X_sample = X_train.head(100) if len(X_train) > 100 else X_train
                    y_pred = self.pipeline.predict(X_sample)
                    signature = infer_signature(X_sample, y_pred)
                    safe_print(f"✅ Model signature inferred successfully")
                except Exception as e:
                    safe_print(f"⚠️  Failed to infer model signature: {e}")

                if not hasattr(self, '_fs_client') or self._fs_client is None:
                    self._fs_client = FeatureStoreClient()

                log_model_kwargs = {
                    "model": self.pipeline,
                    "artifact_path": "model",
                    "flavor": mlflow.sklearn,
                    "registered_model_name": registered_model_name,
                    "signature": signature,
                    "training_set": self._training_set,
                }

                self._fs_client.log_model(**log_model_kwargs)
                model_uri = f"runs:/{parent_run_id}/model"
                safe_print(f"✅ Model logged to MLflow: {model_uri}")

                if registered_model_name:
                    try:
                        client = mlflow.tracking.MlflowClient()
                        versions = client.search_model_versions(filter_string=f"name='{registered_model_name}'")
                        if versions:
                            model_version = max(v.version for v in versions)
                        safe_print(f"✅ Model registered: '{registered_model_name}' version {model_version}")
                        mlflow.set_tag("wedata.has_registered_model", "true")
                        # 设置 WeData 平台 tags
                        if model_version:
                            set_model_version_wedata_tags(
                                registered_model_name=registered_model_name,
                                model_version=model_version,
                                task=self.task
                            )
                    except Exception as e:
                        safe_print(f"⚠️  Could not get model version: {e}")
                        mlflow.set_tag("wedata.has_registered_model", "true")
                else:
                    safe_print(f"ℹ️  Model not registered (register_model={self.register_model}, model_name={self.model_name})")
                    mlflow.set_tag("wedata.has_registered_model", "false")

            except ImportError:
                safe_print(f"⚠️  wedata-feature-engineering not available, falling back to mlflow.sklearn.log_model")
                X_sample = X_train.head(100) if len(X_train) > 100 else X_train
                model_uri, model_version = self._log_model_with_mlflow(
                    parent_run_id, registered_model_name, X_sample=X_sample
                )
            except Exception as e:
                safe_print(f"⚠️  FeatureStoreClient.log_model failed: {e}")
                safe_print("   Falling back to mlflow.sklearn.log_model...")
                X_sample = X_train.head(100) if len(X_train) > 100 else X_train
                model_uri, model_version = self._log_model_with_mlflow(
                    parent_run_id, registered_model_name, X_sample=X_sample
                )
        else:
            safe_print(f"Using mlflow.sklearn.log_model")
            X_sample = X_train.head(100) if len(X_train) > 100 else X_train
            model_uri, model_version = self._log_model_with_mlflow(
                parent_run_id, registered_model_name, X_sample=X_sample
            )

        return model_uri, model_version

    # ========================================================================
    # 私有方法：创建 AutoMLSummary
    # ========================================================================
    def _create_summary(
        self,
        experiment,
        experiment_name: str,
        parent_run_id: str,
        best_trial_run_id: str,
        model_uri: str,
        model_version: str,
        metrics: dict,
        best_est: str,
        best_cfg: dict,
    ) -> AutoMLSummary:
        """创建 AutoMLSummary 对象"""
        task_kwargs = {}
        if self.task == "forecast":
            task_kwargs = {
                "time_col": self.kwargs.get("time_col"),
                "horizon": self.kwargs.get("horizon"),
                "frequency": self.kwargs.get("frequency"),
                "identity_col": self.kwargs.get("identity_col"),
            }

        # 添加数据源表名（如果用户传入表名）
        if self.data_source_table:
            task_kwargs["data_source_table"] = self.data_source_table

        return AutoMLSummary(
            experiment_id=experiment.experiment_id,
            run_id=parent_run_id,
            best_trial_run_id=best_trial_run_id,
            model_uri=model_uri,
            model_version=model_version,
            metrics=metrics,
            best_estimator=best_est,
            best_params=best_cfg,
            task=self.task,
            mlflow_tracking_uri=mlflow.get_tracking_uri(),
            features=self.features,
            target_col=self.target_col,
            metric=self.metric,
            task_kwargs=task_kwargs,
            project_id=self.project_id,
            experiment_name=experiment_name,
        )

    # ========================================================================
    # 私有方法：打印最终总结
    # ========================================================================
    def _print_final_summary(
        self,
        experiment_name: str,
        experiment_id: str,
        parent_run_id: str,
        best_est: str,
        model_uri: str,
        model_version: str,
        metrics: dict,
    ):
        """打印训练完成的最终总结"""
        safe_print("", show_timestamp=False, show_level=False)
        print_separator()
        safe_print(f"🎉 Training Pipeline Completed Successfully!")
        print_separator()
        safe_print(f"Experiment: {experiment_name} (ID: {experiment_id})")
        safe_print(f"Run ID: {parent_run_id}")
        safe_print(f"Best Model: {best_est}")
        if self.register_model and self.model_name:
            safe_print(f"Registered Model: {self.model_name} v{model_version}")
        safe_print(f"Model URI: {model_uri}")

        if self.task == "classification":
            test_acc = metrics.get("test_accuracy", 0)
            test_f1 = metrics.get("test_f1", 0)
            safe_print(f"Test Accuracy: {test_acc:.4f}")
            safe_print(f"Test F1 Score: {test_f1:.4f}")
        elif self.task == "regression":
            test_r2 = metrics.get("test_r2", 0)
            test_rmse = metrics.get("test_rmse", 0)
            safe_print(f"Test R²: {test_r2:.4f}")
            safe_print(f"Test RMSE: {test_rmse:.4f}")

        print_separator()

    # ========================================================================
    # 主方法：训练
    # ========================================================================
    def train(
        self,
        dataset: Union[pd.DataFrame, Any],
        data_source_table: str,
        spark=None
    ) -> AutoMLSummary:
        """
        训练模型

        Args:
            dataset: 数据集（Pandas DataFrame、Spark DataFrame 或表名）
            data_source_table: 数据源表名（三段式：catalog.schema.table_name），用于 notebook 生成
            spark: Spark session（如果 dataset 是表名）

        Returns:
            AutoMLSummary 对象
        """
        # 保存数据源表名
        self.data_source_table = data_source_table
        # ================================================================
        # 阶段 1: 数据加载
        # ================================================================
        pdf = self._load_data(dataset, spark)

        # ================================================================
        # 阶段 2: 特征存储查找（可选）
        # ================================================================
        if self.feature_store_lookups:
            safe_print("", show_timestamp=False, show_level=False)
            print_separator()
            safe_print("🔗 Feature Store Lookups", show_timestamp=False, show_level=False)
            print_separator()
            pdf = self._apply_feature_store_lookups(pdf, spark)

        # ================================================================
        # 阶段 3: 数据准备
        # ================================================================
        safe_print("", show_timestamp=False, show_level=False)
        print_separator()
        safe_print("🔧 Data Preparation", show_timestamp=False, show_level=False)
        print_separator()
        X_train, y_train, X_val, y_val, X_test, y_test, sample_weight_train = self._prepare_data(pdf)
        self._pdf = pdf  # 保存 pdf 引用（时序预测任务需要）

        # ================================================================
        # 阶段 4: 特征预处理
        # ================================================================
        safe_print("", show_timestamp=False, show_level=False)
        print_separator()
        safe_print(f"⚙️  Feature Preprocessing")
        print_separator()

        if self.imputers:
            safe_print(f"Custom imputers configured for {len(self.imputers)} columns:")
            for col, strategy in self.imputers.items():
                safe_print(f"  - {col}: {strategy}")
        else:
            safe_print(f"Using default imputer: auto (median)")

        self.preprocessor = build_numeric_preprocessor(
            self.features,
            imputers=self.imputers,
            default_imputer="auto"
        )
        X_train_num = self.preprocessor.fit_transform(X_train)
        X_val_num = self.preprocessor.transform(X_val)
        X_test_num = self.preprocessor.transform(X_test)

        safe_print(f"Preprocessor fitted successfully")
        safe_print(f"  - Train set: {X_train_num.shape}")
        safe_print(f"  - Val set:   {X_val_num.shape}")
        safe_print(f"  - Test set:  {X_test_num.shape}")

        # ================================================================
        # 阶段 5: MLflow 实验设置
        # ================================================================
        experiment, experiment_name, experiment_id = self._setup_mlflow_experiment()

        # ================================================================
        # 阶段 6: MLflow Run 和 AutoML 训练
        # ================================================================
        # 设置 user_id（从 QCLOUD_UIN 环境变量获取）
        setup_mlflow_user_id()

        with mlflow.start_run(run_name=self.run_name) as parent_run:
            parent_run_id = parent_run.info.run_id
            safe_print(f"Run name: '{self.run_name}'")
            safe_print(f"Run ID: {parent_run_id}")

            # 删除父 run 的 mlflow.source.name tag
            try:
                mlflow.delete_tag("mlflow.source.name")
            except Exception:
                pass

            # 设置 WeData 平台 tags
            set_run_wedata_tags(task=self.task)

            # 记录基本参数
            mlflow.log_params({
                "task": self.task,
                "target_col": self.target_col,
                "timeout_minutes": self.timeout_minutes,
                "metric": self.metric,
                "n_rows": len(pdf),
                "n_features": len(self.features),
            })

            # 记录数据源表名（如果用户传入表名）
            if self.data_source_table:
                mlflow.log_param("data_source_table", self.data_source_table)
                mlflow.set_tag("wedata.data_source_table", self.data_source_table)

            log_feature_list(self.features)
            log_engine_meta({"engine": "flaml", "version": getattr(flaml_pkg, "__version__", "unknown")})

            # ================================================================
            # 阶段 7: FLAML 配置
            # ================================================================
            safe_print("", show_timestamp=False, show_level=False)
            print_separator()
            safe_print(f"🤖 AutoML Training Configuration")
            print_separator()
            self.automl = AutoML()

            # 清理旧日志文件
            if self.auto_cleanup_logs:
                safe_print("", show_timestamp=False, show_level=False)
                safe_print("🧹 Cleaning up old log files...")
                try:
                    deleted_count = cleanup_old_log_files(
                        base_dir=self.log_file_dir,
                        max_age_hours=self.log_max_age_hours,
                        max_files=self.log_max_files,
                        dry_run=False
                    )
                    safe_print(f"✅ Deleted {deleted_count} old log files" if deleted_count > 0 else "✅ No old log files to clean up")
                except Exception as e:
                    safe_print(f"⚠️  Failed to cleanup old log files: {e}")

            # 生成日志文件路径
            log_file_path = generate_log_file_path(
                base_dir=self.log_file_dir,
                run_id=parent_run_id,
                use_timestamp=True,
                use_uuid=True
            )
            safe_print(f"📝 FLAML log file: {log_file_path}")

            # 构建 FLAML 设置
            settings = self._build_flaml_settings(log_file_path)

            safe_print("", show_timestamp=False, show_level=False)
            print_separator()
            safe_print("🚀 Starting AutoML Training...", show_timestamp=False, show_level=False)
            print_separator()

            # ================================================================
            # 阶段 8: 准备 fit 参数并训练
            # ================================================================
            safe_print("", show_timestamp=False, show_level=False)
            safe_print("🔧 Preparing TrialHook to log all trials...")
            trial_hook = TrialHook(
                parent_run_id=parent_run_id,
                features=self.features,
                task=self.task,
                metric=self.metric,
                enable_logging=True
            )

            # 准备 fit 参数
            if self.task == "forecast":
                fit_kwargs = self._prepare_forecast_data(settings)
            else:
                fit_kwargs = {
                    "X_train": X_train_num,
                    "y_train": y_train,
                    "X_val": X_val_num,
                    "y_val": y_val,
                    **settings,
                }
                if sample_weight_train is not None:
                    fit_kwargs["sample_weight"] = sample_weight_train
                    safe_print(f"Using sample weights for training")

            # 执行训练
            start_time = time.time()
            actual_train_time = self._run_automl_training(fit_kwargs)

            # 记录 trials
            trial_hook.log_trials_from_automl(
                self.automl,
                log_file_path=log_file_path,
                feature_names=self.features,
                time_budget=int(self.timeout_minutes * 60),
                train_time=actual_train_time
            )

            # 上传日志文件
            self._upload_log_file(log_file_path)

            # ================================================================
            # 阶段 9: 训练完成后处理
            # ================================================================
            elapsed_time = time.time() - start_time
            safe_print("", show_timestamp=False, show_level=False)
            print_separator()
            safe_print("✅ AutoML Training Completed", show_timestamp=False, show_level=False)
            print_separator()
            safe_print(f"Total training time: {elapsed_time:.1f}s ({elapsed_time/60:.2f} minutes)")

            trial_hook.print_summary()

            # 先为最佳子 run 设置所有必要的 tag（包括 mlflow.source.name, wedata.project 等）
            # 注意：forecast 任务不设置 source_name，因为不支持生成 notebook
            if self.task == "forecast":
                # forecast 任务：不设置 source_name，只设置其他 tag
                trial_hook.set_best_trial_tags(
                    source_name=None,  # 不设置 source.name
                    project_id=self.project_id,
                    task=self.task,
                )
            else:
                trial_hook.set_best_trial_tags(
                    source_name="wedata-automl",
                    project_id=self.project_id,
                    task=self.task,
                )
            # 然后清理其他子 run 的 mlflow.source.name（保留最佳子 run）
            trial_hook.cleanup_child_runs_source_name(experiment.experiment_id, preserve_best=True)

            # 获取 TrialHook 统计信息
            hook_summary = trial_hook.get_summary()
            total_trials_run = hook_summary['total_trials']
            best_trial_run_id = hook_summary['best_trial_run_id']
            best_trial_run_name = hook_summary['best_trial_run_name']

            # 记录最佳配置
            best_est = self.automl.best_estimator
            best_cfg = self.automl.best_config
            log_best_config_overall(best_cfg)
            if getattr(self.automl, "best_config_per_estimator", None):
                log_best_config_per_estimator(self.automl.best_config_per_estimator)

            mlflow.log_param("best_estimator", best_est)
            mlflow.log_param("best_trial_run_id", best_trial_run_id)
            mlflow.log_param("total_trials", total_trials_run)

            mlflow.set_tags({
                "wedata.total_trials_run": str(total_trials_run),
                "wedata.best_run_id": best_trial_run_id,
                "wedata.best_run_name": best_trial_run_name,
            })
            safe_print(f"✅ Tags set: total_trials_run={total_trials_run}, best_run_id={best_trial_run_id}, best_run_name={best_trial_run_name}")

            safe_print("", show_timestamp=False, show_level=False)
            safe_print(f"Best estimator: {best_est}")
            safe_print(f"Best config: {best_cfg}")

            # ================================================================
            # 阶段 10: 构建管道和评估
            # ================================================================
            safe_print("", show_timestamp=False, show_level=False)
            print_separator()
            safe_print(f"🔨 Building Serving Pipeline")
            print_separator()

            # 时序预测任务不构建 sklearn Pipeline（模型需要 TimeSeriesDataset 格式）
            if self.task == "forecast":
                self.pipeline = self.automl.model
                safe_print("Pipeline built: [TimeSeriesEstimator] (forecast mode)")
            else:
                clf = self.automl.model
                self.pipeline = SkPipe([("preprocess", self.preprocessor), ("clf", clf)])
                self.pipeline.fit(X_train, y_train)
                safe_print("Pipeline built: [Preprocessor] -> [Classifier/Regressor]")

            safe_print("", show_timestamp=False, show_level=False)
            print_separator()
            safe_print(f"📊 Model Evaluation")
            print_separator()

            # 时序预测任务跳过传统评估（评估在 FLAML 内部已完成）
            if self.task == "forecast":
                metrics = {"mape": self.automl.best_loss}
                # 记录指标到 MLflow
                mlflow.log_metric("best_mape", self.automl.best_loss)
                mlflow.log_metric("best_loss", self.automl.best_loss)
                # 用用户指定的指标名称也记录一份
                if self.metric:
                    mlflow.log_metric(f"best_{self.metric}", self.automl.best_loss)
                safe_print(f"  Best loss (MAPE): {self.automl.best_loss:.4f}")
            else:
                metrics = self._evaluate_model(X_train, y_train, X_val, y_val, X_test, y_test)

            # ================================================================
            # 阶段 11: 模型记录和注册
            # ================================================================
            model_uri, model_version = self._log_and_register_model(parent_run_id, X_train)

            # ================================================================
            # 阶段 11.5: 时序预测结果保存（可选）
            # ================================================================
            if self.task == "forecast" and self.prediction_result_storage:
                self._save_forecast_predictions(
                    parent_run_id=parent_run_id,
                    pdf=pdf,
                    spark=spark
                )

            # ================================================================
            # 阶段 11.6: 注册模型到 TencentCloud Catalog（可选）
            # ================================================================
            catalog_result = None
            if self.register_to_catalog:
                safe_print("", show_timestamp=False, show_level=False)
                print_separator()
                safe_print(f"📦 Registering Model to TencentCloud Catalog")
                print_separator()

                # 生成 Catalog 模型名称（格式：catalog.schema.model_name）
                if self.catalog_model_name:
                    catalog_model_name = self.catalog_model_name
                else:
                    # 自动生成：从 data_source_table 解析 catalog 和 schema
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    exp_name_clean = "".join(c if c.isalnum() or c == "_" else "_" for c in (self.experiment_name or "automl"))
                    model_name_part = f"{exp_name_clean}_{self.task}_{timestamp}"

                    # 从 data_source_table 解析 catalog 和 schema
                    if self.data_source_table:
                        table_parts = self.data_source_table.split('.')
                        if len(table_parts) >= 3:
                            catalog_name = table_parts[0]
                            schema_name = table_parts[1]
                        elif len(table_parts) == 2:
                            catalog_name = os.getenv('TENCENTCLOUD_DEFAULT_CATALOG_NAME', 'default')
                            schema_name = table_parts[0]
                        else:
                            catalog_name = os.getenv('TENCENTCLOUD_DEFAULT_CATALOG_NAME', 'default')
                            schema_name = os.getenv('TENCENTCLOUD_DEFAULT_SCHEMA_NAME', 'default')
                    else:
                        # 没有 data_source_table，使用默认值
                        catalog_name = os.getenv('TENCENTCLOUD_DEFAULT_CATALOG_NAME', 'default')
                        schema_name = os.getenv('TENCENTCLOUD_DEFAULT_SCHEMA_NAME', 'default')

                    # 构建三段式模型名称
                    catalog_model_name = f"{catalog_name}.{schema_name}.{model_name_part}"
                    safe_print(f"ℹ️  Auto-generated catalog model name: {catalog_model_name}")
                    safe_print(f"   Catalog: {catalog_name}, Schema: {schema_name}, Model: {model_name_part}")

                # 构建 run link
                tracking_uri = mlflow.get_tracking_uri()
                run_link = f"{tracking_uri}/#/experiments/{experiment.experiment_id}/runs/{best_trial_run_id}"

                # 调用注册方法
                catalog_result = trial_hook.register_best_model_to_catalog(
                    model_uri=model_uri,
                    model_name=catalog_model_name,
                    region=self.catalog_region,
                    description=f"AutoML {self.task} model - {best_est}",
                    run_link=run_link,
                )

                if catalog_result:
                    safe_print(f"✅ Model registered to Catalog: {catalog_model_name} v{catalog_result.get('version')}")
                else:
                    safe_print(f"⚠️  Catalog registration skipped or failed")

            # ================================================================
            # 阶段 12: 创建 Summary 并返回
            # ================================================================
            summary = self._create_summary(
                experiment=experiment,
                experiment_name=experiment_name,
                parent_run_id=parent_run_id,
                best_trial_run_id=best_trial_run_id,
                model_uri=model_uri,
                model_version=model_version,
                metrics=metrics,
                best_est=best_est,
                best_cfg=best_cfg,
            )

            self._print_final_summary(
                experiment_name=experiment_name,
                experiment_id=experiment.experiment_id,
                parent_run_id=parent_run_id,
                best_est=best_est,
                model_uri=model_uri,
                model_version=model_version,
                metrics=metrics,
            )

            return summary

