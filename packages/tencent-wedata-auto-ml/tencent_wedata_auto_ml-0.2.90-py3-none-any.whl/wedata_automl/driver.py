"""
WeData AutoML Driver

通用的 AutoML 驱动程序，根据配置自动选择对应的任务类执行实验
类似于 Databricks AutoML 的做法
"""
from typing import Any, Dict, Optional, Union
import logging

from wedata_automl.tasks import Classifier, Regressor, Forecast
from wedata_automl.summary import AutoMLSummary

logger = logging.getLogger(__name__)


class AutoMLDriver:
    """
    AutoML 驱动程序
    
    根据配置自动选择对应的任务类（Classifier/Regressor/Forecast）执行实验
    """
    
    # 支持的任务类型
    SUPPORTED_TASKS = {
        "classification": Classifier,
        "regression": Regressor,
        "forecast": Forecast,
    }
    
    @classmethod
    def run(
        cls,
        task: str,
        dataset: Union[Any, str],
        target_col: str,
        **kwargs
    ) -> AutoMLSummary:
        """
        运行 AutoML 实验
        
        Args:
            task: 任务类型 ("classification", "regression", "forecast")
            dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
            target_col: 目标列名
            **kwargs: 其他参数，根据任务类型不同而不同
            
        Returns:
            AutoMLSummary 对象
            
        Example:
            >>> # 分类任务
            >>> summary = AutoMLDriver.run(
            ...     task="classification",
            ...     dataset=spark.table("demo.wine_quality"),
            ...     target_col="quality",
            ...     timeout_minutes=60,
            ...     max_trials=100,
            ...     metric="accuracy"
            ... )
            
            >>> # 回归任务
            >>> summary = AutoMLDriver.run(
            ...     task="regression",
            ...     dataset=spark.table("demo.house_prices"),
            ...     target_col="price",
            ...     timeout_minutes=60,
            ...     max_trials=100,
            ...     metric="r2"
            ... )
            
            >>> # 时序预测任务
            >>> summary = AutoMLDriver.run(
            ...     task="forecast",
            ...     dataset=spark.table("demo.sales_data"),
            ...     target_col="sales",
            ...     time_col="date",
            ...     horizon=30,
            ...     frequency="D",
            ...     timeout_minutes=60,
            ...     max_trials=100,
            ...     metric="smape"
            ... )
        """
        # 验证任务类型
        if task not in cls.SUPPORTED_TASKS:
            raise ValueError(
                f"Unsupported task type: {task}. "
                f"Supported tasks: {list(cls.SUPPORTED_TASKS.keys())}"
            )
        
        # 获取对应的任务类
        task_class = cls.SUPPORTED_TASKS[task]
        
        logger.info(f"Starting AutoML with task={task}, task_class={task_class.__name__}")
        
        # 创建任务实例
        task_instance = task_class()
        
        # 执行训练
        summary = task_instance.fit(
            dataset=dataset,
            target_col=target_col,
            **kwargs
        )
        
        logger.info(f"AutoML completed. Best estimator: {summary.best_estimator}")
        
        return summary


def run_automl(config: Dict[str, Any]) -> AutoMLSummary:
    """
    根据配置字典运行 AutoML
    
    这是一个便捷函数，接受配置字典并调用 AutoMLDriver.run()
    
    Args:
        config: 配置字典，必须包含以下键：
            - task: 任务类型 ("classification", "regression", "forecast")
            - dataset: 数据集
            - target_col: 目标列名
            其他可选参数根据任务类型不同而不同
            
    Returns:
        AutoMLSummary 对象
        
    Example:
        >>> config = {
        ...     "task": "classification",
        ...     "dataset": spark.table("demo.wine_quality"),
        ...     "target_col": "quality",
        ...     "timeout_minutes": 60,
        ...     "max_trials": 100,
        ...     "metric": "accuracy",
        ...     "experiment_name": "wine_classification",
        ...     "register_model": True,
        ...     "model_name": "wine_model"
        ... }
        >>> summary = run_automl(config)
    """
    # 提取必需参数
    task = config.pop("task")
    dataset = config.pop("dataset")
    target_col = config.pop("target_col")
    
    # 其他参数作为 kwargs
    return AutoMLDriver.run(
        task=task,
        dataset=dataset,
        target_col=target_col,
        **config
    )

