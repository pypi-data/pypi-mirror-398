"""
基础任务类

对齐 Databricks AutoML 的基础类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from wedata_automl.summary import AutoMLSummary


class BaseAutoML(ABC):
    """
    AutoML 基础类
    
    对齐 Databricks AutoML 的基础类
    """
    
    def __init__(self, context_type: str = "wedata"):
        """
        初始化
        
        Args:
            context_type: 上下文类型 ("wedata", "databricks", "local")
        """
        self.context_type = context_type
    
    @abstractmethod
    def fit(
        self,
        dataset: Union[pd.DataFrame, Any],
        target_col: str,
        **kwargs
    ) -> AutoMLSummary:
        """
        训练模型
        
        Args:
            dataset: 数据集（Pandas DataFrame 或 Spark DataFrame 或表名）
            target_col: 目标列名
            **kwargs: 其他参数
            
        Returns:
            AutoMLSummary 对象
        """
        pass


class SupervisedLearner(BaseAutoML):
    """
    监督学习基础类
    
    对齐 Databricks AutoML 的 SupervisedLearner
    """
    
    def __init__(self, context_type: str = "wedata"):
        """
        初始化
        
        Args:
            context_type: 上下文类型
        """
        super().__init__(context_type)

