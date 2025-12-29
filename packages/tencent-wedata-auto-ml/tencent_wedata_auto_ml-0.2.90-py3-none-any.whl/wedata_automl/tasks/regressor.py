"""
回归任务类

对齐 Databricks AutoML 的 Regressor 类
"""
from typing import Any, List, Optional, Union
import pandas as pd
import logging

from wedata_automl.summary import AutoMLSummary
from wedata_automl.tasks.base import SupervisedLearner
from wedata_automl.engines.flaml_trainer import FLAMLTrainer

logger = logging.getLogger(__name__)


class Regressor(SupervisedLearner):
    """
    回归任务类
    
    对齐 Databricks AutoML 的 Regressor 类
    
    Example:
        >>> from wedata_automl.tasks import Regressor
        >>> regressor = Regressor()
        >>> summary = regressor.fit(
        ...     dataset=spark.table("demo.house_prices"),
        ...     target_col="price",
        ...     timeout_minutes=5,
        ...     max_trials=100
        ... )
    """
    
    def fit(
        self,
        dataset: Union[pd.DataFrame, Any, str],
        target_col: str,
        data_source_table: str,
        timeout_minutes: int = 5,
        max_trials: Optional[int] = None,
        metric: str = "auto",
        exclude_cols: Optional[List[str]] = None,
        exclude_frameworks: Optional[List[str]] = None,
        estimator_list: Optional[List[str]] = None,
        sample_weight_col: Optional[str] = None,
        data_split_col: Optional[str] = None,
        experiment_name: Optional[str] = None,
        experiment_id: Optional[str] = None,
        run_name: Optional[str] = None,
        register_model: bool = True,
        model_name: Optional[str] = None,
        max_concurrent_trials: int = 1,
        use_spark: bool = False,
        custom_hp: Optional[dict] = None,
        project_id: Optional[str] = None,
        imputers: Optional[dict] = None,
        spark=None,
        **kwargs
    ) -> AutoMLSummary:
        """
        训练回归模型

        Args:
            dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
            target_col: 目标列名
            data_source_table: 数据源表名（三段式：catalog.schema.table_name），用于 notebook 生成和模型注册
            timeout_minutes: 超时时间（分钟），默认 5
            max_trials: 最大试验次数，默认 None（无限制）
            metric: 评估指标，默认 "auto"（自动选择 r2）
                - deviance: Deviance（默认）
                - rmse: Root Mean Squared Error
                - mae: Mean Absolute Error
                - r2: R-squared
                - mse: Mean Squared Error
                - auto: 自动选择
            exclude_cols: 排除的列，默认 None
            exclude_frameworks: 排除的框架，默认 None（已弃用，请使用 estimator_list）
                - sklearn: Scikit-learn 算法
                - xgboost: XGBoost
                - lightgbm: LightGBM
                默认全选（sklearn, xgboost, lightgbm）
            estimator_list: 估计器列表，默认 None（使用所有可用估计器）
                可选值: ["lgbm", "xgboost", "rf", "extra_tree"]
                例如: ["lgbm", "xgboost"] 只使用 LightGBM 和 XGBoost
            sample_weight_col: 样本权重列，默认 None
            data_split_col: 数据划分列，默认 None
            experiment_name: MLflow 实验名称，默认 None
            experiment_id: MLflow 实验 ID，默认 None
            run_name: MLflow run 名称，默认 None
            register_model: 是否注册模型，默认 True
            model_name: 模型名称，默认 None
            max_concurrent_trials: 最大并发试验数，默认 1，最大 100
            custom_hp: 自定义超参数搜索空间，默认 None
                格式: {estimator_name: {param_name: search_space}}
                例如: {"lgbm": {"n_estimators": {"domain": range(100, 1000), "init_value": 100}}}
            project_id: 项目 ID，用于多租户隔离，默认 None
                - 优先使用传入的 project_id 参数
                - 如果未传入，则从环境变量 WEDATA_PROJECT_ID 读取
                - 如果都未配置，则抛出 ValueError 异常
            spark: Spark session，默认 None
            **kwargs: 其他参数

        Returns:
            AutoMLSummary 对象

        Raises:
            ValueError: 如果 project_id 未配置（既未传入参数，也未设置环境变量）

        Example:
            >>> regressor = Regressor()
            >>> summary = regressor.fit(
            ...     dataset=spark.table("demo.house_prices"),
            ...     target_col="price",
            ...     timeout_minutes=5,
            ...     max_trials=100,
            ...     metric="r2",
            ...     exclude_cols=["id", "timestamp"],
            ...     experiment_name="house_price_regression",
            ...     register_model=True,
            ...     model_name="house_price_model"
            ... )
            >>> print(summary)

            # 使用自定义搜索空间
            >>> custom_search_space = {
            ...     "lgbm": {
            ...         "n_estimators": {"domain": range(100, 500), "init_value": 100},
            ...         "learning_rate": {"domain": (0.01, 0.3), "init_value": 0.1}
            ...     }
            ... }
            >>> summary = regressor.fit(
            ...     dataset=df,
            ...     target_col="price",
            ...     custom_hp=custom_search_space
            ... )
        """
        logger.info(f"Starting regression task with target_col={target_col}")

        # 验证参数
        if max_concurrent_trials < 1 or max_concurrent_trials > 100:
            raise ValueError("max_concurrent_trials must be between 1 and 100")

        # 验证评估指标
        valid_metrics = ["deviance", "rmse", "mae", "r2", "mse", "auto"]
        if metric not in valid_metrics:
            raise ValueError(f"metric must be one of {valid_metrics}, got {metric}")

        # 创建 FLAMLTrainer
        trainer = FLAMLTrainer(
            task="regression",
            target_col=target_col,
            timeout_minutes=timeout_minutes,
            max_trials=max_trials,
            metric=metric,
            exclude_cols=exclude_cols,
            exclude_frameworks=exclude_frameworks,
            estimator_list=estimator_list,
            sample_weight_col=sample_weight_col,
            data_split_col=data_split_col,
            experiment_name=experiment_name,
            experiment_id=experiment_id,
            run_name=run_name or "regression",
            register_model=register_model,
            model_name=model_name,
            max_concurrent_trials=max_concurrent_trials,
            use_spark=use_spark,
            custom_hp=custom_hp,
            project_id=project_id,
            imputers=imputers,
            **kwargs
        )
        
        # 训练
        summary = trainer.train(dataset, data_source_table=data_source_table, spark=spark)

        logger.info(f"Regression task completed. Best estimator: {summary.best_estimator}")
        
        return summary

