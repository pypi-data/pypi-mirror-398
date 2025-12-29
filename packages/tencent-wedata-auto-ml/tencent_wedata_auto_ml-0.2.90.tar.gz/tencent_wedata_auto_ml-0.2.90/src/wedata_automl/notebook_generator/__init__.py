"""
WeData AutoML Notebook Generator

自动生成可复现的 Jupyter Notebook，类似于 Databricks AutoML
"""
from wedata_automl.notebook_generator.generator import NotebookGenerator
from wedata_automl.notebook_generator.templates import (
    ClassificationNotebookTemplate,
    RegressionNotebookTemplate,
    ForecastNotebookTemplate,
)

__all__ = [
    "NotebookGenerator",
    "ClassificationNotebookTemplate",
    "RegressionNotebookTemplate",
    "ForecastNotebookTemplate",
]

