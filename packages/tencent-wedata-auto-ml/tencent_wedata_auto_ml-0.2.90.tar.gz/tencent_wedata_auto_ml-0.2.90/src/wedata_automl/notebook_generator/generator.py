"""
Notebook Generator

生成可复现的 Jupyter Notebook
"""
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from wedata_automl.notebook_generator.templates import (
    ClassificationNotebookTemplate,
    RegressionNotebookTemplate,
    ForecastNotebookTemplate,
)


class NotebookGenerator:
    """
    Notebook 生成器
    
    根据 AutoML 训练结果生成可复现的 Jupyter Notebook
    """
    
    TEMPLATE_MAP = {
        "classification": ClassificationNotebookTemplate,
        "regression": RegressionNotebookTemplate,
        "forecast": ForecastNotebookTemplate,
    }
    
    def __init__(
        self,
        task: str,
        best_estimator: str,
        best_config: Dict[str, Any],
        experiment_id: str,
        run_id: str,
        mlflow_tracking_uri: str,
        features: List[str],
        target_col: str,
        metric: str,
        # 环境变量配置（从 driver 读取并渲染到 notebook）
        tencentcloud_secret_id: Optional[str] = None,
        tencentcloud_secret_key: Optional[str] = None,
        tencentcloud_tmp_token: Optional[str] = None,
        tencentcloud_endpoint: Optional[str] = None,
        wedata_project_id: Optional[str] = None,
        qcloud_region: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Notebook 生成器

        Args:
            task: 任务类型 ("classification", "regression", "forecast")
            best_estimator: 最佳估计器名称
            best_config: 最佳超参数配置
            experiment_id: MLflow 实验 ID
            run_id: MLflow Run ID
            mlflow_tracking_uri: MLflow Tracking URI
            features: 特征列名列表
            target_col: 目标列名
            metric: 评估指标
            tencentcloud_secret_id: 腾讯云 Secret ID（用于注册到 TCCatalog）
            tencentcloud_secret_key: 腾讯云 Secret Key（用于注册到 TCCatalog）
            tencentcloud_tmp_token: 腾讯云临时 Token（可选）
            tencentcloud_endpoint: TCCatalog API 端点
            wedata_project_id: WeData 项目 ID
            qcloud_region: 腾讯云地域（如 ap-guangzhou）
            **kwargs: 其他任务特定参数
        """
        if task not in self.TEMPLATE_MAP:
            raise ValueError(f"Unsupported task: {task}. Supported: {list(self.TEMPLATE_MAP.keys())}")

        self.task = task
        self.best_estimator = best_estimator
        self.best_config = best_config
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.features = features
        self.target_col = target_col
        self.metric = metric

        # 环境变量配置（优先使用传入的参数，其次从环境变量读取）
        self.tencentcloud_secret_id = tencentcloud_secret_id or os.environ.get('TENCENTCLOUD_SECRET_ID')
        self.tencentcloud_secret_key = tencentcloud_secret_key or os.environ.get('TENCENTCLOUD_SECRET_KEY')
        self.tencentcloud_tmp_token = tencentcloud_tmp_token or os.environ.get('TENCENTCLOUD_TMP_TOKEN')
        self.tencentcloud_endpoint = tencentcloud_endpoint or os.environ.get('TENCENTCLOUD_ENDPOINT', 'tccatalog.internal.tencentcloudapi.com')
        self.wedata_project_id = wedata_project_id or os.environ.get('WEDATA_PROJECT_ID')
        self.qcloud_region = qcloud_region or os.environ.get('QCLOUD_REGION', 'ap-guangzhou')

        self.kwargs = kwargs

        # 获取对应的模板类
        self.template_class = self.TEMPLATE_MAP[task]
    
    def generate(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 Notebook

        Args:
            output_path: 输出路径（可选）。如果提供，将保存到文件

        Returns:
            Notebook 字典（符合 Jupyter Notebook 格式）
        """
        # 创建模板实例
        template = self.template_class(
            best_estimator=self.best_estimator,
            best_config=self.best_config,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            mlflow_tracking_uri=self.mlflow_tracking_uri,
            features=self.features,
            target_col=self.target_col,
            metric=self.metric,
            # 传递环境变量配置
            tencentcloud_secret_id=self.tencentcloud_secret_id,
            tencentcloud_secret_key=self.tencentcloud_secret_key,
            tencentcloud_tmp_token=self.tencentcloud_tmp_token,
            tencentcloud_endpoint=self.tencentcloud_endpoint,
            wedata_project_id=self.wedata_project_id,
            qcloud_region=self.qcloud_region,
            **self.kwargs
        )
        
        # 生成 Notebook
        notebook = template.generate()
        
        # 如果提供了输出路径，保存到文件
        if output_path:
            self._save_notebook(notebook, output_path)
        
        return notebook
    
    def _save_notebook(self, notebook: Dict[str, Any], output_path: str):
        """
        保存 Notebook 到文件
        
        Args:
            notebook: Notebook 字典
            output_path: 输出路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        # 保存为 JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Notebook 已保存到: {output_path}")
    
    @staticmethod
    def create_cell(cell_type: str, source: List[str], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        创建 Notebook Cell
        
        Args:
            cell_type: Cell 类型 ("code", "markdown")
            source: Cell 内容（行列表）
            metadata: Cell 元数据
        
        Returns:
            Cell 字典
        """
        cell = {
            "cell_type": cell_type,
            "metadata": metadata or {},
            "source": source
        }
        
        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        
        return cell

