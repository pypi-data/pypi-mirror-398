"""
任务类模块

对齐 Databricks AutoML 的任务类
"""
from .base import BaseAutoML, SupervisedLearner
from .classifier import Classifier
from .regressor import Regressor
from .forecast import Forecast

__all__ = [
    "BaseAutoML",
    "SupervisedLearner",
    "Classifier",
    "Regressor",
    "Forecast",
]

