__version__ = "0.2.90"

# 必须在 import mlflow 之前设置环境变量
import os

# 禁用 MLflow 2.15+ 的 LoggedModel 功能（避免与旧版 MLflow 服务器不兼容）
os.environ.setdefault("MLFLOW_ENABLE_LOGGED_MODELS", "false")

# 修复 MLFLOW_TRACKING_URI 缺少协议前缀的问题
# 某些环境（如 DLC）可能设置的是 "10.0.3.42:5000" 而不是 "http://10.0.3.42:5000"
_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "")
if _tracking_uri and not _tracking_uri.startswith(("http://", "https://", "file://", "databricks", "postgresql", "mysql", "sqlite", "mssql")):
    _fixed_uri = f"http://{_tracking_uri}"
    os.environ["MLFLOW_TRACKING_URI"] = _fixed_uri
    print(f"✅ Fixed MLFLOW_TRACKING_URI: {_tracking_uri} → {_fixed_uri}")

# 导入便捷函数（对齐 Databricks）
from .api import classify, regress, forecast

# 导入任务类（对齐 Databricks）
from .tasks import Classifier, Regressor, Forecast

# 导入 AutoMLSummary
from .summary import AutoMLSummary

# 导入 Driver（通用驱动程序）
from .driver import AutoMLDriver, run_automl

__all__ = [
    # 便捷函数
    "classify",
    "regress",
    "forecast",
    # 任务类
    "Classifier",
    "Regressor",
    "Forecast",
    # 返回对象
    "AutoMLSummary",
    # 驱动程序
    "AutoMLDriver",
    "run_automl",
]

