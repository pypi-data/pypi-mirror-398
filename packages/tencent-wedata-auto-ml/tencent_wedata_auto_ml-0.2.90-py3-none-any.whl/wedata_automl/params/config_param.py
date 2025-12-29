"""
ConfigParam Enum - 参数定义

对齐 Databricks AutoML 的参数管理系统
"""
from enum import Enum
from typing import Callable, Any, Optional, Tuple
from .converters import to_int, to_float, to_bool, split_by_comma, parse_json


class ConfigParam(Enum):
    """
    配置参数 Enum
    
    每个参数包含：
    - param_name: 内部参数名（Python API）
    - widget_name: Widget 名称（Databricks UI）
    - default_value: 默认值
    - type_converter: 类型转换函数
    
    对齐 Databricks AutoML 的 Param Enum
    """
    
    # 基础参数
    TARGET_COL = ("target_col", "targetCol", None, None)
    TIMEOUT_MINUTES = ("timeout_minutes", "timeoutMinutes", 5, to_int)
    MAX_TRIALS = ("max_trials", "maxTrials", 100, to_int)
    
    # 数据参数
    EXCLUDE_COLS = ("exclude_cols", "excludeCols", None, split_by_comma)
    EXCLUDE_FRAMEWORKS = ("exclude_frameworks", "excludeFrameworks", None, split_by_comma)
    SAMPLE_WEIGHT_COL = ("sample_weight_col", "sampleWeightCol", None, None)
    
    # 评估参数
    METRIC = ("metric", "metric", "auto", None)
    POS_LABEL = ("pos_label", "posLabel", None, None)
    
    # 数据划分参数
    DATA_SPLIT_COL = ("data_split_col", "dataSplitCol", None, None)
    TRAIN_VAL_SPLIT_COL = ("train_val_split_col", "trainValSplitCol", None, None)
    
    # 特征工程参数
    IMPUTERS = ("imputers", "imputers", None, parse_json)
    FEATURE_STORE_LOOKUPS = ("feature_store_lookups", "featureStoreLookups", None, parse_json)
    
    # MLflow 参数
    EXPERIMENT_NAME = ("experiment_name", "experimentName", None, None)
    EXPERIMENT_ID = ("experiment_id", "experimentId", None, None)
    RUN_NAME = ("run_name", "runName", None, None)
    
    # 模型注册参数
    REGISTER_MODEL = ("register_model", "registerModel", True, to_bool)
    MODEL_NAME = ("model_name", "modelName", None, None)

    # 时序预测参数
    TIME_COL = ("time_col", "timeCol", None, None)
    HORIZON = ("horizon", "horizon", None, to_int)
    FREQUENCY = ("frequency", "frequency", None, None)
    IDENTITY_COL = ("identity_col", "identityCol", None, split_by_comma)

    # 并发控制参数
    MAX_CONCURRENT_TRIALS = ("max_concurrent_trials", "maxConcurrentTrials", 1, to_int)
    
    # WeData 特有参数
    TABLE = ("table", "table", None, None)
    LABEL_COL = ("label_col", "labelCol", None, None)  # 向后兼容
    TIME_BUDGET = ("time_budget", "timeBudget", None, to_int)  # 向后兼容
    
    def __init__(
        self,
        param_name: str,
        widget_name: str,
        default_value: Any,
        type_converter: Optional[Callable[[Any], Any]] = None
    ):
        """
        初始化参数
        
        Args:
            param_name: 内部参数名
            widget_name: Widget 名称
            default_value: 默认值
            type_converter: 类型转换函数
        """
        self.param_name = param_name
        self.widget_name = widget_name
        self.default_value = default_value
        self.type_converter = type_converter or (lambda x: x)
    
    def convert(self, value: Any) -> Any:
        """
        转换参数值
        
        Args:
            value: 原始值
            
        Returns:
            转换后的值
        """
        if value is None or value == "":
            return self.default_value
        return self.type_converter(value)
    
    @classmethod
    def get_by_param_name(cls, param_name: str) -> Optional["ConfigParam"]:
        """
        根据参数名获取 ConfigParam
        
        Args:
            param_name: 参数名
            
        Returns:
            ConfigParam 或 None
        """
        for param in cls:
            if param.param_name == param_name:
                return param
        return None
    
    @classmethod
    def get_by_widget_name(cls, widget_name: str) -> Optional["ConfigParam"]:
        """
        根据 Widget 名称获取 ConfigParam
        
        Args:
            widget_name: Widget 名称
            
        Returns:
            ConfigParam 或 None
        """
        for param in cls:
            if param.widget_name == widget_name:
                return param
        return None
    
    @classmethod
    def normalize_params(cls, params: dict) -> dict:
        """
        标准化参数字典
        
        将 widget_name 映射到 param_name，并应用类型转换
        
        Args:
            params: 原始参数字典
            
        Returns:
            标准化后的参数字典
        """
        normalized = {}
        
        for key, value in params.items():
            # 尝试通过 param_name 查找
            param = cls.get_by_param_name(key)
            if param is None:
                # 尝试通过 widget_name 查找
                param = cls.get_by_widget_name(key)
            
            if param is not None:
                # 使用 param_name 作为键
                normalized[param.param_name] = param.convert(value)
            else:
                # 未知参数，直接保留
                normalized[key] = value
        
        # 添加默认值
        for param in cls:
            if param.param_name not in normalized and param.default_value is not None:
                normalized[param.param_name] = param.default_value
        
        return normalized

