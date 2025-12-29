"""
AutoML Summary - 训练结果摘要对象

对齐 Databricks AutoML 的 AutoMLSummary 类
"""
import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class AutoMLSummary:
    """
    AutoML 训练结果摘要

    对齐 Databricks AutoML 的 AutoMLSummary 类

    Attributes:
        experiment_id: MLflow 实验 ID
        run_id: 主 run ID
        best_trial_run_id: 最佳 trial 的 run ID
        model_uri: 模型 URI (格式: runs:/<run_id>/model)
        model_version: 注册的模型版本号（如果注册了）
        metrics: 评估指标字典
        best_estimator: 最佳估计器名称
        best_params: 最佳超参数
        artifacts: 产物路径字典
        task: 任务类型 ("classification", "regression", "forecast")
        mlflow_tracking_uri: MLflow Tracking URI
        features: 特征列名列表
        target_col: 目标列名
        metric: 评估指标名称
        task_kwargs: 任务特定参数
        project_id: 项目 ID（用于 WeData 平台）
        experiment_name: 实验名称
    """
    experiment_id: str
    run_id: str
    best_trial_run_id: str
    model_uri: str
    model_version: Optional[int] = None
    metrics: Optional[Dict[str, float]] = None
    best_estimator: Optional[str] = None
    best_params: Optional[Dict[str, Any]] = None
    artifacts: Optional[Dict[str, str]] = None
    task: Optional[str] = None
    mlflow_tracking_uri: Optional[str] = None
    features: Optional[List[str]] = None
    target_col: Optional[str] = None
    metric: Optional[str] = None
    task_kwargs: Dict[str, Any] = field(default_factory=dict)
    project_id: Optional[str] = None
    experiment_name: Optional[str] = None
    
    def __repr__(self) -> str:
        """字符串表示"""
        lines = [
            "AutoMLSummary:",
            f"  Experiment ID: {self.experiment_id}",
            f"  Run ID: {self.run_id}",
            f"  Best Trial Run ID: {self.best_trial_run_id}",
            f"  Model URI: {self.model_uri}",
        ]
        
        if self.model_version is not None:
            lines.append(f"  Model Version: {self.model_version}")
        
        if self.best_estimator:
            lines.append(f"  Best Estimator: {self.best_estimator}")
        
        if self.metrics:
            lines.append("  Metrics:")
            for key, value in self.metrics.items():
                lines.append(f"    {key}: {value:.4f}")
        
        if self.best_params:
            lines.append("  Best Params:")
            for key, value in self.best_params.items():
                lines.append(f"    {key}: {value}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "best_trial_run_id": self.best_trial_run_id,
            "model_uri": self.model_uri,
            "model_version": self.model_version,
            "metrics": self.metrics,
            "best_estimator": self.best_estimator,
            "best_params": self.best_params,
            "artifacts": self.artifacts,
            "task": self.task,
            "mlflow_tracking_uri": self.mlflow_tracking_uri,
            "features": self.features,
            "target_col": self.target_col,
            "metric": self.metric,
            "task_kwargs": self.task_kwargs,
            "project_id": self.project_id,
            "experiment_name": self.experiment_name,
        }

    def generate_notebook(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成可复现的 Jupyter Notebook

        注意：forecast 任务不支持生成 notebook，会抛出 ValueError

        Args:
            output_path: 输出路径（可选）。如果提供，将保存到文件

        Returns:
            Notebook 字典（符合 Jupyter Notebook 格式）

        Raises:
            ValueError: 如果任务类型为 forecast（预测任务不生成 notebook）

        Example:
            >>> summary = classify(...)
            >>> # 生成并保存 Notebook
            >>> summary.generate_notebook("best_model.ipynb")
            >>> # 或者只生成不保存
            >>> notebook = summary.generate_notebook()
        """
        from wedata_automl.notebook_generator import NotebookGenerator

        if not self.task:
            raise ValueError("Cannot generate notebook: task type is not set")

        # 🆕 forecast 任务不生成 notebook
        if self.task == "forecast":
            raise ValueError(
                "Forecast task does not support notebook generation. "
                "Prediction results are saved directly to DLC table via PredictionResultStorage parameter."
            )

        if not self.best_estimator or not self.best_params:
            raise ValueError("Cannot generate notebook: best estimator or params not available")

        generator = NotebookGenerator(
            task=self.task,
            best_estimator=self.best_estimator,
            best_config=self.best_params,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            mlflow_tracking_uri=self.mlflow_tracking_uri or "http://localhost:5000",
            features=self.features or [],
            target_col=self.target_col or "target",
            metric=self.metric or "accuracy",
            **self.task_kwargs
        )

        return generator.generate(output_path=output_path)

    def save_notebook_to_wedata(
        self,
        script_name: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "ap-guangzhou",
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成 Notebook 并保存到 WeData 平台

        调用 CreateExploreScriptByOwnerUin API 将生成的 notebook 保存到 WeData 数据探索脚本中。

        注意：forecast 任务不支持此方法，会抛出 ValueError

        Args:
            script_name: 脚本名称，默认使用实验名称 + .ipynb 后缀
            parent_folder_id: 父文件夹 ID，默认从环境变量 WEDATA_PARENT_FOLDER_ID 获取
            secret_id: 腾讯云 Secret ID，默认从环境变量 TENCENTCLOUD_SECRET_ID 获取
            secret_key: 腾讯云 Secret Key，默认从环境变量 TENCENTCLOUD_SECRET_KEY 获取
            region: 地域，默认 "ap-guangzhou"

        Returns:
            创建结果字典，包含:
                - script_id: 脚本 ID
                - script_name: 脚本名称
                - success: 是否成功
                - message: 消息

        Raises:
            ValueError: 如果缺少必要的参数（project_id, parent_folder_id, secret_id, secret_key）
            ValueError: 如果任务类型为 forecast（预测任务不生成 notebook）

        Example:
            >>> summary = classify(...)
            >>> result = summary.save_notebook_to_wedata()
            >>> print(f"Notebook saved: {result['script_id']}")
        """
        # 🆕 forecast 任务不支持保存 notebook
        if self.task == "forecast":
            raise ValueError(
                "Forecast task does not support notebook generation. "
                "Prediction results are saved directly to DLC table via PredictionResultStorage parameter."
            )

        from wedata_automl.utils.cloud_sdk_client.client import FeatureCloudSDK
        from wedata_automl.utils.cloud_sdk_client import models

        # 获取参数，优先使用传入值，否则使用环境变量
        project_id = self.project_id or os.environ.get("WEDATA_PROJECT_ID")
        parent_folder_id = parent_folder_id or os.environ.get("WEDATA_PARENT_FOLDER_ID")
        secret_id = secret_id or os.environ.get("TENCENTCLOUD_SECRET_ID")
        secret_key = secret_key or os.environ.get("TENCENTCLOUD_SECRET_KEY")
        token = token or os.environ.get("TENCENTCLOUD_TMP_TOKEN")

        # 验证必要参数
        if not project_id:
            raise ValueError(
                "❌ 未配置 Project ID！\n"
                "请通过以下任一方式配置：\n"
                "1. 在训练时传入 project_id 参数\n"
                "2. 设置环境变量：export WEDATA_PROJECT_ID='your_project_id'"
            )

        if not parent_folder_id:
            raise ValueError(
                "❌ 未配置 Parent Folder ID！\n"
                "请通过以下任一方式配置：\n"
                "1. 传入 parent_folder_id 参数\n"
                "2. 设置环境变量：export WEDATA_PARENT_FOLDER_ID='your_folder_id'"
            )

        if not secret_id or not secret_key:
            raise ValueError(
                "❌ 未配置腾讯云认证信息！\n"
                "请设置以下环境变量：\n"
                "  export TENCENTCLOUD_SECRET_ID='your_secret_id'\n"
                "  export TENCENTCLOUD_SECRET_KEY='your_secret_key'"
            )

        # 生成脚本名称
        if not script_name:
            # 使用实验名称，如果没有则使用默认名称
            base_name = self.experiment_name or f"automl_{self.task}"
            # 确保以 .ipynb 结尾
            if not base_name.endswith(".ipynb"):
                script_name = f"{base_name}.ipynb"
            else:
                script_name = base_name

        # 生成 Notebook 内容
        notebook = self.generate_notebook()
        script_content = json.dumps(notebook, ensure_ascii=False, indent=2)

        # 创建 SDK 客户端
        client = FeatureCloudSDK(
            secret_id=secret_id,
            secret_key=secret_key,
            region=region,
            token=token
        )

        # 创建请求
        request = models.CreateExploreScriptRequest()
        request.ScriptName = script_name
        request.ExtensionType = "code_studio"
        request.ScriptContent = script_content
        request.ProjectId = project_id
        request.ParentFolderId = parent_folder_id

        # 调用 CreateExploreScriptByOwnerUin API
        try:
            print(f"📝 Step 1: CreateExploreScriptByOwnerUin...")
            print(f"   ScriptName: {script_name}")
            print(f"   ProjectId: {project_id}")
            print(f"   ParentFolderId: {parent_folder_id}")

            response = client.CreateExploreScriptByOwnerUin(request)

            if response.Data:
                script = response.Data
                file_id = script.ScriptId  # FileId 就是 ScriptId
                # version_id = "1"

                # 构建 notebook 路径: /FileId=xxx&VersionId=xxx
                print(f"\n📝 Step 3: 构建 Notebook 路径...")

                notebook_path = f"FileId={file_id}"


                # 更新 MLflow source.name
                print(f"\n📝 Step 4: 更新 MLflow source.name...")
                print(f"   run_id: {self.run_id}")
                print(f"   best_trial_run_id: {self.best_trial_run_id}")
                self._update_run_source_name(notebook_path)
                print(f"   ✅ MLflow source.name 已更新为: {notebook_path}")

                return {
                    "success": True,
                    "script_id": file_id,
                    "file_id": file_id,
                    "script_name": script.ScriptName,
                    "notebook_path": notebook_path,
                    "extension_type": script.ExtensionType,
                    "create_time": script.CreateTime,
                    "message": f"✅ Notebook 保存成功: {script.ScriptName} (FileId={file_id})"
                }
            else:
                print(f"   ❌ CreateExploreScriptByOwnerUin 返回空数据")
                return {
                    "success": False,
                    "script_id": None,
                    "file_id": None,
                    "script_name": script_name,
                    "notebook_path": None,
                    "message": "❌ Notebook 保存失败: 响应数据为空"
                }
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return {
                "success": False,
                "script_id": None,
                "file_id": None,
                "script_name": script_name,
                "notebook_path": None,
                "message": f"❌ Notebook 保存失败: {str(e)}"
            }

    def _update_run_source_name(self, notebook_path: str) -> None:
        """
        更新父 run 和最佳子 run 的 mlflow.source.name tag

        在 AutoML 训练完成后，用生成的 notebook 路径更新父 run 和最佳子 run 的 source.name，
        这样在 MLflow UI 中可以看到正确的代码来源。

        Args:
            notebook_path: Notebook 的路径，例如 "/automl_notebook.ipynb"
        """
        import mlflow

        try:
            # 使用 MLflow client 更新 tag（可以更新已结束的 run）
            client = mlflow.tracking.MlflowClient()
            # 更新父 run 的 source.name
            client.set_tag(self.run_id, "mlflow.source.name", notebook_path)
            print(f"      ✅ 父 run ({self.run_id}) source.name 已更新")
            # 🆕 同时更新最佳子 run 的 source.name
            if self.best_trial_run_id:
                client.set_tag(self.best_trial_run_id, "mlflow.source.name", notebook_path)
                print(f"      ✅ 最佳子 run ({self.best_trial_run_id}) source.name 已更新")
        except Exception as e:
            # 记录失败日志
            print(f"      ❌ 更新 source.name 失败: {e}")

    def update_source_name(self, notebook_path: str) -> bool:
        """
        手动更新父 run 和最佳子 run 的 mlflow.source.name tag

        如果不使用 save_notebook_to_wedata，可以调用此方法手动设置 notebook 路径。
        父 run 和最佳子 run 都会被更新。

        Args:
            notebook_path: Notebook 的路径，例如 "/my_notebook.ipynb"

        Returns:
            是否成功更新（父 run 和最佳子 run 都成功才返回 True）

        Example:
            >>> summary = classify(...)
            >>> # 生成 notebook 到本地
            >>> summary.generate_notebook("/path/to/notebook.ipynb")
            >>> # 更新父 run 和最佳子 run 的 source.name
            >>> summary.update_source_name("/path/to/notebook.ipynb")
        """
        import mlflow

        try:
            client = mlflow.tracking.MlflowClient()
            # 更新父 run 的 source.name
            client.set_tag(self.run_id, "mlflow.source.name", notebook_path)
            # 🆕 同时更新最佳子 run 的 source.name
            if self.best_trial_run_id:
                client.set_tag(self.best_trial_run_id, "mlflow.source.name", notebook_path)
            return True
        except Exception as e:
            return False

