"""
Base Notebook Template

所有 Notebook 模板的基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaseNotebookTemplate(ABC):
    """
    Notebook 模板基类
    """

    def __init__(
        self,
        best_estimator: str,
        best_config: Dict[str, Any],
        experiment_id: str,
        run_id: str,
        mlflow_tracking_uri: str,
        features: List[str],
        target_col: str,
        metric: str,
        data_source_table: Optional[str] = None,
        # 环境变量配置（从 driver 读取）
        tencentcloud_secret_id: Optional[str] = None,
        tencentcloud_secret_key: Optional[str] = None,
        tencentcloud_tmp_token: Optional[str] = None,
        tencentcloud_endpoint: Optional[str] = None,
        wedata_project_id: Optional[str] = None,
        qcloud_region: Optional[str] = None,
        **kwargs
    ):
        """
        初始化模板

        Args:
            best_estimator: 最佳估计器名称
            best_config: 最佳超参数配置
            experiment_id: MLflow 实验 ID
            run_id: MLflow Run ID
            mlflow_tracking_uri: MLflow Tracking URI
            features: 特征列名列表
            target_col: 目标列名
            metric: 评估指标
            data_source_table: 数据源表名（如果用户传入表名）
            tencentcloud_secret_id: 腾讯云 Secret ID
            tencentcloud_secret_key: 腾讯云 Secret Key
            tencentcloud_tmp_token: 腾讯云临时 Token（可选）
            tencentcloud_endpoint: TCCatalog API 端点
            wedata_project_id: WeData 项目 ID
            qcloud_region: 腾讯云地域（如 ap-guangzhou）
            **kwargs: 其他参数
        """
        self.best_estimator = best_estimator
        self.best_config = best_config
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.features = features
        self.target_col = target_col
        self.metric = metric
        self.data_source_table = data_source_table

        # 环境变量配置
        self.tencentcloud_secret_id = tencentcloud_secret_id
        self.tencentcloud_secret_key = tencentcloud_secret_key
        self.tencentcloud_tmp_token = tencentcloud_tmp_token
        self.tencentcloud_endpoint = tencentcloud_endpoint or "tccatalog.internal.tencentcloudapi.com"
        self.wedata_project_id = wedata_project_id
        self.qcloud_region = qcloud_region or "ap-guangzhou"

        self.kwargs = kwargs
    
    def generate(self) -> Dict[str, Any]:
        """
        生成 Notebook

        Returns:
            Notebook 字典
        """
        cells = []

        # 添加各个 Cell
        cells.append(self._create_header_cell())
        cells.append(self._create_import_cell())
        cells.append(self._create_mlflow_setup_cell())
        cells.append(self._create_load_data_cell())
        cells.extend(self._create_preprocessing_cells())
        cells.extend(self._create_model_training_cells())
        cells.extend(self._create_evaluation_cells())
        cells.extend(self._create_model_registration_cells())
        cells.append(self._create_inference_cell())

        # 构建 Notebook
        notebook = {
            "cells": cells,
            "metadata": self._create_metadata(),
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        return notebook
    
    @abstractmethod
    def _create_preprocessing_cells(self) -> List[Dict[str, Any]]:
        """创建预处理 Cells"""
        pass
    
    @abstractmethod
    def _create_model_training_cells(self) -> List[Dict[str, Any]]:
        """创建模型训练 Cells"""
        pass
    
    @abstractmethod
    def _create_evaluation_cells(self) -> List[Dict[str, Any]]:
        """创建评估 Cells"""
        pass
    
    def _create_header_cell(self) -> Dict[str, Any]:
        """创建标题 Cell"""
        task_name = self.__class__.__name__.replace("NotebookTemplate", "")
        return self._create_markdown_cell([
            f"# {task_name} Training - Auto-generated Notebook\n",
            "\n",
            "- This is an auto-generated notebook by WeData AutoML.\n",
            f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"- Best Estimator: **{self.best_estimator}**\n",
            f"- Metric: **{self.metric}**\n",
            f"- MLflow Experiment: [{self.experiment_id}]({self.mlflow_tracking_uri}/#/experiments/{self.experiment_id})\n",
            f"- MLflow Run: [{self.run_id}]({self.mlflow_tracking_uri}/#/experiments/{self.experiment_id}/runs/{self.run_id})\n",
        ])
    
    def _create_import_cell(self) -> Dict[str, Any]:
        """创建导入 Cell"""
        return self._create_code_cell([
            "import os\n",
            "import mlflow\n",
            "import mlflow.sklearn\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "from sklearn.pipeline import Pipeline\n",
            "from sklearn.preprocessing import StandardScaler\n",
            "from sklearn.impute import SimpleImputer\n",
        ])
    
    def _create_mlflow_setup_cell(self) -> Dict[str, Any]:
        """创建 MLflow 设置 Cell"""
        return self._create_code_cell([
            f"# Set MLflow tracking URI\n",
            f"mlflow.set_tracking_uri('{self.mlflow_tracking_uri}')\n",
            f"\n",
            f"# Set MLflow registry URI (TCLake plugin for model registration)\n",
            f"region = os.environ.get('QCLOUD_REGION', 'ap-guangzhou')\n",
            f"mlflow.set_registry_uri(f'tclake:{{region}}')\n",
            f"print(f'Registry URI: tclake:{{region}}')\n",
            f"\n",
            f"# Set experiment\n",
            f"mlflow.set_experiment(experiment_id='{self.experiment_id}')\n",
        ])
    
    def _create_load_data_cell(self) -> Dict[str, Any]:
        """创建数据加载 Cell"""
        if self.data_source_table:
            # 用户传入了表名，使用 spark.table() 加载数据
            return self._create_code_cell([
                f"# Load training data from the same table used during training\n",
                f"from pyspark.sql import SparkSession\n",
                f"\n",
                f"# Get or create Spark session\n",
                f"spark = SparkSession.builder.getOrCreate()\n",
                f"\n",
                f"# Load data from table\n",
                f"table_name = '{self.data_source_table}'\n",
                f"df = spark.table(table_name).toPandas()\n",
                f"print(f'Data source: {{table_name}}')\n",
                f"print(f'Data shape: {{df.shape}}')\n",
                f"df.head()\n",
            ])
        else:
            # 用户传入的是 DataFrame，无法自动加载
            return self._create_code_cell([
                f"# Load training data\n",
                f"# Note: The original training used a DataFrame directly (not a table name).\n",
                f"# Please load your data using one of the following methods:\n",
                f"#   1. Load from table: df = spark.table('catalog.database.table_name').toPandas()\n",
                f"#   2. Load from parquet: df = pd.read_parquet('path/to/your/data.parquet')\n",
                f"#   3. Load from CSV: df = pd.read_csv('path/to/your/data.csv')\n",
                f"\n",
                f"# df = spark.table('your_table_name').toPandas()\n",
                f"# print(f'Data shape: {{df.shape}}')\n",
                f"# df.head()\n",
            ])
    
    def _create_model_registration_cells(self) -> List[Dict[str, Any]]:
        """创建模型注册的 Cells

        分为三部分：
        1. 安装 mlflow-tclake-plugin
        2. 设置环境变量（从 driver 渲染的凭证）
        3. 使用 mlflow-tclake-plugin 注册到 TCCatalog
        """
        cells = []

        # 获取模型名称
        model_name = self.kwargs.get('model_name', f'automl_{self.best_estimator}')

        # ===== Cell 1: 安装 mlflow-tclake-plugin =====
        cells.append(self._create_markdown_cell([
            "## Install mlflow-tclake-plugin\n",
            "\n",
            "Install the `mlflow-tclake-plugin` package to enable model registration to TencentCloud Catalog.\n",
        ]))

        cells.append(self._create_code_cell([
            "# Install mlflow-tclake-plugin for TCCatalog integration\n",
            "import subprocess\n",
            "import sys\n",
            "\n",
            "try:\n",
            "    import mlflow_tclake_plugin\n",
            "    print('✅ mlflow-tclake-plugin is already installed')\n",
            "except ImportError:\n",
            "    print('Installing mlflow-tclake-plugin...')\n",
            "    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mlflow-tclake-plugin', '-q'])\n",
            "    print('✅ mlflow-tclake-plugin installed successfully')\n",
        ]))

        # ===== Cell 2: 设置环境变量 =====
        cells.append(self._create_markdown_cell([
            "## Setup Environment Variables for TCCatalog\n",
            "\n",
            "Configure the environment variables required for `mlflow-tclake-plugin` to register models to TCCatalog.\n",
            "\n",
            "These credentials are automatically populated from the driver environment.\n",
        ]))

        # 生成环境变量设置代码
        env_code = [
            "import os\n",
            "\n",
            "# Set TencentCloud credentials for TCCatalog access\n",
            "# These values are rendered from the driver environment\n",
        ]

        # 根据是否有凭证，生成不同的代码
        if self.tencentcloud_secret_id and self.tencentcloud_secret_key:
            env_code.extend([
                f"os.environ['TENCENTCLOUD_SECRET_ID'] = '{self.tencentcloud_secret_id}'\n",
                f"os.environ['TENCENTCLOUD_SECRET_KEY'] = '{self.tencentcloud_secret_key}'\n",
            ])
            if self.tencentcloud_tmp_token:
                env_code.append(f"os.environ['TENCENTCLOUD_TMP_TOKEN'] = '{self.tencentcloud_tmp_token}'\n")
        else:
            env_code.extend([
                "# ⚠️ Credentials not provided during notebook generation\n",
                "# Please set your credentials manually:\n",
                "# os.environ['TENCENTCLOUD_SECRET_ID'] = 'your_secret_id'\n",
                "# os.environ['TENCENTCLOUD_SECRET_KEY'] = 'your_secret_key'\n",
                "# os.environ['TENCENTCLOUD_TMP_TOKEN'] = 'your_tmp_token'  # Optional\n",
            ])

        env_code.extend([
            f"\nos.environ['TENCENTCLOUD_ENDPOINT'] = '{self.tencentcloud_endpoint}'\n",
            f"os.environ['QCLOUD_REGION'] = '{self.qcloud_region}'\n",
        ])

        if self.wedata_project_id:
            env_code.append(f"os.environ['WEDATA_PROJECT_ID'] = '{self.wedata_project_id}'\n")

        env_code.extend([
            "\nprint('✅ Environment variables configured')\n",
            f"print(f'   Region: {self.qcloud_region}')\n",
            f"print(f'   Endpoint: {self.tencentcloud_endpoint}')\n",
        ])

        cells.append(self._create_code_cell(env_code))

        # ===== Cell 3: 注册到 TCCatalog =====
        cells.append(self._create_markdown_cell([
            "## Register Model to TCCatalog\n",
            "\n",
            "Use `mlflow-tclake-plugin` to register the trained model to TencentCloud Catalog.\n",
            "\n",
            "The model will be registered with a three-part name: `catalog.schema.model_name`\n",
        ]))

        # 生成模型注册代码
        register_code = [
            "import mlflow\n",
            "\n",
        ]

        if self.data_source_table:
            # 有数据源表名，自动解析 catalog 和 schema
            register_code.extend([
                "# Parse the three-part table name to get catalog and schema\n",
                f"data_source_table = '{self.data_source_table}'\n",
                "table_parts = data_source_table.split('.')\n",
                "\n",
                "if len(table_parts) >= 3:\n",
                "    catalog_name = table_parts[0]\n",
                "    schema_name = table_parts[1]\n",
                "elif len(table_parts) == 2:\n",
                "    catalog_name = 'DataLakeCatalog'  # Default catalog\n",
                "    schema_name = table_parts[0]\n",
                "else:\n",
                "    catalog_name = 'DataLakeCatalog'\n",
                "    schema_name = 'default'\n",
                "\n",
            ])
        else:
            # 没有数据源表名，使用默认值
            register_code.extend([
                "# No data source table provided, using default catalog and schema\n",
                "# Please modify these values as needed\n",
                "catalog_name = 'DataLakeCatalog'\n",
                "schema_name = 'default'\n",
                "\n",
            ])

        register_code.extend([
            f"# Model name for registration\n",
            f"model_name = '{model_name}'\n",
            "registered_model_name = f'{catalog_name}.{schema_name}.{model_name}'\n",
            "\n",
            "print(f'📦 Registering model to TCCatalog...')\n",
            "print(f'   Catalog: {catalog_name}')\n",
            "print(f'   Schema: {schema_name}')\n",
            "print(f'   Model: {model_name}')\n",
            "print(f'   Full Name: {registered_model_name}')\n",
            "\n",
            "# Configure TCLake as MLflow model registry\n",
            f"region = os.environ.get('QCLOUD_REGION', '{self.qcloud_region}')\n",
            "mlflow.set_registry_uri(f'tclake:{region}')\n",
            "\n",
            "# Register the model to TCCatalog\n",
            "# Note: run_id is captured from the training cell above\n",
            "model_uri = f'runs:/{run.info.run_id}/model'\n",
            "result = mlflow.register_model(model_uri, registered_model_name)\n",
            "\n",
            "print(f'\\n✅ Model successfully registered to TCCatalog!')\n",
            "print(f'   Model Name: {result.name}')\n",
            "print(f'   Version: {result.version}')\n",
            "print(f'   Source: {result.source}')\n",
        ])

        cells.append(self._create_code_cell(register_code))

        return cells

    def _create_inference_cell(self) -> Dict[str, Any]:
        """创建推理 Cell"""
        return self._create_code_cell([
            f"# Load model for inference\n",
            f"model_uri = f'runs:/{{run_id}}/model'\n",
            f"model = mlflow.pyfunc.load_model(model_uri)\n",
            f"\n",
            f"# Make predictions\n",
            f"# predictions = model.predict(test_data)\n",
            f"# print(predictions)\n",
        ])
    
    @staticmethod
    def _create_code_cell(source: List[str]) -> Dict[str, Any]:
        """创建代码 Cell"""
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source
        }
    
    @staticmethod
    def _create_markdown_cell(source: List[str]) -> Dict[str, Any]:
        """创建 Markdown Cell"""
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": source
        }
    
    def _create_metadata(self) -> Dict[str, Any]:
        """创建 Notebook 元数据"""
        return {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.0"
            }
        }

