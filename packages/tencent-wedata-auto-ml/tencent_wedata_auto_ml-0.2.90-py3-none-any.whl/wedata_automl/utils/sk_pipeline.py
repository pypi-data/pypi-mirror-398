import pandas as pd
from typing import Dict, Any, Optional, Union, List
from sklearn.pipeline import Pipeline as SkPipe
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.impute import SimpleImputer


# 支持的填充策略映射
IMPUTER_STRATEGY_MAP = {
    "auto": "median",           # 自动选择 -> 使用 median
    "mean": "mean",             # 均值填充
    "median": "median",         # 中位数填充
    "most_frequent": "most_frequent",  # 众数填充
    "constant": "constant",     # 常量填充
}


def _to_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({c: pd.to_numeric(df[c], errors="coerce") for c in df.columns})


def _parse_imputer_config(
    imputer_config: Union[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    解析 imputer 配置

    Args:
        imputer_config: 可以是字符串（如 "mean", "median", "auto"）
                       或字典（如 {"strategy": "constant", "fill_value": 0}）

    Returns:
        SimpleImputer 的参数字典
    """
    if isinstance(imputer_config, str):
        strategy = IMPUTER_STRATEGY_MAP.get(imputer_config.lower(), "median")
        return {"strategy": strategy}
    elif isinstance(imputer_config, dict):
        strategy = imputer_config.get("strategy", "median")
        strategy = IMPUTER_STRATEGY_MAP.get(strategy.lower(), strategy)
        result = {"strategy": strategy}
        if strategy == "constant" and "fill_value" in imputer_config:
            result["fill_value"] = imputer_config["fill_value"]
        return result
    else:
        return {"strategy": "median"}


def build_numeric_preprocessor(
    feature_cols: List[str],
    imputers: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
    default_imputer: str = "auto"
):
    """
    构建数值特征预处理器

    Args:
        feature_cols: 特征列名列表
        imputers: 列级别的缺失值填充策略，格式：
            {
                "column_name": "mean",  # 字符串策略
                "column_name2": {"strategy": "constant", "fill_value": 0},  # 字典策略
            }
            支持的策略:
            - "auto": 自动选择（默认使用 median）
            - "mean": 均值填充
            - "median": 中位数填充
            - "most_frequent": 众数填充
            - {"strategy": "constant", "fill_value": <value>}: 常量填充
        default_imputer: 默认填充策略，默认 "auto"

    Returns:
        ColumnTransformer 预处理器
    """
    imputers = imputers or {}

    # 如果所有列使用相同的 imputer 策略，使用简化的 pipeline
    # 否则为每列创建单独的 transformer
    unique_strategies = set()
    for col in feature_cols:
        if col in imputers:
            config = _parse_imputer_config(imputers[col])
            unique_strategies.add(str(config))
        else:
            config = _parse_imputer_config(default_imputer)
            unique_strategies.add(str(config))

    # 如果只有一种策略，使用简化的 pipeline
    if len(unique_strategies) == 1:
        # 获取默认策略配置
        default_config = _parse_imputer_config(
            imputers.get(feature_cols[0], default_imputer) if feature_cols else default_imputer
        )
        num_pipe = SkPipe(steps=[
            ("to_numeric", FunctionTransformer(_to_numeric_df, feature_names_out="one-to-one")),
            ("impute", SimpleImputer(**default_config)),
            ("scale", StandardScaler()),
        ])
        return ColumnTransformer(
            transformers=[("num", num_pipe, feature_cols)],
            remainder="drop",
            sparse_threshold=0,
            verbose_feature_names_out=False,
        )

    # 多种策略：为每列创建单独的 transformer
    transformers = []
    for i, col in enumerate(feature_cols):
        if col in imputers:
            config = _parse_imputer_config(imputers[col])
        else:
            config = _parse_imputer_config(default_imputer)

        col_pipe = SkPipe(steps=[
            ("to_numeric", FunctionTransformer(
                lambda df, c=col: pd.DataFrame({c: pd.to_numeric(df[c], errors="coerce")}),
                feature_names_out="one-to-one"
            )),
            ("impute", SimpleImputer(**config)),
            ("scale", StandardScaler()),
        ])
        transformers.append((f"col_{i}_{col}", col_pipe, [col]))

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        sparse_threshold=0,
        verbose_feature_names_out=False,
    )

