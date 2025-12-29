"""
便捷函数 API

对齐 Databricks AutoML 的便捷函数
"""
from typing import Any, List, Optional, Union
import pandas as pd

from wedata_automl.summary import AutoMLSummary
from wedata_automl.tasks import Classifier, Regressor, Forecast


def classify(
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
    pos_label: Optional[Union[str, int]] = None,
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
    分类任务便捷函数

    对齐 Databricks AutoML 的 classify() 函数

    Args:
        dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
        target_col: 目标列名
        data_source_table: 数据源表名（三段式：catalog.schema.table_name），用于 notebook 生成和模型注册
        timeout_minutes: 超时时间（分钟），默认 5
        max_trials: 最大试验次数，默认 None（无限制）
        metric: 评估指标，默认 "auto"（自动选择 accuracy）
            - f1: F1 Score
            - log_loss: Log Loss（默认）
            - precision: Precision
            - accuracy: Accuracy
            - roc_auc: ROC AUC
            - rmse: Root Mean Squared Error
            - mae: Mean Absolute Error
            - auto: 自动选择
        exclude_cols: 排除的列，默认 None
        exclude_frameworks: 排除的框架，默认 None（已弃用，请使用 estimator_list）
            - sklearn: Scikit-learn 算法
            - xgboost: XGBoost
            - lightgbm: LightGBM
            默认全选（sklearn, xgboost, lightgbm）
        estimator_list: 估计器列表，默认 None（使用所有可用估计器）
            可选值: ["lgbm", "xgboost", "rf", "extra_tree", "lrl1"]
            例如: ["lgbm", "xgboost"] 只使用 LightGBM 和 XGBoost
            注意: lrl1 仅适用于分类任务
        sample_weight_col: 样本权重列，默认 None
        pos_label: 正类标签（二分类），默认 None
        data_split_col: 数据划分列，默认 None
        experiment_name: MLflow 实验名称，默认 None
        experiment_id: MLflow 实验 ID，默认 None
        run_name: MLflow run 名称，默认 None
        register_model: 是否注册模型，默认 True
        model_name: 模型名称，默认 None
        max_concurrent_trials: 最大并发试验数，默认 1，最大 100
        custom_hp: 自定义超参数搜索空间，默认 None
        project_id: 项目 ID，用于多租户隔离，默认 None
            - 优先使用传入的 project_id 参数
            - 如果未传入，则从环境变量 WEDATA_PROJECT_ID 读取
            - 如果都未配置，则抛出 ValueError 异常
        imputers: 缺失值填充策略字典，默认 None
            - 格式: {列名: 填充策略}
            - 填充策略可以是字符串: "auto", "mean", "median", "most_frequent"
            - 或字典: {"strategy": "constant", "fill_value": <value>}
            - 示例: {"age": "mean", "income": "median"}
        spark: Spark session，默认 None
        **kwargs: 其他参数

    Returns:
        AutoMLSummary 对象

    Raises:
        ValueError: 如果 project_id 未配置（既未传入参数，也未设置环境变量）

    Example:
        >>> from wedata_automl import classify
        >>> summary = classify(
        ...     dataset=spark.table("demo.wine_quality"),
        ...     target_col="quality",
        ...     timeout_minutes=5,
        ...     max_trials=100,
        ...     metric="accuracy",
        ...     experiment_name="wine_quality_classification",
        ...     register_model=True,
        ...     model_name="wine_quality_model"
        ... )
        >>> print(summary)
    """
    classifier = Classifier()
    return classifier.fit(
        dataset=dataset,
        target_col=target_col,
        data_source_table=data_source_table,
        timeout_minutes=timeout_minutes,
        max_trials=max_trials,
        metric=metric,
        exclude_cols=exclude_cols,
        exclude_frameworks=exclude_frameworks,
        estimator_list=estimator_list,
        sample_weight_col=sample_weight_col,
        pos_label=pos_label,
        data_split_col=data_split_col,
        experiment_name=experiment_name,
        experiment_id=experiment_id,
        run_name=run_name,
        register_model=register_model,
        model_name=model_name,
        max_concurrent_trials=max_concurrent_trials,
        use_spark=use_spark,
        custom_hp=custom_hp,
        project_id=project_id,
        imputers=imputers,
        spark=spark,
        **kwargs
    )


def regress(
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
    回归任务便捷函数

    对齐 Databricks AutoML 的 regress() 函数

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
        project_id: 项目 ID，用于多租户隔离，默认 None
            - 优先使用传入的 project_id 参数
            - 如果未传入，则从环境变量 WEDATA_PROJECT_ID 读取
            - 如果都未配置，则抛出 ValueError 异常
        imputers: 缺失值填充策略字典，默认 None
            - 格式: {列名: 填充策略}
            - 填充策略可以是字符串: "auto", "mean", "median", "most_frequent"
            - 或字典: {"strategy": "constant", "fill_value": <value>}
            - 示例: {"age": "mean", "income": "median"}
        spark: Spark session，默认 None
        **kwargs: 其他参数

    Returns:
        AutoMLSummary 对象

    Raises:
        ValueError: 如果 project_id 未配置（既未传入参数，也未设置环境变量）

    Example:
        >>> from wedata_automl import regress
        >>> summary = regress(
        ...     dataset=spark.table("demo.house_prices"),
        ...     target_col="price",
        ...     timeout_minutes=5,
        ...     max_trials=100,
        ...     metric="r2",
        ...     experiment_name="house_price_regression",
        ...     register_model=True,
        ...     model_name="house_price_model"
        ... )
        >>> print(summary)
    """
    regressor = Regressor()
    return regressor.fit(
        dataset=dataset,
        target_col=target_col,
        data_source_table=data_source_table,
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
        run_name=run_name,
        register_model=register_model,
        model_name=model_name,
        max_concurrent_trials=max_concurrent_trials,
        use_spark=use_spark,
        custom_hp=custom_hp,
        project_id=project_id,
        imputers=imputers,
        spark=spark,
        **kwargs
    )


def forecast(
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
    spark=None,
    **kwargs
) -> AutoMLSummary:
    """
    时序预测任务便捷函数

    对齐 Databricks AutoML 的 forecast() 函数

    Args:
        dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
        target_col: 目标列名（要预测的值）
        time_col: 时间列名
        horizon: 预测时间范围（预测未来多少个时间点）
        data_source_table: 数据源表名（三段式：catalog.schema.table_name），用于 notebook 生成和模型注册
        frequency: 时间频率（D=天, W=周, M=月, H=小时等），默认 "D"
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
        data_split_col: 数据划分列，默认 None
        experiment_name: MLflow 实验名称，默认 None
        experiment_id: MLflow 实验 ID，默认 None
        run_name: MLflow run 名称，默认 None
        register_model: 是否注册模型，默认 True
        model_name: 模型名称，默认 None
        max_concurrent_trials: 最大并发试验数，默认 1，最大 100
        custom_hp: 自定义超参数搜索空间，默认 None
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
        spark: Spark session，默认 None
        **kwargs: 其他参数

    Returns:
        AutoMLSummary 对象

    Raises:
        ValueError: 如果 project_id 未配置（既未传入参数，也未设置环境变量）

    Example:
        >>> from wedata_automl import forecast
        >>> summary = forecast(
        ...     dataset=spark.table("demo.sales_data"),
        ...     target_col="sales",
        ...     time_col="date",
        ...     horizon=30,
        ...     frequency="D",
        ...     timeout_minutes=10,
        ...     max_trials=100,
        ...     metric="smape",
        ...     experiment_name="sales_forecasting",
        ...     register_model=True,
        ...     model_name="sales_forecast_model"
        ... )
        >>> print(summary)
    """
    forecaster = Forecast()
    return forecaster.fit(
        dataset=dataset,
        target_col=target_col,
        time_col=time_col,
        horizon=horizon,
        data_source_table=data_source_table,
        frequency=frequency,
        identity_col=identity_col,
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
        run_name=run_name,
        register_model=register_model,
        model_name=model_name,
        max_concurrent_trials=max_concurrent_trials,
        custom_hp=custom_hp,
        project_id=project_id,
        country_code=country_code,
        feature_store_lookups=feature_store_lookups,
        spark=spark,
        **kwargs
    )

