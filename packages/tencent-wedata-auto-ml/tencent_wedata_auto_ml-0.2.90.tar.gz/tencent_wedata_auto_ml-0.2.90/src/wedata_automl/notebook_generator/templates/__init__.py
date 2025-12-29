"""
Notebook Templates

为不同任务类型提供 Notebook 模板
"""
from wedata_automl.notebook_generator.templates.base import BaseNotebookTemplate
from wedata_automl.notebook_generator.templates.classification import ClassificationNotebookTemplate
from wedata_automl.notebook_generator.templates.regression import RegressionNotebookTemplate
from wedata_automl.notebook_generator.templates.forecast import ForecastNotebookTemplate

__all__ = [
    "BaseNotebookTemplate",
    "ClassificationNotebookTemplate",
    "RegressionNotebookTemplate",
    "ForecastNotebookTemplate",
]

