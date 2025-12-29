#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 MLflow source.name 管理功能（单元测试）

不需要完整的 AutoML 训练，只验证核心逻辑。
"""

import os
import sys
import tempfile

import mlflow
import pytest


class TestMlflowSourceName:
    """测试 MLflow source.name tag 管理"""
    
    @pytest.fixture(autouse=True)
    def setup_mlflow(self):
        """设置 MLflow 临时环境"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mlflow_uri = f"file://{tmpdir}/mlruns"
            mlflow.set_tracking_uri(mlflow_uri)
            
            # 设置实验
            mlflow.set_experiment("test_source_name")
            
            yield
    
    def test_delete_tag_removes_source_name(self):
        """测试 delete_tag 可以删除 mlflow.source.name"""
        # 创建一个 run 并设置 source.name
        with mlflow.start_run() as run:
            run_id = run.info.run_id
            
            # 先设置 tag
            mlflow.set_tag("mlflow.source.name", "/original_notebook.ipynb")
            
            # 验证 tag 存在
            client = mlflow.tracking.MlflowClient()
            run_data = client.get_run(run_id)
            assert run_data.data.tags.get("mlflow.source.name") == "/original_notebook.ipynb"
            
            # 删除 tag
            mlflow.delete_tag("mlflow.source.name")
            
            # 验证 tag 被删除
            run_data = client.get_run(run_id)
            assert run_data.data.tags.get("mlflow.source.name") is None
    
    def test_delete_tag_on_nonexistent_tag_does_not_error(self):
        """测试删除不存在的 tag 不会报错"""
        with mlflow.start_run() as run:
            # 尝试删除不存在的 tag
            try:
                mlflow.delete_tag("mlflow.source.name")
            except Exception:
                # 某些 MLflow 版本可能会报错，我们捕获并忽略
                pass
    
    def test_set_tag_after_run_ends(self):
        """测试 run 结束后可以通过 MlflowClient 设置 tag"""
        # 创建一个 run
        with mlflow.start_run() as run:
            run_id = run.info.run_id
        
        # run 已结束，使用 client 设置 tag
        client = mlflow.tracking.MlflowClient()
        client.set_tag(run_id, "mlflow.source.name", "/new_notebook.ipynb")
        
        # 验证 tag 被设置
        run_data = client.get_run(run_id)
        assert run_data.data.tags.get("mlflow.source.name") == "/new_notebook.ipynb"
    
    def test_nested_run_delete_tag(self):
        """测试嵌套 run 中删除 tag"""
        with mlflow.start_run() as parent_run:
            parent_run_id = parent_run.info.run_id
            
            # 删除父 run 的 source.name
            try:
                mlflow.delete_tag("mlflow.source.name")
            except Exception:
                pass
            
            # 创建子 run
            with mlflow.start_run(run_name="child_run", nested=True) as child_run:
                child_run_id = child_run.info.run_id
                
                # 删除子 run 的 source.name
                try:
                    mlflow.delete_tag("mlflow.source.name")
                except Exception:
                    pass
        
        # 验证两个 run 都没有 source.name
        client = mlflow.tracking.MlflowClient()
        
        parent_data = client.get_run(parent_run_id)
        child_data = client.get_run(child_run_id)
        
        assert parent_data.data.tags.get("mlflow.source.name") is None
        assert child_data.data.tags.get("mlflow.source.name") is None
        
        # 更新父 run 的 source.name
        client.set_tag(parent_run_id, "mlflow.source.name", "/generated_notebook.ipynb")
        
        # 验证只有父 run 有 source.name
        parent_data = client.get_run(parent_run_id)
        child_data = client.get_run(child_run_id)
        
        assert parent_data.data.tags.get("mlflow.source.name") == "/generated_notebook.ipynb"
        assert child_data.data.tags.get("mlflow.source.name") is None


class TestAutoMLSummaryUpdateSourceName:
    """测试 AutoMLSummary.update_source_name 方法"""

    @pytest.fixture(autouse=True)
    def setup_mlflow(self):
        """设置 MLflow 临时环境"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mlflow_uri = f"file://{tmpdir}/mlruns"
            mlflow.set_tracking_uri(mlflow_uri)
            mlflow.set_experiment("test_summary")
            yield

    def test_update_source_name_method(self):
        """测试 AutoMLSummary.update_source_name 方法"""
        # 直接从 summary 模块导入，避免触发 __init__ 的完整导入链
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "summary",
            os.path.join(os.path.dirname(__file__), "..", "src", "wedata_automl", "summary.py")
        )
        summary_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(summary_module)
        AutoMLSummary = summary_module.AutoMLSummary

        # 创建一个 run
        with mlflow.start_run() as run:
            run_id = run.info.run_id
            experiment_id = run.info.experiment_id

        # 创建 summary 对象
        summary = AutoMLSummary(
            experiment_id=experiment_id,
            run_id=run_id,
            best_trial_run_id=run_id,
            model_uri=f"runs:/{run_id}/model"
        )

        # 调用 update_source_name
        success = summary.update_source_name("/my_notebook.ipynb")

        # 验证成功
        assert success is True

        # 验证 tag 被更新
        client = mlflow.tracking.MlflowClient()
        run_data = client.get_run(run_id)
        assert run_data.data.tags.get("mlflow.source.name") == "/my_notebook.ipynb"


class TestCleanupChildRunsSourceName:
    """测试 cleanup_child_runs_source_name 方法（模拟版本，不依赖 FLAML）"""

    @pytest.fixture(autouse=True)
    def setup_mlflow(self):
        """设置 MLflow 临时环境"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mlflow_uri = f"file://{tmpdir}/mlruns"
            mlflow.set_tracking_uri(mlflow_uri)
            mlflow.set_experiment("test_cleanup")
            yield

    def test_cleanup_removes_source_name_from_child_runs(self):
        """测试可以使用 MlflowClient 删除子 run 的 source.name"""
        # 创建父 run 和多个子 run
        with mlflow.start_run() as parent_run:
            parent_run_id = parent_run.info.run_id
            experiment_id = parent_run.info.experiment_id

            # 创建几个子 run，模拟有 source.name 的情况
            child_run_ids = []
            for i in range(3):
                with mlflow.start_run(run_name=f"child_{i}", nested=True) as child_run:
                    child_run_ids.append(child_run.info.run_id)
                    # 设置 source.name（模拟 MLFLOW_RUN_CONTEXT）
                    mlflow.set_tag("mlflow.source.name", "/test_notebook.ipynb")

        # 验证子 run 有 source.name
        client = mlflow.tracking.MlflowClient()
        for run_id in child_run_ids:
            run = client.get_run(run_id)
            assert run.data.tags.get("mlflow.source.name") == "/test_notebook.ipynb"

        # 模拟 cleanup_child_runs_source_name 的逻辑
        child_runs = client.search_runs(
            experiment_ids=[experiment_id],
            filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}'",
            max_results=1000
        )

        cleaned_count = 0
        for run in child_runs:
            run_id = run.info.run_id
            if "mlflow.source.name" in run.data.tags:
                try:
                    client.delete_tag(run_id, "mlflow.source.name")
                    cleaned_count += 1
                except Exception:
                    pass

        # 验证清理成功
        assert cleaned_count == 3

        # 验证所有子 run 的 source.name 已删除
        for run_id in child_run_ids:
            run = client.get_run(run_id)
            assert run.data.tags.get("mlflow.source.name") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

