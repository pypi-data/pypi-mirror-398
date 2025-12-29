"""
MLflow 2.21.x / 2.22.x 兼容性补丁

修复 MLflow 2.21.x 和 2.22.x 版本中的 generate_request_id 导入错误。

错误信息:
    ImportError: cannot import name 'generate_request_id' from 'mlflow.tracing.utils'

根本原因:
    mlflow.store.tracking.file_store 模块在导入时尝试从 mlflow.tracing.utils 导入
    generate_request_id，但由于循环依赖或模块初始化顺序问题导致导入失败。

解决方案:
    使用 import hook 在 mlflow.tracing.utils 模块加载时自动注入 generate_request_id 函数。

使用方法:
    这个补丁会在模块导入时自动应用，无需手动调用。

    ```python
    # 自动应用补丁
    import wedata_automl.utils.mlflow_patch

    import mlflow  # 现在可以安全导入
    ```
"""

import sys
import uuid
import logging
import importlib.abc
import importlib.machinery
import importlib.util

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """
    生成唯一的请求 ID。

    这是 MLflow 2.21.x+ 中 mlflow.tracing.utils.generate_request_id 的实现。
    """
    return uuid.uuid4().hex


class MLflowPatchFinder(importlib.abc.MetaPathFinder):
    """
    自定义 import hook，在 mlflow.tracing.utils 模块加载后自动注入 generate_request_id。
    """

    def find_module(self, fullname, path=None):
        if fullname == "mlflow.tracing.utils":
            return MLflowPatchLoader()
        return None


class MLflowPatchLoader(importlib.abc.Loader):
    """
    自定义 loader，在模块加载后注入 generate_request_id 函数。
    """

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        # 使用默认的导入机制加载模块
        spec = importlib.machinery.PathFinder.find_spec(fullname)
        if spec is None:
            raise ImportError(f"No module named '{fullname}'")

        module = importlib.util.module_from_spec(spec)
        sys.modules[fullname] = module

        try:
            spec.loader.exec_module(module)
        except Exception:
            # 如果加载失败，尝试注入 generate_request_id
            pass

        # 注入 generate_request_id（如果不存在）
        if not hasattr(module, "generate_request_id"):
            module.generate_request_id = generate_request_id
            logger.info("✅ 成功注入 generate_request_id 到 mlflow.tracing.utils")

        return module


def apply_mlflow_patch():
    """
    应用 MLflow 兼容性补丁，修复 generate_request_id 导入错误。

    这个函数会注册一个 import hook，在 mlflow.tracing.utils 模块加载时自动注入
    generate_request_id 函数。
    """
    # 检查是否已经注册了 hook
    for finder in sys.meta_path:
        if isinstance(finder, MLflowPatchFinder):
            logger.debug("MLflow 补丁已经注册，跳过。")
            return

    # 注册 import hook
    sys.meta_path.insert(0, MLflowPatchFinder())
    logger.info("✅ 成功注册 MLflow 兼容性补丁")

    # 如果 mlflow.tracing.utils 已经被导入，直接修补
    if "mlflow.tracing.utils" in sys.modules:
        tracing_utils = sys.modules["mlflow.tracing.utils"]
        if not hasattr(tracing_utils, "generate_request_id"):
            tracing_utils.generate_request_id = generate_request_id
            logger.info("✅ 成功修补已导入的 mlflow.tracing.utils 模块")


def check_mlflow_compatibility():
    """
    检查 MLflow 版本兼容性，并在需要时应用补丁。

    Returns:
        bool: 如果 MLflow 兼容或补丁成功应用，返回 True；否则返回 False。
    """
    try:
        import mlflow
        from packaging.version import Version

        mlflow_version = Version(mlflow.__version__)

        # MLflow 2.21.x 和 2.22.x 需要补丁
        if Version("2.21.0") <= mlflow_version < Version("2.23.0"):
            logger.info(
                f"检测到 MLflow {mlflow.__version__}，可能需要兼容性补丁。"
            )

            # 尝试导入 generate_request_id
            try:
                from mlflow.tracing.utils import generate_request_id

                logger.info("✅ generate_request_id 可以正常导入，无需补丁。")
                return True
            except ImportError:
                logger.warning(
                    f"❌ MLflow {mlflow.__version__} 存在 generate_request_id 导入错误。"
                )
                logger.info("建议降级到 MLflow 2.16.2 或 2.17.2。")
                logger.info("或者在导入 mlflow 之前调用 apply_mlflow_patch()。")
                return False

        # 其他版本
        elif mlflow_version < Version("2.16.0"):
            logger.warning(
                f"MLflow {mlflow.__version__} 版本过低，推荐升级到 2.16.2 或更高版本。"
            )
            return True
        else:
            logger.debug(f"MLflow {mlflow.__version__} 版本兼容。")
            return True

    except ImportError:
        logger.error("MLflow 未安装。")
        return False
    except Exception as e:
        logger.error(f"检查 MLflow 兼容性时发生错误：{e}", exc_info=True)
        return False


# 自动应用补丁
try:
    apply_mlflow_patch()
except Exception as e:
    logger.warning(f"自动应用 MLflow 补丁失败：{e}")

