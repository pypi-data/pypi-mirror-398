# WeData AutoML

腾讯云 WeData 平台的 AutoML SDK，基于 FLAML 构建，集成 MLflow 进行实验追踪和模型注册。

## ✨ 功能特性

- **多任务支持**：分类（Classification）、回归（Regression）、时序预测（Forecast）
- **FLAML 驱动**：高效的 AutoML 超参数搜索，支持 LightGBM、XGBoost、RandomForest 等估计器
- **MLflow 集成**：自动实验追踪、模型日志记录、模型注册
- **Spark 支持**：支持 Spark DataFrame 输入，可配合 DLC 使用
- **特征工程集成**：与 WeData 特征工程 SDK 无缝对接
- **Notebook 生成**：自动生成可复现的 Jupyter Notebook（分类/回归任务）
- **并发训练**：支持多 Trial 并发执行

## 📦 安装

```bash
# 基础安装
pip install tencent-wedata-auto-ml

# 可选依赖
pip install "tencent-wedata-auto-ml[xgboost]"     # XGBoost 支持
pip install "tencent-wedata-auto-ml[lightgbm]"   # LightGBM 支持
pip install "tencent-wedata-auto-ml[full]"       # 完整安装（推荐）
```

## 🚀 快速开始

### 便捷函数 API

```python
from wedata_automl import classify, regress, forecast

# 分类任务
summary = classify(
    dataset=spark.table("demo.wine_quality"),
    target_col="quality",
    timeout_minutes=10,
    max_trials=100,
    metric="accuracy",
    project_id="your_project_id",
    experiment_name="wine_classification",
    register_model=True,
    model_name="wine_model"
)

# 回归任务
summary = regress(
    dataset=df,
    target_col="price",
    timeout_minutes=10,
    metric="r2",
    project_id="your_project_id"
)

# 时序预测任务
summary = forecast(
    dataset=spark.table("demo.sales_data"),
    target_col="sales",
    time_col="date",
    horizon=30,
    frequency="D",
    timeout_minutes=60,
    project_id="your_project_id"
)
```

### 任务类 API

```python
from wedata_automl import Classifier, Regressor, Forecast

# 使用 Classifier 类
classifier = Classifier()
summary = classifier.fit(
    dataset=df,
    target_col="label",
    timeout_minutes=10,
    project_id="your_project_id"
)

# 使用 Regressor 类
regressor = Regressor()
summary = regressor.fit(
    dataset=df,
    target_col="target",
    timeout_minutes=10,
    project_id="your_project_id"
)
```

### 查看结果

```python
print(summary)
# AutoMLSummary:
#   Experiment ID: 42
#   Run ID: abc123...
#   Best Trial Run ID: def456...
#   Model URI: runs:/abc123.../model
#   Best Estimator: lgbm
#   Metrics:
#     accuracy: 0.9500
#     f1: 0.9400

# 生成可复现 Notebook（仅分类/回归任务）
summary.generate_notebook("best_model.ipynb")

# 保存 Notebook 到 WeData 平台
summary.save_notebook_to_wedata()
```

## 📋 主要参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `dataset` | 数据集（Pandas/Spark DataFrame 或表名） | 必填 |
| `target_col` | 目标列名 | 必填 |
| `project_id` | WeData 项目 ID | 必填 |
| `timeout_minutes` | 超时时间（分钟） | 5 |
| `max_trials` | 最大试验次数 | 100 |
| `metric` | 评估指标 | auto |
| `estimator_list` | 估计器列表 | None（使用全部） |
| `register_model` | 是否注册模型 | True |
| `model_name` | 注册模型名称 | None |
| `experiment_name` | MLflow 实验名称 | None |
| `custom_hp` | 自定义超参数搜索空间 | None |

### 评估指标

**分类任务**：`accuracy`, `f1`, `log_loss`, `roc_auc`, `precision`, `recall`

**回归任务**：`r2`, `mse`, `rmse`, `mae`, `mape`

**时序预测**：`smape`, `mse`, `rmse`, `mae`, `mdape`

### 估计器列表

**分类/回归**：`lgbm`, `xgboost`, `rf`, `extra_tree`, `lrl1`（仅分类）

**时序预测**：`prophet`, `arima`, `sarimax`

## ⚙️ 环境配置

```bash
# 必需：项目 ID
export WEDATA_PROJECT_ID="your_project_id"

# 必需：MLflow Tracking URI
export MLFLOW_TRACKING_URI="http://your-mlflow-server:5000"

# 可选：腾讯云密钥（用于保存 Notebook 到 WeData）
export TENCENTCLOUD_SECRET_ID="your_secret_id"
export TENCENTCLOUD_SECRET_KEY="your_secret_key"
```

## 📁 项目结构

```
wedata-automl/
├── src/wedata_automl/
│   ├── api.py              # 便捷函数 (classify, regress, forecast)
│   ├── summary.py          # AutoMLSummary 结果对象
│   ├── driver.py           # AutoML 驱动程序
│   ├── tasks/              # 任务类
│   │   ├── classifier.py   # Classifier 类
│   │   ├── regressor.py    # Regressor 类
│   │   └── forecast.py     # Forecast 类
│   ├── engines/            # 训练引擎
│   │   ├── flaml_trainer.py # FLAML 训练器
│   │   └── trial_hook.py   # Trial 日志钩子
│   ├── notebook_generator/ # Notebook 生成器
│   └── utils/              # 工具函数
├── templates/              # Driver 模板
│   ├── classification_driver_template.py
│   └── forecast_driver_template.py
├── docs/                   # 文档
└── examples/               # 示例代码
```

## 📚 文档

### 使用指南
- [Notebook 生成器](docs/NOTEBOOK_GENERATOR.md) - 自动生成可复现 Notebook
- [并行训练支持](docs/FLAML_PARALLEL_SUPPORT.md) - 多 Trial 并发执行
- [日志文件管理](docs/LOG_FILE_MANAGEMENT.md) - FLAML 日志配置
- [主要指标记录](docs/PRIMARY_METRIC_LOGGING.md) - 评估指标说明
- [模型注册标签](docs/REGISTER_MODEL_TAG.md) - 模型注册配置

### 技术参考
- [MLflow 版本兼容性](docs/MLFLOW_VERSION_COMPATIBILITY.md) - MLflow 2.16.x - 2.22.x 支持
- [MLflow 补丁说明](docs/MLFLOW_PATCH_README.md) - 自动补丁机制
 - WeData 脚本创建 API
- [Databricks AutoML 实现分析](docs/DATABRICKS_AUTOML_IMPLEMENTATION.md) - 设计参考

## ⚠️ 注意事项

- Python >= 3.9
- **Project ID 必填**：通过 `project_id` 参数或 `WEDATA_PROJECT_ID` 环境变量配置
- MLflow Tracking URI 必须正确配置

## 📄 License

MIT
