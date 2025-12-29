"""
分类任务类

对齐 Databricks AutoML 的 Classifier 类
"""
from typing import Any, List, Optional, Union
import pandas as pd
import logging

from wedata_automl.summary import AutoMLSummary
from wedata_automl.tasks.base import SupervisedLearner
from wedata_automl.engines.flaml_trainer import FLAMLTrainer
from wedata_automl.params import ConfigParam

logger = logging.getLogger(__name__)


class Classifier(SupervisedLearner):
    """
    分类任务类
    
    对齐 Databricks AutoML 的 Classifier 类
    
    Example:
        >>> from wedata_automl.tasks import Classifier
        >>> classifier = Classifier()
        >>> summary = classifier.fit(
        ...     dataset=spark.table("demo.wine_quality"),
        ...     target_col="quality",
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
        训练分类模型

        Args:
            dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
            target_col: 目标列名
            data_source_table: 数据源表名（三段式：catalog.schema.table_name），用于 notebook 生成和模型注册
            timeout_minutes: 超时时间（分钟），默认 5
            max_trials: 最大试验次数，默认 None（无限制）
            metric: 评估指标，用于选择最佳模型，默认 "auto"（使用 log_loss）
                常用指标:
                    - 'log_loss': 对数损失（默认，推荐用于多分类）
                    - 'accuracy': 准确率（适合类别平衡的数据）
                    - 'f1': F1 分数（二分类）
                    - 'macro_f1': Macro-averaged F1（多分类，类别不平衡）
                    - 'micro_f1': Micro-averaged F1（多分类）
                    - 'roc_auc': ROC AUC（二分类）
                    - 'roc_auc_ovr': One-vs-Rest ROC AUC（多分类）
                    - 'precision': 精确率
                    - 'recall': 召回率
                    - 'auto': 自动选择（使用 log_loss）
                注意: FLAML 会根据此指标选择最佳模型
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
            max_concurrent_trials: 并发 trials 数量，默认 1（顺序执行）
                - 设置 > 1 时，FLAML 会并行执行多个 trials
                - 本地模式：使用多线程并行
                - Spark 模式：使用 Spark 分布式并行（需要设置 use_spark=True）
                - 注意：并发会增加内存和 CPU 使用
            use_spark: 是否使用 Spark 作为并行后端，默认 False
                - True: 使用 Spark 分布式执行 trials（需要 Spark 集群）
                - False: 使用本地多线程并行
                - 注意：Spark 模式不支持 GPU 训练
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
            >>> classifier = Classifier()
            >>> summary = classifier.fit(
            ...     dataset=spark.table("demo.wine_quality"),
            ...     target_col="quality",
            ...     timeout_minutes=5,
            ...     max_trials=100,
            ...     metric="accuracy",
            ...     exclude_cols=["id", "timestamp"],
            ...     experiment_name="wine_quality_classification",
            ...     register_model=True,
            ...     model_name="wine_quality_model"
            ... )
            >>> print(summary)

            # 使用自定义搜索空间
            >>> custom_search_space = {
            ...     "lgbm": {
            ...         "n_estimators": {"domain": range(100, 500), "init_value": 100},
            ...         "learning_rate": {"domain": (0.01, 0.3), "init_value": 0.1}
            ...     }
            ... }
            >>> summary = classifier.fit(
            ...     dataset=df,
            ...     target_col="quality",
            ...     custom_hp=custom_search_space
            ... )
        """
        logger.info(f"Starting classification task with target_col={target_col}")

        # 验证参数
        if max_concurrent_trials < 1 or max_concurrent_trials > 100:
            raise ValueError("max_concurrent_trials must be between 1 and 100")

        # 验证评估指标
        valid_metrics = ["f1", "log_loss", "precision", "accuracy", "roc_auc", "rmse", "mae", "auto"]
        if metric not in valid_metrics:
            raise ValueError(f"metric must be one of {valid_metrics}, got {metric}")

        # 创建 FLAMLTrainer
        trainer = FLAMLTrainer(
            task="classification",
            target_col=target_col,
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
            run_name=run_name or "classification",
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
        logger.info(f"Classification task completed. Best estimator: {summary.best_estimator}")
        
        return summary

