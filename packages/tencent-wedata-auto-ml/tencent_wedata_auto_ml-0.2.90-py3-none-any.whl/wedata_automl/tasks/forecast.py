"""
时序预测任务类

对齐 Databricks AutoML 的 Forecast 类
"""
from typing import Any, List, Optional, Union
import pandas as pd
import logging

from wedata_automl.summary import AutoMLSummary
from wedata_automl.tasks.base import BaseAutoML
from wedata_automl.engines.flaml_trainer import FLAMLTrainer

logger = logging.getLogger(__name__)


class Forecast(BaseAutoML):
    """
    时序预测任务类
    
    对齐 Databricks AutoML 的 Forecast 类
    
    Example:
        >>> from wedata_automl.tasks import Forecast
        >>> forecast = Forecast()
        >>> summary = forecast.fit(
        ...     dataset=spark.table("demo.sales_data"),
        ...     target_col="sales",
        ...     time_col="date",
        ...     horizon=30,
        ...     frequency="D",
        ...     timeout_minutes=10,
        ...     max_trials=100
        ... )
    """
    
    def fit(
        self,
        dataset: Union[pd.DataFrame, Any, str],
        target_col: str,
        time_col: str,
        horizon: int,
        data_source_table: str,
        frequency: str = "D",
        identity_col: Optional[List[str]] = None,
        timeout_minutes: int = 60,
        max_trials: Optional[int] = 100,
        metric: str = "smape",
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
        custom_hp: Optional[dict] = None,
        project_id: Optional[str] = None,
        country_code: Optional[str] = "US",
        feature_store_lookups: Optional[list] = None,
        prediction_result_storage: Optional[str] = None,
        storage_data_source_id: Optional[str] = None,
        storage_data_source_name: Optional[str] = None,
        spark=None,
        **kwargs
    ) -> AutoMLSummary:
        """
        训练时序预测模型

        Args:
            dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
            target_col: 目标列名（要预测的值）
            time_col: 时间列名
            horizon: 预测时间范围（预测未来多少个时间点）
            data_source_table: 数据源表名（三段式：catalog.schema.table_name），用于 notebook 生成和模型注册
            frequency: 时间频率（D=天, W=周, M=月, H=小时等）
            identity_col: 标识列（用于多时间序列预测），默认 None
            timeout_minutes: 超时时间（分钟），默认 60
            max_trials: 最大试验次数，默认 100
            metric: 评估指标，默认 "smape"
                - smape: Symmetric Mean Absolute Percentage Error（默认）
                - mse: Mean Squared Error
                - rmse: Root Mean Squared Error
                - mae: Mean Absolute Error
                - mdape: Median Absolute Percentage Error
            exclude_cols: 排除的列，默认 None
            exclude_frameworks: 排除的框架，默认 None（已弃用，请使用 estimator_list）
                - prophet: Prophet
                - arima: ARIMA
                - deepar: Deep-AR
            estimator_list: 估计器列表，默认 None（使用所有可用估计器）
                可选值: 根据时序预测任务的可用估计器
                例如: ["prophet", "arima"] 只使用 Prophet 和 ARIMA
            sample_weight_col: 样本权重列，默认 None（仅多时序预测使用）
                - 指定每个时序的相对重要性
                - 权重必须是非负值（0 到 10,000 之间）
                - 同一时序的所有行必须具有相同的权重
            data_split_col: 数据划分列，默认 None
            experiment_name: MLflow 实验名称，默认 None
            experiment_id: MLflow 实验 ID，默认 None
            run_name: MLflow run 名称，默认 None
            register_model: 是否注册模型，默认 True
            model_name: 模型名称，默认 None
            max_concurrent_trials: 最大并发试验数，默认 1，最大 100
            custom_hp: 自定义超参数搜索空间，默认 None
                格式: {estimator_name: {param_name: search_space}}
                例如: {"prophet": {"changepoint_prior_scale": {"domain": (0.001, 0.5), "init_value": 0.05}}}
            project_id: 项目 ID，用于多租户隔离，默认 None
                - 优先使用传入的 project_id 参数
                - 如果未传入，则从环境变量 WEDATA_PROJECT_ID 读取
                - 如果都未配置，则抛出 ValueError 异常
            country_code: 节假日国家代码，默认 "US"（仅 Prophet 使用）
                - 双字母国家/地区代码
                - 设置为空字符串 "" 可忽略节假日
                - 示例: "US"（美国）, "CN"（中国）, "JP"（日本）
            feature_store_lookups: 特征存储查找配置，默认 None
                - 格式: [{"table_name": str, "lookup_key": str/list, "timestamp_lookup_key": str}]
                - 用于从特征存储中查找协变量数据
            prediction_result_storage: 预测结果存储路径，默认 None
                - DLC 两段式路径，如 "/DataLake/data/"
                - 如果提供，训练完成后会自动执行预测并保存到 DLC 表
                - 表名格式: {database}.{table_path}_{run_id}_{timestamp}
            storage_data_source_id: 存储数据源 ID，默认 None
            storage_data_source_name: 存储数据源名称，默认 None
            spark: Spark session，默认 None
            **kwargs: 其他参数

        Returns:
            AutoMLSummary 对象

        Raises:
            ValueError: 如果 project_id 未配置（既未传入参数，也未设置环境变量）

        Note:
            Forecast 任务不支持生成 notebook。预测结果通过 prediction_result_storage 参数
            直接保存到 DLC 表中。

        Example:
            >>> forecast = Forecast()
            >>> summary = forecast.fit(
            ...     dataset=spark.table("demo.sales_data"),
            ...     target_col="sales",
            ...     time_col="date",
            ...     horizon=30,
            ...     frequency="D",
            ...     timeout_minutes=10,
            ...     max_trials=100,
            ...     metric="smape",
            ...     exclude_frameworks=["deepar"],
            ...     experiment_name="sales_forecasting",
            ...     register_model=True,
            ...     model_name="sales_forecast_model"
            ... )
            >>> print(summary)

            # 使用自定义搜索空间
            >>> custom_search_space = {
            ...     "prophet": {
            ...         "changepoint_prior_scale": {"domain": (0.001, 0.5), "init_value": 0.05},
            ...         "seasonality_prior_scale": {"domain": (0.01, 10), "init_value": 1.0}
            ...     }
            ... }
            >>> summary = forecast.fit(
            ...     dataset=df,
            ...     target_col="sales",
            ...     time_col="date",
            ...     horizon=30,
            ...     custom_hp=custom_search_space
            ... )
        """
        logger.info(f"Starting forecast task with target_col={target_col}, time_col={time_col}, horizon={horizon}")
        
        # 验证参数
        if max_concurrent_trials < 1 or max_concurrent_trials > 100:
            raise ValueError("max_concurrent_trials must be between 1 and 100")
        
        # 验证评估指标
        valid_metrics = ["smape", "mse", "rmse", "mae", "mdape"]
        if metric not in valid_metrics:
            raise ValueError(f"metric must be one of {valid_metrics}, got {metric}")
        
        # 创建 FLAMLTrainer
        trainer = FLAMLTrainer(
            task="forecast",
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
            run_name=run_name or "forecast",
            register_model=register_model,
            model_name=model_name,
            max_concurrent_trials=max_concurrent_trials,
            custom_hp=custom_hp,
            project_id=project_id,
            country_code=country_code,
            feature_store_lookups=feature_store_lookups,
            # 时序预测特有参数
            time_col=time_col,
            horizon=horizon,
            frequency=frequency,
            identity_col=identity_col,
            # 预测结果存储参数
            prediction_result_storage=prediction_result_storage,
            storage_data_source_id=storage_data_source_id,
            storage_data_source_name=storage_data_source_name,
            **kwargs
        )

        # 训练
        summary = trainer.train(dataset, data_source_table=data_source_table, spark=spark)

        logger.info(f"Forecast task completed. Best estimator: {summary.best_estimator}")

        return summary

