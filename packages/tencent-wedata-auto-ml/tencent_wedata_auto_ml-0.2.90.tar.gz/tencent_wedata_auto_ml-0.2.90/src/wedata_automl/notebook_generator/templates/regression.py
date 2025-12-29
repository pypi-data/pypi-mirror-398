"""
Regression Notebook Template

回归任务的 Notebook 模板
"""
from typing import Dict, Any, List
from wedata_automl.notebook_generator.templates.base import BaseNotebookTemplate


class RegressionNotebookTemplate(BaseNotebookTemplate):
    """
    回归任务 Notebook 模板
    """

    # 估计器名称映射
    ESTIMATOR_MAP = {
        "lgbm": ("LGBMRegressor", "lightgbm"),
        "xgboost": ("XGBRegressor", "xgboost"),
        "xgb_limitdepth": ("XGBRegressor", "xgboost"),
        "rf": ("RandomForestRegressor", "sklearn.ensemble"),
        "extra_tree": ("ExtraTreesRegressor", "sklearn.ensemble"),
    }

    # 每个估计器支持的参数白名单
    ESTIMATOR_VALID_PARAMS = {
        "lgbm": {
            "n_estimators", "max_depth", "num_leaves", "learning_rate", "subsample",
            "colsample_bytree", "reg_alpha", "reg_lambda", "min_child_samples",
            "min_child_weight", "max_bin", "verbose", "n_jobs", "random_state",
            "log_max_bin", "min_data_in_leaf",
        },
        "xgboost": {
            "n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree",
            "colsample_bylevel", "reg_alpha", "reg_lambda", "min_child_weight", "gamma",
            "max_leaves", "grow_policy", "tree_method", "n_jobs", "random_state", "verbosity",
        },
        "xgb_limitdepth": {
            "n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree",
            "colsample_bylevel", "reg_alpha", "reg_lambda", "min_child_weight", "gamma",
            "max_leaves", "grow_policy", "tree_method", "n_jobs", "random_state", "verbosity",
        },
        "rf": {
            "n_estimators", "max_depth", "min_samples_split", "min_samples_leaf",
            "max_features", "bootstrap", "oob_score", "n_jobs", "random_state",
            "criterion", "max_leaf_nodes", "min_weight_fraction_leaf",
            "min_impurity_decrease", "ccp_alpha", "max_samples",
        },
        "extra_tree": {
            "n_estimators", "max_depth", "min_samples_split", "min_samples_leaf",
            "max_features", "bootstrap", "oob_score", "n_jobs", "random_state",
            "criterion", "max_leaf_nodes", "min_weight_fraction_leaf",
            "min_impurity_decrease", "ccp_alpha", "max_samples",
        },
    }
    
    def _create_preprocessing_cells(self) -> List[Dict[str, Any]]:
        """创建预处理 Cells"""
        cells = []
        
        # 数据分割说明
        cells.append(self._create_markdown_cell([
            "## Train-Validation-Test Split\n",
            "\n",
            "The data is split into:\n",
            "- **Train** (60%): Used to train the model\n",
            "- **Validation** (20%): Used to tune hyperparameters\n",
            "- **Test** (20%): Used to evaluate final performance\n",
        ]))
        
        # 数据分割代码
        cells.append(self._create_code_cell([
            "from sklearn.model_selection import train_test_split\n",
            "\n",
            f"# Separate features and target\n",
            f"X = df[{self.features}]\n",
            f"y = df['{self.target_col}']\n",
            "\n",
            "# Split into train+val and test\n",
            "X_trainval, X_test, y_trainval, y_test = train_test_split(\n",
            "    X, y, test_size=0.2, random_state=42\n",
            ")\n",
            "\n",
            "# Split train+val into train and val\n",
            "X_train, X_val, y_train, y_val = train_test_split(\n",
            "    X_trainval, y_trainval, test_size=0.25, random_state=42\n",
            ")\n",
            "\n",
            "print(f'Train size: {len(X_train)}')\n",
            "print(f'Validation size: {len(X_val)}')\n",
            "print(f'Test size: {len(X_test)}')\n",
        ]))
        
        # 预处理 Pipeline
        cells.append(self._create_markdown_cell([
            "## Preprocessing Pipeline\n",
            "\n",
            "Create an intelligent preprocessing pipeline that automatically detects and handles multiple data types:\n",
            "\n",
            "| Feature Type | Detection | Preprocessing |\n",
            "|--------------|-----------|---------------|\n",
            "| **Numerical** | int, float, nullable Int/Float | Impute with median, StandardScaler |\n",
            "| **Binary** | Only 2 unique values | Impute with most frequent, map to 0/1 |\n",
            "| **Low-cardinality Categorical** | ≤50 unique values | Impute with most frequent, OneHotEncoder |\n",
            "| **High-cardinality Categorical** | >50 unique values | Impute with most frequent, OrdinalEncoder |\n",
            "| **Text** | Avg length >50 chars | TfidfVectorizer (max 100 features) |\n",
            "| **Datetime** | datetime64 types | Extract year, month, day, hour, dayofweek |\n",
        ]))

        cells.append(self._create_code_cell([
            "from sklearn.compose import ColumnTransformer\n",
            "from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder, LabelEncoder\n",
            "from sklearn.feature_extraction.text import TfidfVectorizer\n",
            "from sklearn.impute import SimpleImputer\n",
            "from sklearn.base import BaseEstimator, TransformerMixin\n",
            "import numpy as np\n",
            "import re\n",
            "\n",
            "# ============== Custom Transformers ==============\n",
            "\n",
            "class DatetimeFeatureExtractor(BaseEstimator, TransformerMixin):\n",
            '    """Extract temporal features from datetime columns."""\n',
            "    def fit(self, X, y=None):\n",
            "        return self\n",
            "    \n",
            "    def transform(self, X):\n",
            "        result = []\n",
            "        for col in X.columns:\n",
            "            dt_col = pd.to_datetime(X[col], errors='coerce')\n",
            "            result.append(dt_col.dt.year.fillna(0).values.reshape(-1, 1))\n",
            "            result.append(dt_col.dt.month.fillna(0).values.reshape(-1, 1))\n",
            "            result.append(dt_col.dt.day.fillna(0).values.reshape(-1, 1))\n",
            "            result.append(dt_col.dt.hour.fillna(0).values.reshape(-1, 1))\n",
            "            result.append(dt_col.dt.dayofweek.fillna(0).values.reshape(-1, 1))\n",
            "        return np.hstack(result) if result else np.array([]).reshape(len(X), 0)\n",
            "\n",
            "\n",
            "class BinaryEncoder(BaseEstimator, TransformerMixin):\n",
            '    """Encode binary features to 0/1."""\n',
            "    def __init__(self):\n",
            "        self.mappings_ = {}\n",
            "    \n",
            "    def fit(self, X, y=None):\n",
            "        # Works with DataFrame (set_config ensures pandas output)\n",
            "        X_df = pd.DataFrame(X) if not hasattr(X, 'columns') else X\n",
            "        for col in X_df.columns:\n",
            "            unique_vals = X_df[col].dropna().unique()\n",
            "            if len(unique_vals) == 2:\n",
            "                self.mappings_[col] = {unique_vals[0]: 0, unique_vals[1]: 1}\n",
            "            elif len(unique_vals) == 1:\n",
            "                self.mappings_[col] = {unique_vals[0]: 0}\n",
            "            else:\n",
            "                self.mappings_[col] = {v: i for i, v in enumerate(unique_vals)}\n",
            "        return self\n",
            "    \n",
            "    def transform(self, X):\n",
            "        X_df = pd.DataFrame(X) if not hasattr(X, 'columns') else X.copy()\n",
            "        for col in X_df.columns:\n",
            "            if col in self.mappings_:\n",
            "                X_df[col] = X_df[col].map(self.mappings_[col]).fillna(0)\n",
            "        return X_df.values\n",
            "\n",
            "\n",
            "class TextColumnVectorizer(BaseEstimator, TransformerMixin):\n",
            '    """Vectorize text columns using TF-IDF."""\n',
            "    def __init__(self, max_features=100):\n",
            "        self.max_features = max_features\n",
            "        self.vectorizers_ = {}\n",
            "    \n",
            "    def fit(self, X, y=None):\n",
            "        for col in X.columns:\n",
            "            vectorizer = TfidfVectorizer(\n",
            "                max_features=self.max_features,\n",
            "                stop_words='english',\n",
            "                lowercase=True,\n",
            "                token_pattern=r'(?u)\\\\b\\\\w+\\\\b'\n",
            "            )\n",
            "            text_data = X[col].fillna('').astype(str)\n",
            "            vectorizer.fit(text_data)\n",
            "            self.vectorizers_[col] = vectorizer\n",
            "        return self\n",
            "    \n",
            "    def transform(self, X):\n",
            "        result = []\n",
            "        for col in X.columns:\n",
            "            if col in self.vectorizers_:\n",
            "                text_data = X[col].fillna('').astype(str)\n",
            "                tfidf_matrix = self.vectorizers_[col].transform(text_data)\n",
            "                result.append(tfidf_matrix.toarray())\n",
            "        return np.hstack(result) if result else np.array([]).reshape(len(X), 0)\n",
            "\n",
        ]))

        # 第二个代码单元格：特征类型检测
        cells.append(self._create_code_cell([
            "# ============== Feature Type Detection ==============\n",
            "\n",
            f"# All features used in training\n",
            f"all_features = {self.features}\n",
            "\n",
            "# Configuration\n",
            "HIGH_CARDINALITY_THRESHOLD = 50  # Use OrdinalEncoder if unique values > threshold\n",
            "TEXT_AVG_LENGTH_THRESHOLD = 50   # Treat as text if avg string length > threshold\n",
            "\n",
            "# Initialize feature lists\n",
            "numerical_features = []\n",
            "binary_features = []\n",
            "low_cardinality_cat_features = []\n",
            "high_cardinality_cat_features = []\n",
            "text_features = []\n",
            "datetime_features = []\n",
            "\n",
            "# Analyze each feature\n",
            "for col in all_features:\n",
            "    dtype = X_train[col].dtype\n",
            "    n_unique = X_train[col].nunique()\n",
            "    \n",
            "    # Check for datetime\n",
            "    if pd.api.types.is_datetime64_any_dtype(dtype):\n",
            "        datetime_features.append(col)\n",
            "        continue\n",
            "    \n",
            "    # Check for numerical (including pandas nullable types)\n",
            "    if pd.api.types.is_numeric_dtype(dtype):\n",
            "        # Binary numerical (e.g., 0/1 flags)\n",
            "        if n_unique <= 2:\n",
            "            binary_features.append(col)\n",
            "        else:\n",
            "            numerical_features.append(col)\n",
            "        continue\n",
            "    \n",
            "    # Check for boolean\n",
            "    if pd.api.types.is_bool_dtype(dtype):\n",
            "        binary_features.append(col)\n",
            "        continue\n",
            "    \n",
            "    # String/Object/Category types - need further analysis\n",
            "    if dtype == 'object' or pd.api.types.is_categorical_dtype(dtype):\n",
            "        # Calculate average string length for text detection\n",
            "        sample = X_train[col].dropna().astype(str)\n",
            "        avg_length = sample.str.len().mean() if len(sample) > 0 else 0\n",
            "        \n",
            "        # Text feature: long strings\n",
            "        if avg_length > TEXT_AVG_LENGTH_THRESHOLD:\n",
            "            text_features.append(col)\n",
            "        # Binary categorical\n",
            "        elif n_unique <= 2:\n",
            "            binary_features.append(col)\n",
            "        # Low cardinality categorical: use OneHotEncoder\n",
            "        elif n_unique <= HIGH_CARDINALITY_THRESHOLD:\n",
            "            low_cardinality_cat_features.append(col)\n",
            "        # High cardinality categorical: use OrdinalEncoder\n",
            "        else:\n",
            "            high_cardinality_cat_features.append(col)\n",
            "        continue\n",
            "    \n",
            "    # Unknown types: try to convert to string and treat as categorical\n",
            "    print(f'Unknown dtype for {col}: {dtype}, converting to string')\n",
            "    X_train[col] = X_train[col].astype(str)\n",
            "    X_val[col] = X_val[col].astype(str)\n",
            "    X_test[col] = X_test[col].astype(str)\n",
            "    if X_train[col].nunique() <= HIGH_CARDINALITY_THRESHOLD:\n",
            "        low_cardinality_cat_features.append(col)\n",
            "    else:\n",
            "        high_cardinality_cat_features.append(col)\n",
            "\n",
            "print('=' * 60)\n",
            "print('Feature Type Detection Results:')\n",
            "print('=' * 60)\n",
            "print(f'Numerical ({len(numerical_features)}): {numerical_features}')\n",
            "print(f'Binary ({len(binary_features)}): {binary_features}')\n",
            "print(f'Low-cardinality Categorical ({len(low_cardinality_cat_features)}): {low_cardinality_cat_features}')\n",
            "print(f'High-cardinality Categorical ({len(high_cardinality_cat_features)}): {high_cardinality_cat_features}')\n",
            "print(f'Text ({len(text_features)}): {text_features}')\n",
            "print(f'Datetime ({len(datetime_features)}): {datetime_features}')\n",
            "print('=' * 60)\n",
        ]))

        # 第三个代码单元格：构建预处理管道
        cells.append(self._create_code_cell([
            "# ============== Build Preprocessing Pipeline ==============\n",
            "\n",
            "# Enable pandas output for all sklearn transformers (sklearn 1.2+)\n",
            "# This ensures DataFrame is preserved through the pipeline\n",
            "from sklearn import set_config\n",
            "set_config(transform_output='pandas')\n",
            "\n",
            "# Numerical preprocessing: median imputation + standardization\n",
            "numerical_pipeline = Pipeline([\n",
            "    ('imputer', SimpleImputer(strategy='median')),\n",
            "    ('scaler', StandardScaler()),\n",
            "])\n",
            "\n",
            "# Binary preprocessing: most frequent imputation + binary encoding\n",
            "binary_pipeline = Pipeline([\n",
            "    ('imputer', SimpleImputer(strategy='most_frequent')),\n",
            "    ('encoder', BinaryEncoder()),\n",
            "])\n",
            "\n",
            "# Low-cardinality categorical: most frequent imputation + one-hot encoding\n",
            "low_cat_pipeline = Pipeline([\n",
            "    ('imputer', SimpleImputer(strategy='most_frequent')),\n",
            "    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),\n",
            "])\n",
            "\n",
            "# High-cardinality categorical: most frequent imputation + ordinal encoding\n",
            "high_cat_pipeline = Pipeline([\n",
            "    ('imputer', SimpleImputer(strategy='most_frequent')),\n",
            "    ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)),\n",
            "])\n",
            "\n",
            "# Text preprocessing: TF-IDF vectorization\n",
            "text_pipeline = Pipeline([\n",
            "    ('vectorizer', TextColumnVectorizer(max_features=100)),\n",
            "])\n",
            "\n",
            "# Datetime preprocessing: extract temporal features + standardization\n",
            "datetime_pipeline = Pipeline([\n",
            "    ('extractor', DatetimeFeatureExtractor()),\n",
            "    ('scaler', StandardScaler()),\n",
            "])\n",
            "\n",
            "# Combine all transformers\n",
            "transformers = []\n",
            "if numerical_features:\n",
            "    transformers.append(('num', numerical_pipeline, numerical_features))\n",
            "if binary_features:\n",
            "    transformers.append(('bin', binary_pipeline, binary_features))\n",
            "if low_cardinality_cat_features:\n",
            "    transformers.append(('low_cat', low_cat_pipeline, low_cardinality_cat_features))\n",
            "if high_cardinality_cat_features:\n",
            "    transformers.append(('high_cat', high_cat_pipeline, high_cardinality_cat_features))\n",
            "if text_features:\n",
            "    transformers.append(('text', text_pipeline, text_features))\n",
            "if datetime_features:\n",
            "    transformers.append(('datetime', datetime_pipeline, datetime_features))\n",
            "\n",
            "preprocessor = ColumnTransformer(\n",
            "    transformers=transformers,\n",
            "    remainder='drop',  # Drop unhandled columns\n",
            "    verbose_feature_names_out=False\n",
            ")\n",
            "\n",
            "print(f'Total transformers: {len(transformers)}')\n",
            "for name, _, cols in transformers:\n",
            "    print(f'  - {name}: {len(cols)} features')\n",
        ]))
        
        return cells
    
    def _create_model_training_cells(self) -> List[Dict[str, Any]]:
        """创建模型训练 Cells"""
        cells = []
        
        # 获取估计器信息
        estimator_class, estimator_module = self.ESTIMATOR_MAP.get(
            self.best_estimator,
            ("UnknownRegressor", "unknown")
        )
        
        # 模型训练说明
        cells.append(self._create_markdown_cell([
            f"## Train {estimator_class}\n",
            "\n",
            f"Train the best model found by AutoML: **{estimator_class}**\n",
            "\n",
            "The hyperparameters below are the best configuration found during AutoML search.\n",
        ]))
        
        # 导入模型
        cells.append(self._create_code_cell([
            f"from {estimator_module} import {estimator_class}\n",
        ]))
        
        # 超参数配置
        config_str = self._format_config(self.best_config)
        cells.append(self._create_code_cell([
            f"# Best hyperparameters found by AutoML\n",
            f"best_config = {config_str}\n",
        ]))
        
        # 创建和训练模型（只记录到 MLflow，不注册到 Catalog）
        cells.append(self._create_code_cell([
            f"# Create full pipeline\n",
            f"model = Pipeline([\n",
            f"    ('preprocessor', preprocessor),\n",
            f"    ('regressor', {estimator_class}(**best_config)),\n",
            f"])\n",
            f"\n",
            f"# Train model and log to MLflow\n",
            f"with mlflow.start_run(experiment_id='{self.experiment_id}') as run:\n",
            f"    # Train the model\n",
            f"    model.fit(X_train, y_train)\n",
            f"    \n",
            f"    # Evaluate on validation set\n",
            f"    val_score = model.score(X_val, y_val)\n",
            f"    mlflow.log_metric('val_{self.metric}', val_score)\n",
            f"    print(f'Validation {self.metric}: {{val_score:.4f}}')\n",
            f"    \n",
            f"    # Log hyperparameters\n",
            f"    mlflow.log_params(best_config)\n",
            f"    \n",
            f"    # Infer model signature\n",
            f"    from mlflow.models import infer_signature\n",
            f"    y_pred = model.predict(X_val)\n",
            f"    signature = infer_signature(X_val, y_pred)\n",
            f"    \n",
            f"    # Log model to MLflow (without registering to Catalog)\n",
            f"    mlflow.sklearn.log_model(\n",
            f"        sk_model=model,\n",
            f"        artifact_path='model',\n",
            f"        signature=signature,\n",
            f"    )\n",
            f"    \n",
            f"    print(f'✅ Model logged to MLflow')\n",
            f"    print(f'   Run ID: {{run.info.run_id}}')\n",
            f"    print(f'   Experiment ID: {self.experiment_id}')\n",
        ]))
        
        return cells
    
    def _create_evaluation_cells(self) -> List[Dict[str, Any]]:
        """创建评估 Cells"""
        cells = []
        
        cells.append(self._create_markdown_cell([
            "## Model Evaluation\n",
            "\n",
            "Evaluate the model on the test set.\n",
        ]))
        
        cells.append(self._create_code_cell([
            "from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "# Predictions\n",
            "y_pred = model.predict(X_test)\n",
            "\n",
            "# Metrics\n",
            "mse = mean_squared_error(y_test, y_pred)\n",
            "mae = mean_absolute_error(y_test, y_pred)\n",
            "r2 = r2_score(y_test, y_pred)\n",
            "\n",
            "print(f'Test MSE: {mse:.4f}')\n",
            "print(f'Test MAE: {mae:.4f}')\n",
            "print(f'Test R2: {r2:.4f}')\n",
            "\n",
            "# Scatter plot\n",
            "plt.figure(figsize=(8, 6))\n",
            "plt.scatter(y_test, y_pred, alpha=0.5)\n",
            "plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)\n",
            "plt.xlabel('True Values')\n",
            "plt.ylabel('Predictions')\n",
            "plt.title('True vs Predicted Values')\n",
            "plt.show()\n",
        ]))
        
        return cells
    
    def _filter_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤配置，只保留当前估计器支持的参数

        FLAML 的 best_config 可能包含 FLAML 特有的参数（如 max_leaves for RF），
        这些参数不一定适用于原生的 sklearn/xgboost/lightgbm 模型。

        Args:
            config: FLAML 返回的原始配置

        Returns:
            过滤后的配置，只包含当前估计器支持的参数
        """
        valid_params = self.ESTIMATOR_VALID_PARAMS.get(self.best_estimator, set())

        if not valid_params:
            # 如果没有定义白名单，返回原始配置
            return config

        filtered_config = {}
        for key, value in config.items():
            if key in valid_params:
                filtered_config[key] = value

        return filtered_config

    def _format_config(self, config: Dict[str, Any]) -> str:
        """格式化配置为 Python 代码，同时过滤不支持的参数"""
        import json

        # 过滤配置
        filtered_config = self._filter_config(config)

        return json.dumps(filtered_config, indent=4)

