from typing import Optional, Tuple
import logging
from wedata_automl.utils.print_utils import safe_print

logger = logging.getLogger(__name__)


def get_or_create_spark():
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception as e:
        raise RuntimeError("Spark is not available in this environment.") from e


def read_table_to_pandas(table: str, spark=None):
    if spark is None:
        spark = get_or_create_spark()
    return spark.read.table(table).toPandas()


def compute_split_and_weights(
    y,
    task: str = "classification",
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    stratify: bool = True,
    random_state: int = 42,
) -> Tuple["pd.Series", "pd.Series"]:
    """Compute Databricks-style split marker and sample weights.

    Returns:
        split_col: pd.Series with values {0: train, 1: val, 2: test}
        sample_weights: pd.Series aligned to y
    """
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split

    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        total = train_ratio + val_ratio + test_ratio
        train_ratio, val_ratio, test_ratio = train_ratio / total, val_ratio / total, test_ratio / total
        safe_print(f"Ratios normalized: train={train_ratio:.2f}, val={val_ratio:.2f}, test={test_ratio:.2f}", level="INFO")

    n = len(y)
    idx = np.arange(n)
    can_stratify = False
    if task == "classification" and stratify:
        vc = pd.Series(y).value_counts()
        can_stratify = all(count >= 2 for count in vc.values)
        if can_stratify:
            safe_print("Stratified split enabled: all classes have >=2 samples", level="INFO")
        else:
            safe_print("Stratified split disabled: some classes have <2 samples, using random split", level="WARNING")

    # first split: train vs temp
    strat = y if can_stratify else None
    idx_train, idx_temp, y_train, y_temp = train_test_split(
        idx, y, test_size=(1.0 - train_ratio), random_state=random_state, stratify=strat
    )

    # second split: val vs test
    strat2 = y_temp if (can_stratify and len(np.unique(y_temp)) > 1) else None
    test_size = test_ratio / (val_ratio + test_ratio) if (val_ratio + test_ratio) > 0 else 0.5
    idx_val, idx_test = train_test_split(
        idx_temp, test_size=test_size, random_state=random_state, stratify=strat2
    )

    split_col = pd.Series(index=np.arange(n), dtype=int)
    split_col.loc[idx_train] = 0
    split_col.loc[idx_val] = 1
    split_col.loc[idx_test] = 2

    # sample weights
    if task == "classification":
        from sklearn.utils.class_weight import compute_sample_weight
        sample_weights = pd.Series(compute_sample_weight(class_weight="balanced", y=y))
    else:
        sample_weights = pd.Series(np.ones(n, dtype=float))

    return split_col, sample_weights

