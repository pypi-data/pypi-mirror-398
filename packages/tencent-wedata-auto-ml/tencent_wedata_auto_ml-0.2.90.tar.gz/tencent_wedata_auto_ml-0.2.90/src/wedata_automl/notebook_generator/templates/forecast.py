"""
Forecast Notebook Template

时序预测任务的 Notebook 模板
"""
from typing import Dict, Any, List
from wedata_automl.notebook_generator.templates.base import BaseNotebookTemplate


class ForecastNotebookTemplate(BaseNotebookTemplate):
    """
    时序预测任务 Notebook 模板
    """
    
    def _create_preprocessing_cells(self) -> List[Dict[str, Any]]:
        """创建预处理 Cells"""
        cells = []
        
        time_col = self.kwargs.get("time_col", "ds")
        horizon = self.kwargs.get("horizon", 30)
        frequency = self.kwargs.get("frequency", "D")
        
        # 数据准备说明
        cells.append(self._create_markdown_cell([
            "## Data Preparation\n",
            "\n",
            f"- **Time Column**: {time_col}\n",
            f"- **Target Column**: {self.target_col}\n",
            f"- **Horizon**: {horizon}\n",
            f"- **Frequency**: {frequency}\n",
        ]))
        
        # 数据准备代码
        cells.append(self._create_code_cell([
            f"# Prepare time series data\n",
            f"df['{time_col}'] = pd.to_datetime(df['{time_col}'])\n",
            f"df = df.sort_values('{time_col}')\n",
            f"\n",
            f"# Split into train and test\n",
            f"train_size = int(len(df) * 0.8)\n",
            f"train_df = df[:train_size]\n",
            f"test_df = df[train_size:]\n",
            f"\n",
            f"print(f'Train size: {{len(train_df)}}')\n",
            f"print(f'Test size: {{len(test_df)}}')\n",
        ]))
        
        return cells
    
    def _create_model_training_cells(self) -> List[Dict[str, Any]]:
        """创建模型训练 Cells"""
        cells = []
        
        time_col = self.kwargs.get("time_col", "ds")
        horizon = self.kwargs.get("horizon", 30)
        
        # 模型训练说明
        cells.append(self._create_markdown_cell([
            f"## Train Forecast Model\n",
            "\n",
            f"Train the best model found by AutoML: **{self.best_estimator}**\n",
            "\n",
            "The hyperparameters below are the best configuration found during AutoML search.\n",
        ]))
        
        # 导入 FLAML
        cells.append(self._create_code_cell([
            "from flaml import AutoML\n",
        ]))
        
        # 超参数配置
        config_str = self._format_config(self.best_config)
        cells.append(self._create_code_cell([
            f"# Best hyperparameters found by AutoML\n",
            f"best_config = {config_str}\n",
        ]))
        
        # 获取模型名称（从 kwargs 或生成默认名称）
        model_name = self.kwargs.get('model_name', f'automl_forecast_{self.best_estimator}')

        # 创建和训练模型
        cells.append(self._create_code_cell([
            f"# Create AutoML instance\n",
            f"automl = AutoML()\n",
            f"\n",
            f"# Model name for registration (three-part name: catalog.schema.model)\n",
            f"# You can customize this name\n",
            f"MODEL_NAME = '{model_name}'\n",
            f"\n",
            f"# Train model and register to TCCatalog\n",
            f"with mlflow.start_run(experiment_id='{self.experiment_id}') as run:\n",
            f"    automl.fit(\n",
            f"        dataframe=train_df,\n",
            f"        label='{self.target_col}',\n",
            f"        task='forecast',\n",
            f"        time_col='{time_col}',\n",
            f"        period={horizon},\n",
            f"        **best_config\n",
            f"    )\n",
            f"    \n",
            f"    print(f'Best estimator: {{automl.best_estimator}}')\n",
            f"    print(f'Best config: {{automl.best_config}}')\n",
            f"    \n",
            f"    # Save and register the forecast model\n",
            f"    import pickle\n",
            f"    import tempfile\n",
            f"    \n",
            f"    with tempfile.TemporaryDirectory() as tmpdir:\n",
            f"        model_path = f'{{tmpdir}}/model.pkl'\n",
            f"        with open(model_path, 'wb') as f:\n",
            f"            pickle.dump(automl, f)\n",
            f"        \n",
            f"        # Log model artifact\n",
            f"        mlflow.log_artifact(model_path, 'model')\n",
            f"        \n",
            f"        # Register model to TCCatalog\n",
            f"        model_uri = f'runs:/{{run.info.run_id}}/model'\n",
            f"        result = mlflow.register_model(model_uri, MODEL_NAME)\n",
            f"        \n",
            f"        print(f'✅ Model registered: {{MODEL_NAME}}')\n",
            f"        print(f'   Version: {{result.version}}')\n",
            f"        print(f'   Run ID: {{run.info.run_id}}')\n",
        ]))
        
        return cells
    
    def _create_evaluation_cells(self) -> List[Dict[str, Any]]:
        """创建评估 Cells"""
        cells = []
        
        time_col = self.kwargs.get("time_col", "ds")
        horizon = self.kwargs.get("horizon", 30)
        
        cells.append(self._create_markdown_cell([
            "## Model Evaluation\n",
            "\n",
            "Evaluate the model on the test set.\n",
        ]))
        
        cells.append(self._create_code_cell([
            "from sklearn.metrics import mean_absolute_error, mean_squared_error\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "# Make predictions\n",
            "# Note: Pass the full test_df to include exogenous features if the model uses them\n",
            f"predictions = automl.predict(test_df)\n",
            "\n",
            "# Calculate metrics\n",
            f"mae = mean_absolute_error(test_df['{self.target_col}'], predictions)\n",
            f"mse = mean_squared_error(test_df['{self.target_col}'], predictions)\n",
            f"rmse = mse ** 0.5\n",
            "\n",
            "print(f'Test MAE: {mae:.4f}')\n",
            "print(f'Test RMSE: {rmse:.4f}')\n",
            "\n",
            "# Plot predictions\n",
            "plt.figure(figsize=(12, 6))\n",
            f"plt.plot(test_df['{time_col}'], test_df['{self.target_col}'], label='Actual', marker='o')\n",
            f"plt.plot(test_df['{time_col}'], predictions, label='Predicted', marker='x')\n",
            "plt.xlabel('Time')\n",
            f"plt.ylabel('{self.target_col}')\n",
            "plt.title('Forecast: Actual vs Predicted')\n",
            "plt.legend()\n",
            "plt.xticks(rotation=45)\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
        ]))
        
        return cells
    
    def _format_config(self, config: Dict[str, Any]) -> str:
        """格式化配置为 Python 代码"""
        import json
        return json.dumps(config, indent=4)

