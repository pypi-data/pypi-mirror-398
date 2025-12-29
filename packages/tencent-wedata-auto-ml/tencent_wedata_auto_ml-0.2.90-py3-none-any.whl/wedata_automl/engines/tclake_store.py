"""
TCLake Store - TencentCloud Catalog 模型注册存储

从 mlflow-tclake-plugin 迁移的代码，用于将模型注册到 TencentCloud Catalog。

环境变量要求（必需）：
- TENCENTCLOUD_SECRET_ID: 腾讯云 Secret ID
- TENCENTCLOUD_SECRET_KEY: 腾讯云 Secret Key
- TENCENTCLOUD_ENDPOINT: tccatalog API 端点
- WEDATA_PROJECT_ID: WeData 项目 ID

环境变量（可选）：
- TENCENTCLOUD_TOKEN: 临时 Token
- TENCENTCLOUD_DEFAULT_CATALOG_NAME: 默认 Catalog 名称（默认 "default"）
- TENCENTCLOUD_DEFAULT_SCHEMA_NAME: 默认 Schema 名称（默认 "default"）
- TENCENTCLOUD_DEBUG: 开启调试日志
- TCLAKE_CACHE_SIZE: 缓存大小（默认 100）
- TCLAKE_CACHE_TTL_SECS: 缓存过期时间秒数（默认 300）
"""

import base64
import json
import os
import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from cachetools import TTLCache
from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from mlflow.entities.model_registry import RegisteredModel, ModelVersion, ModelVersionTag
from mlflow.exceptions import MlflowException
from mlflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE, RESOURCE_ALREADY_EXISTS
from mlflow.store.model_registry import (
    SEARCH_REGISTERED_MODEL_MAX_RESULTS_THRESHOLD,
    SEARCH_MODEL_VERSION_MAX_RESULTS_THRESHOLD,
)
from mlflow.store.model_registry.abstract_store import AbstractStore
from mlflow.utils.search_utils import SearchModelUtils, SearchModelVersionUtils
from mlflow.store.entities.paged_list import PagedList


# ============================================================================
# 常量定义
# ============================================================================

TCLAKE_MLFLOW_TAG_PREFIX = "tclake.tag."
TCLAKE_MLFLOW_RUN_ID_KEY = "tclake.mlflow.run_id"
TCLAKE_MLFLOW_RUN_LINK_KEY = "tclake.mlflow.run_link"
TCLAKE_UUID_KEY = "tccatalog.identifier"
TCLAKE_MLFLOW_MODEL_SIGNATURE_KEY = "tclake.mlflow.model_signature"
TCLAKE_WEDATA_PROJECT_ID_KEY = "wedata.project"

_tencent_cloud_debug = os.getenv("TENCENTCLOUD_DEBUG", None)


def _log_msg(msg: str) -> None:
    if _tencent_cloud_debug:
        print(msg)


def _get_create_time_from_audit(audit: Dict) -> int:
    dt_str = audit["CreatedTime"]
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)


def _get_last_updated_time_from_audit(audit: Dict) -> int:
    dt_str = audit["LastModifiedTime"]
    if dt_str is None or len(dt_str) == 0:
        return _get_create_time_from_audit(audit)
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)


def _get_description(resp: Optional[Dict]) -> Optional[str]:
    if resp is None or "Comment" not in resp:
        return None
    return resp["Comment"]


def _set_kv_to_properties(key: str, value: Any, properties: Optional[List] = None) -> List:
    if properties is None:
        properties = []
    if value is not None:
        properties.append({"Key": key, "Value": value})
    return properties


def _get_kv_from_properties(properties: Optional[List], key: str) -> Optional[str]:
    if properties is None:
        return None
    for p in properties:
        if p["Key"] == key:
            return p["Value"]
    return None


def _set_run_id_to_properties(run_id: Optional[str], properties: Optional[List] = None) -> List:
    return _set_kv_to_properties(TCLAKE_MLFLOW_RUN_ID_KEY, run_id, properties)


def _get_run_id_from_properties(properties: Optional[List]) -> Optional[str]:
    return _get_kv_from_properties(properties, TCLAKE_MLFLOW_RUN_ID_KEY)


def _set_run_link_to_properties(run_link: Optional[str], properties: Optional[List]) -> List:
    return _set_kv_to_properties(TCLAKE_MLFLOW_RUN_LINK_KEY, run_link, properties)


def _get_run_link_from_properties(properties: Optional[List]) -> Optional[str]:
    return _get_kv_from_properties(properties, TCLAKE_MLFLOW_RUN_LINK_KEY)


def _add_tag_to_properties(tag: ModelVersionTag, properties: Optional[List] = None) -> List:
    if tag and tag.value is not None:
        properties = _set_kv_to_properties(TCLAKE_MLFLOW_TAG_PREFIX + tag.key, tag.value, properties)
    return properties


def _add_tags_to_properties(tags: Optional[List[ModelVersionTag]], properties: Optional[List] = None) -> List:
    if tags:
        for tag in tags:
            properties = _add_tag_to_properties(tag, properties)
    return properties


def _add_project_id_to_properties(project_id: Optional[str], properties: Optional[List] = None) -> List:
    if project_id is not None:
        properties = _set_kv_to_properties(TCLAKE_WEDATA_PROJECT_ID_KEY, project_id, properties)
    return properties



def _parse_model_signatures_from_dict(signature_dict: Dict) -> List[Dict]:
    """解析模型签名字典为 Catalog 格式"""
    signatures = []
    inputs_str = signature_dict.get("inputs")
    if inputs_str:
        inputs = json.loads(inputs_str)
        for input_item in inputs:
            model_signature = {
                "name": input_item.get("name", ""),
                "type": "INPUT",
                "inputFlag": "true"
            }
            type_val = input_item.get("type")
            if type_val is not None:
                if type_val == "tensor":
                    tensor_spec = input_item.get("tensor-spec", {}).get("dtype", "")
                    if tensor_spec:
                        model_signature["type"] = str(tensor_spec)
                else:
                    model_signature["type"] = str(type_val)
            signatures.append(model_signature)

    outputs_str = signature_dict.get("outputs")
    if outputs_str:
        outputs = json.loads(outputs_str)
        for output_item in outputs:
            name_val = output_item.get("name", "")
            if not name_val:
                name_val = output_item.get("prediction_column_name", "")
            model_signature = {
                "name": name_val,
                "type": "OUTPUT",
                "inputFlag": "false"
            }
            type_val = output_item.get("type")
            if type_val is not None:
                if type_val == "tensor":
                    tensor_spec = output_item.get("tensor-spec", {}).get("dtype", "")
                    if tensor_spec:
                        model_signature["type"] = str(tensor_spec)
                else:
                    model_signature["type"] = str(type_val)
            signatures.append(model_signature)

    _log_msg(f"parse model version signatures: {signatures}")
    return signatures


def _add_model_signature_to_properties(source: str, properties: List) -> List:
    """从模型源获取签名并添加到 properties"""
    _log_msg(f"model source is {source}")
    try:
        from mlflow.models.model import get_model_info
        model_info = get_model_info(source)
        signature = model_info.signature
        _log_msg(f"model {source} signature is {signature}")
        if signature:
            sig_json = json.dumps(_parse_model_signatures_from_dict(signature.to_dict()))
            _log_msg(f"model {source} signature json is {sig_json}")
        else:
            _log_msg(f"Registered model signature is not found in source artifact location '{source}'")
            sig_json = json.dumps([])
    except Exception as e:
        _log_msg(f"Failed to get model signature from {source}: {e}")
        sig_json = json.dumps([])
    properties = _set_kv_to_properties(TCLAKE_MLFLOW_MODEL_SIGNATURE_KEY, sig_json, properties)
    return properties


def _get_model_version(version: int) -> str:
    return str(version)


def _set_model_version(version: str) -> int:
    return int(version)


def _make_model(resp: Dict) -> RegisteredModel:
    """从 API 响应构造 RegisteredModel 对象"""
    properties = resp["Properties"]
    audit = resp["Audit"]
    return RegisteredModel(
        name=resp["Name"],
        creation_timestamp=_get_create_time_from_audit(audit),
        last_updated_timestamp=_get_last_updated_time_from_audit(audit),
        description=_get_description(resp),
        tags=_get_tags_from_properties(properties),
    )


def _get_model_version_name(entity: Dict) -> str:
    return "{}.{}.{}".format(entity["CatalogName"], entity["SchemaName"], entity["ModelName"])


def _make_model_version(entity: Dict, name: str) -> ModelVersion:
    """从 API 响应构造 ModelVersion 对象"""
    properties = entity["Properties"]
    audit = entity["Audit"]
    return ModelVersion(
        name=name,
        version=_get_model_version(entity["Version"]),
        creation_timestamp=_get_create_time_from_audit(audit),
        last_updated_timestamp=_get_last_updated_time_from_audit(audit),
        description=_get_description(entity),
        source=entity["Uri"],
        run_id=_get_run_id_from_properties(properties),
        tags=_get_tags_from_properties(properties),
        run_link=_get_run_link_from_properties(properties),
        status="READY",
    )


def _get_tencent_cloud_headers() -> Optional[Dict]:
    header_json = os.getenv("TENCENTCLOUD_HEADER_JSON", None)
    if header_json is None:
        return None
    return json.loads(header_json)


def _get_tencent_cloud_client_profile():
    endpoint = os.getenv("TENCENTCLOUD_ENDPOINT", None)
    if endpoint is None:
        return None
    client_profile = ClientProfile()
    client_profile.httpProfile.endpoint = endpoint
    return client_profile


def _parse_page_token(page_token: str) -> Dict:
    decoded_token = base64.b64decode(page_token)
    parsed_token = json.loads(decoded_token)
    return parsed_token


def _create_page_token(offset: int, search_id: str) -> str:
    return base64.b64encode(json.dumps({"offset": offset, "search_id": search_id}).encode("utf-8"))


# ============================================================================
# TCLakeStore 类
# ============================================================================

class TCLakeStore(AbstractStore):
    """
    TencentCloud Catalog 模型注册存储

    实现 MLflow AbstractStore 接口，将模型注册到腾讯云 Catalog。
    """

    def __init__(self, store_uri: str = None, tracking_uri: str = None):
        super().__init__(store_uri, tracking_uri)
        _log_msg(f"initializing tencent tclake client {store_uri} {tracking_uri}")

        sid = os.getenv("TENCENTCLOUD_SECRET_ID", "")
        if len(sid) == 0:
            raise MlflowException("TENCENTCLOUD_SECRET_ID is not set")
        sk = os.getenv("TENCENTCLOUD_SECRET_KEY", "")
        if len(sk) == 0:
            raise MlflowException("TENCENTCLOUD_SECRET_KEY is not set")

        token = os.getenv("TENCENTCLOUD_TOKEN", None)
        client_profile = _get_tencent_cloud_client_profile()
        cred = credential.Credential(sid, sk, token)

        # 解析 region: store_uri 格式为 "tclake:{region}"
        if store_uri:
            parts = store_uri.split(":")
            if len(parts) < 2:
                raise MlflowException("set store_uri tclake:{region}")
            region = parts[1]
        else:
            region = "ap-beijing"

        self.client = CommonClient("tccatalog", "2024-10-24", cred, region, client_profile)
        self.headers = _get_tencent_cloud_headers()
        self.default_catalog_name = os.getenv("TENCENTCLOUD_DEFAULT_CATALOG_NAME", "default")
        self.default_schema_name = os.getenv("TENCENTCLOUD_DEFAULT_SCHEMA_NAME", "default")
        self.project_id = os.getenv("WEDATA_PROJECT_ID", "")

        cache_size = int(os.getenv("TCLAKE_CACHE_SIZE", "100"))
        cache_ttl = int(os.getenv("TCLAKE_CACHE_TTL_SECS", "300"))
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)

        _log_msg(f"initialized tencent tclake client successfully {region} {client_profile} "
                 f"{self.headers} {cache_size} {cache_ttl}")

    def _split_model_name(self, name: str) -> List[str]:
        """
        解析模型名称为 [catalog, schema, model] 三部分

        支持格式：
        - "model_name" -> [default_catalog, default_schema, model_name]
        - "schema.model_name" -> [default_catalog, schema, model_name]
        - "catalog.schema.model_name" -> [catalog, schema, model_name]
        """
        parts = name.split(".")
        if len(parts) == 1:
            return [self.default_catalog_name, self.default_schema_name, parts[0]]
        if len(parts) == 2:
            return [self.default_catalog_name, parts[0], parts[1]]
        if len(parts) == 3:
            return parts
        raise MlflowException(f"invalid model name: {name}, must be catalog.schema.model")

    def _call(self, action: str, req: Dict) -> Dict:
        """调用腾讯云 API"""
        _log_msg(f"req: {action}\n{json.dumps(req, indent=2)}")
        body = self.client.call(action, req, headers=self.headers)
        body_obj = json.loads(body)
        _log_msg(f"body: {action}\n{json.dumps(body_obj, indent=2)}")
        resp = body_obj["Response"]
        return resp


    def _get_model_version_numbers(self, name: str) -> List[int]:
        """获取模型的所有版本号"""
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DescribeModelVersionNumbers", req_body)
        return resp["Versions"]

    def _get_model_version_by_alias(self, name: str, alias: str) -> Optional[ModelVersion]:
        """通过别名获取模型版本"""
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersions": self._get_model_version_numbers(name)
        }
        resp = self._call("DescribeModelVersions", req_body)
        model_version = None
        for mv in resp["ModelVersions"]:
            if alias in mv["Aliases"]:
                model_version = mv
                break
        if model_version is None:
            return None
        return _make_model_version(model_version, name)

    def create_registered_model(self, name: str, tags=None, description: str = None) -> RegisteredModel:
        """创建注册模型"""
        _log_msg(f"create_registered_model {name} {tags} {description}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        properties = []
        _add_tags_to_properties(tags, properties)
        _add_project_id_to_properties(self.project_id, properties)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "Comment": description if description else "",
            "Properties": properties
        }

        try:
            resp = self._call("CreateModel", req_body)
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                if e.code == "FailedOperation.MetalakeAlreadyExistsError":
                    raise MlflowException(
                        f"Registered Model (name={name}) already exists.",
                        RESOURCE_ALREADY_EXISTS,
                    )
            raise
        return _make_model(resp["Model"])

    def update_registered_model(self, name: str, description: str) -> RegisteredModel:
        """更新注册模型描述"""
        _log_msg(f"update_register_model {name} {description}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "NewComment": description if description else ""
        }
        resp = self._call("ModifyModelComment", req_body)
        return _make_model(resp["Model"])

    def rename_registered_model(self, name: str, new_name: str) -> RegisteredModel:
        """重命名注册模型"""
        _log_msg(f"rename_register_model {name} {new_name}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "NewName": new_name
        }
        resp = self._call("ModifyModelName", req_body)
        return _make_model(resp["Model"])

    def delete_registered_model(self, name: str) -> None:
        """删除注册模型"""
        _log_msg(f"delete_register_model {name}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DropModel", req_body)
        if not resp["Dropped"]:
            raise MlflowException(f"Failed to delete model {name}")

    def get_registered_model(self, name: str) -> RegisteredModel:
        """获取注册模型"""
        _log_msg(f"get_registered_model {name}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DescribeModel", req)
        return _make_model(resp["Model"])

    def get_latest_versions(self, name: str, stages=None) -> List[ModelVersion]:
        """获取最新版本"""
        _log_msg(f"get_latest_versions {name} {stages}")
        if stages is not None:
            raise NotImplementedError("Method not support stages")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
        }
        resp = self._call("DescribeModelVersions", req)
        return [_make_model_version(mv, name) for mv in resp["ModelVersions"]]

    def set_registered_model_tag(self, name: str, tag) -> None:
        """设置模型 tag"""
        _log_msg(f"set_registered_model_tag {name} {tag}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "Properties": _add_tag_to_properties(tag)
        }
        self._call("ModifyModelProperties", req)

    def delete_registered_model_tag(self, name: str, key: str) -> None:
        """删除模型 tag"""
        _log_msg(f"delete_registered_model_tag {name} {key}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "RemovedKeys": [_append_tag_key_prefix(key)]
        }
        self._call("ModifyModelProperties", req)


    def create_model_version(
        self,
        name: str,
        source: str,
        run_id: str = None,
        tags=None,
        run_link: str = None,
        description: str = None,
        local_model_path: str = None,
    ) -> ModelVersion:
        """创建模型版本"""
        _log_msg(f"create_model_version {name} {source} {run_id} {tags} {run_link} {description} {local_model_path}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        version_alias = str(uuid.uuid4())
        properties = []
        _add_tags_to_properties(tags, properties)
        _set_run_id_to_properties(run_id, properties)
        _set_run_link_to_properties(run_link, properties)
        _add_model_signature_to_properties(source, properties)
        _add_project_id_to_properties(self.project_id, properties)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "Uri": source,
            "Comment": description if description else "",
            "Properties": properties,
            "Aliases": [version_alias]
        }
        self._call("CreateModelVersion", req_body)
        return self._get_model_version_by_alias(name, version_alias)

    def update_model_version(self, name: str, version: str, description: str) -> ModelVersion:
        """更新模型版本描述"""
        _log_msg(f"update_model_version {name} {version} {description}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": _set_model_version(version),
            "NewComment": description if description else ""
        }
        resp = self._call("ModifyModelVersionComment", req_body)
        return _make_model_version(resp["ModelVersion"], name)

    def transition_model_version_stage(self, name, version, stage, archive_existing_versions):
        raise NotImplementedError("Method not implemented")

    def delete_model_version(self, name: str, version: str) -> None:
        """删除模型版本"""
        _log_msg(f"delete_model_version {name} {version}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": _set_model_version(version),
        }
        resp = self._call("DropModelVersion", req_body)
        if not resp["Dropped"]:
            raise Exception(f"Failed to delete model version {name} {version}")

    def get_model_version(self, name: str, version: str) -> ModelVersion:
        """获取模型版本"""
        _log_msg(f"get_model_version {name} {version}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req_body = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": _set_model_version(version),
        }
        resp = self._call("DescribeModelVersion", req_body)
        return _make_model_version(resp["ModelVersion"], name)

    def _fetch_all_models(self) -> List[RegisteredModel]:
        """获取所有模型"""
        req_body = {
            "Offset": 0,
            "Limit": 200,
            "SnapshotBased": True,
            "SnapshotId": ""
        }
        resp = self._call("SearchModels", req_body)
        total = resp['TotalCount']
        model_list = resp['Models']
        while len(model_list) < total:
            time.sleep(0.05)
            req_body["Offset"] += req_body["Limit"]
            req_body["SnapshotId"] = resp["SnapshotId"]
            resp = self._call("SearchModels", req_body)
            model_list.extend(resp['Models'])
            if len(resp['Models']) < req_body["Limit"]:
                break
        return [_make_model(model) for model in model_list]

    def _fetch_all_model_versions(self) -> List[ModelVersion]:
        """获取所有模型版本"""
        req_body = {
            "Offset": 0,
            "Limit": 200,
            "SnapshotBased": True,
            "SnapshotId": ""
        }
        resp = self._call("SearchModelVersions", req_body)
        total = resp['TotalCount']
        model_version_list = resp['ModelVersions']
        while len(model_version_list) < total:
            time.sleep(0.05)
            req_body["Offset"] += req_body["Limit"]
            req_body["SnapshotId"] = resp["SnapshotId"]
            resp = self._call("SearchModelVersions", req_body)
            model_version_list.extend(resp['ModelVersions'])
            if len(resp['ModelVersions']) < req_body["Limit"]:
                break
        return [
            _make_model_version(mv, _get_model_version_name(mv))
            for mv in model_version_list
        ]

    def search_registered_models(
        self, filter_string=None, max_results=None, order_by=None, page_token=None
    ) -> PagedList:
        """搜索注册模型"""
        _log_msg(f"search_registered_models {filter_string} {max_results} {order_by} {page_token}")
        if not isinstance(max_results, int) or max_results < 1:
            raise MlflowException(
                f"Invalid value for max_results. It must be a positive integer, but got {max_results}",
                INVALID_PARAMETER_VALUE,
            )

        if max_results > SEARCH_REGISTERED_MODEL_MAX_RESULTS_THRESHOLD:
            raise MlflowException(
                f"Invalid value for request parameter max_results. It must be at most "
                f"{SEARCH_REGISTERED_MODEL_MAX_RESULTS_THRESHOLD}, but got value {max_results}",
                INVALID_PARAMETER_VALUE,
            )
        if page_token is None:
            registered_models = self._fetch_all_models()
            filtered_rms = SearchModelUtils.filter(registered_models, filter_string)
            sorted_rms = SearchModelUtils.sort(filtered_rms, order_by)
            if len(sorted_rms) == 0:
                return PagedList([], None)
            search_id = "model_" + str(uuid.uuid4())
            page_token = _create_page_token(0, search_id)
            self.cache[search_id] = sorted_rms
            _log_msg(f"search_registered_models add cache {filter_string} {max_results} "
                     f"{order_by} {page_token} {search_id} {len(sorted_rms)}")
        return self._get_page_list(page_token, max_results)

    def search_model_versions(
        self, filter_string=None, max_results=None, order_by=None, page_token=None
    ) -> PagedList:
        """搜索模型版本"""
        _log_msg(f"search_model_versions {filter_string} {max_results} {order_by} {page_token}")
        if not isinstance(max_results, int) or max_results < 1:
            raise MlflowException(
                f"Invalid value for max_results. It must be a positive integer, but got {max_results}",
                INVALID_PARAMETER_VALUE,
            )

        if max_results > SEARCH_MODEL_VERSION_MAX_RESULTS_THRESHOLD:
            raise MlflowException(
                f"Invalid value for request parameter max_results. It must be at most "
                f"{SEARCH_MODEL_VERSION_MAX_RESULTS_THRESHOLD}, but got value {max_results}",
                INVALID_PARAMETER_VALUE,
            )
        if page_token is None:
            model_versions = self._fetch_all_model_versions()
            filtered_mvs = SearchModelVersionUtils.filter(model_versions, filter_string)
            sorted_mvs = SearchModelVersionUtils.sort(
                filtered_mvs,
                order_by or ["last_updated_timestamp DESC", "name ASC", "version_number DESC"],
            )
            if len(sorted_mvs) == 0:
                return PagedList([], None)
            search_id = "model_version_" + str(uuid.uuid4())
            page_token = _create_page_token(0, search_id)
            self.cache[search_id] = sorted_mvs
            _log_msg(f"search_model_versions add cache {filter_string} {max_results} "
                     f"{order_by} {page_token} {search_id} {len(sorted_mvs)}")

        return self._get_page_list(page_token, max_results)

    def _get_page_list(self, page_token, max_results) -> PagedList:
        """获取分页列表"""
        token_info = _parse_page_token(page_token)
        _log_msg(f"_get_page_list token_info {page_token} {max_results} {token_info}")
        sorted_mvs = self.cache.get(token_info['search_id'])
        if sorted_mvs is None:
            raise MlflowException(
                "Invalid page token: search id not found or expired",
                INVALID_PARAMETER_VALUE,
            )
        start_offset = token_info['offset']
        final_offset = start_offset + max_results

        paginated_rms = sorted_mvs[start_offset: min(len(sorted_mvs), final_offset)]
        next_page_token = None
        if final_offset < len(sorted_mvs):
            next_page_token = _create_page_token(final_offset, token_info['search_id'])
        else:
            self.cache.pop(token_info['search_id'], None)
            _log_msg(f"pop cache {token_info['search_id']} {start_offset} {final_offset} "
                     f"{len(sorted_mvs)} {page_token} {next_page_token}")
        return PagedList(paginated_rms, next_page_token)

    def set_model_version_tag(self, name: str, version: str, tag) -> None:
        """设置模型版本 tag"""
        _log_msg(f"set_model_version_tag {name} {version} {tag}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": _set_model_version(version),
            "Properties": _add_tag_to_properties(tag)
        }
        self._call("ModifyModelVersionProperties", req)

    def delete_model_version_tag(self, name: str, version: str, key: str) -> None:
        """删除模型版本 tag"""
        _log_msg(f"delete_model_version_tag {name} {version} {key}")
        [catalog_name, schema_name, model_name] = self._split_model_name(name)
        req = {
            "CatalogName": catalog_name,
            "SchemaName": schema_name,
            "ModelName": model_name,
            "ModelVersion": _set_model_version(version),
            "RemovedKeys": [_append_tag_key_prefix(key)]
        }
        self._call("ModifyModelVersionProperties", req)

    def set_registered_model_alias(self, name, alias, version):
        raise NotImplementedError("Method not implemented")

    def delete_registered_model_alias(self, name, alias):
        raise NotImplementedError("Method not implemented")

    def get_model_version_by_alias(self, name: str, alias: str) -> Optional[ModelVersion]:
        """通过别名获取模型版本"""
        _log_msg(f"get_model_version_by_alias {name} {alias}")
        return self._get_model_version_by_alias(name, alias)

    def get_model_version_download_uri(self, name: str, version: str) -> str:
        """获取模型版本下载 URI"""
        _log_msg(f"get_model_version_download_uri {name} {version}")
        model_version = self.get_model_version(name, version)
        return model_version.source
