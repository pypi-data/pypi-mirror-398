"""
Catalog Registry - 将最佳模型注册到 TencentCloud Catalog

使用 mlflow-tclake-plugin 的 TCLakeStore 将模型注册到 TencentCloud Catalog。

环境变量要求（必需）：
- TENCENTCLOUD_SECRET_ID: 腾讯云 Secret ID
- TENCENTCLOUD_SECRET_KEY: 腾讯云 Secret Key
- TENCENTCLOUD_ENDPOINT: tccatalog API 端点（如 tccatalog.tencentcloudapi.com）
- WEDATA_PROJECT_ID: WeData 项目 ID

环境变量（可选）：
- TENCENTCLOUD_TOKEN: 临时 Token（使用临时密钥时需要）
- TENCENTCLOUD_DEFAULT_CATALOG_NAME: 默认 Catalog 名称（默认 "default"）
- TENCENTCLOUD_DEFAULT_SCHEMA_NAME: 默认 Schema 名称（默认 "default"）

模型名称格式：
- 完整格式: "catalog.schema.model_name" (3 部分)
- 简化格式: "schema.model_name" (2 部分，使用默认 catalog)
- 最简格式: "model_name" (1 部分，使用默认 catalog 和 schema)
"""

import os
from typing import Optional, Dict, Any
from wedata_automl.utils.print_utils import safe_print


def register_model_to_catalog(
    model_uri: str,
    model_name: str,
    run_id: Optional[str] = None,
    run_link: Optional[str] = None,
    description: Optional[str] = None,
    region: str = "ap-beijing",
    tags: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    将模型注册到 TencentCloud Catalog

    使用 mlflow-tclake-plugin 的 TCLakeStore 将 MLflow 模型注册到 TencentCloud Catalog。
    模型会被创建为 Catalog 中的 RegisteredModel，每次调用会创建新的 ModelVersion。

    Args:
        model_uri: MLflow 模型 URI，如 "runs:/{run_id}/model"
        model_name: 模型名称，支持三种格式：
            - "catalog.schema.model_name" (完整)
            - "schema.model_name" (使用默认 catalog)
            - "model_name" (使用默认 catalog 和 schema)
        run_id: 关联的 MLflow run ID，会作为 property 存储
        run_link: 关联的 MLflow run 链接，会作为 property 存储
        description: 模型描述
        region: 地域，默认 "ap-beijing"
        tags: 额外的 tags，会作为 properties 存储（key 会添加 "tclake.tag." 前缀）

    Returns:
        注册结果字典，包含以下字段：
        - success: bool
        - model_name: str
        - version: str
        - source: str (模型 URI)
        - run_id: str
        失败返回 None

    Note:
        TCLakeStore 会自动从 model_uri 读取模型签名并存储到 Catalog。
        还会自动将 WEDATA_PROJECT_ID 作为 "wedata.project" property 存储。
    """
    try:
        # 检查必要的环境变量
        secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID", "")
        secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY", "")

        if not secret_id or not secret_key:
            safe_print("⚠️  Catalog 注册跳过：未设置 TENCENTCLOUD_SECRET_ID/SECRET_KEY")
            return None

        # 检查是否设置了 tccatalog endpoint
        endpoint = os.environ.get("TENCENTCLOUD_ENDPOINT", "")
        if not endpoint:
            safe_print("⚠️  Catalog 注册跳过：未设置 TENCENTCLOUD_ENDPOINT")
            return None

        # 导入本地的 TCLakeStore
        try:
            from .tclake_store import TCLakeStore
        except ImportError as e:
            safe_print(f"⚠️  Catalog 注册跳过：TCLakeStore 导入失败: {e}")
            return None

        # 创建 TCLakeStore 实例
        # store_uri 格式: "tclake:{region}"
        store_uri = f"tclake:{region}"
        store = TCLakeStore(store_uri=store_uri)

        # 检查模型是否已存在，如果不存在则创建
        try:
            store.get_registered_model(model_name)
            safe_print(f"📦 模型已存在于 Catalog: {model_name}")
        except Exception:
            # 模型不存在，创建新模型
            safe_print(f"📦 在 Catalog 中创建新模型: {model_name}")
            store.create_registered_model(
                name=model_name,
                description=description,
            )

        # 创建模型版本
        # tags 需要转换为 ModelVersionTag 对象
        from mlflow.entities.model_registry import ModelVersionTag
        version_tags = []
        if tags:
            for key, value in tags.items():
                version_tags.append(ModelVersionTag(key, str(value)))

        # TCLakeStore.create_model_version 会自动:
        # 1. 从 source (model_uri) 读取模型签名
        # 2. 将 run_id 存储为 "tclake.mlflow.run_id" property
        # 3. 将 run_link 存储为 "tclake.mlflow.run_link" property
        # 4. 将 WEDATA_PROJECT_ID 存储为 "wedata.project" property
        model_version = store.create_model_version(
            name=model_name,
            source=model_uri,
            run_id=run_id,
            run_link=run_link,
            description=description,
            tags=version_tags if version_tags else None,
        )

        if model_version:
            safe_print(f"✅ 模型已注册到 Catalog: {model_name} v{model_version.version}")
            return {
                "success": True,
                "model_name": model_name,
                "version": model_version.version,
                "source": model_version.source,
                "run_id": model_version.run_id,
            }
        else:
            safe_print(f"⚠️  Catalog 模型版本创建失败")
            return None

    except Exception as e:
        safe_print(f"⚠️  Catalog 注册失败: {e}")
        return None


def is_catalog_registry_enabled() -> bool:
    """
    检查是否启用了 Catalog 注册功能

    Returns:
        True 如果必要的环境变量都已设置
    """
    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    endpoint = os.environ.get("TENCENTCLOUD_ENDPOINT", "")

    return bool(secret_id and secret_key and endpoint)

