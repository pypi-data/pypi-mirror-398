import json

from tencentcloud.wedata.v20210820.wedata_client import WedataClient
from tencentcloud.wedata.v20250806.wedata_client import WedataClient as WedataClientV2
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from wedata_automl.utils.cloud_sdk_client.utils import get_client_profile, set_request_header, is_mock
import wedata_automl.utils.cloud_sdk_client.models as models
from wedata_automl.utils.log.logger import get_logger


class FeatureCloudSDK:
    def __init__(self, secret_id: str, secret_key: str, region: str, token=None):
        self._client = WedataClient(credential.Credential(secret_id, secret_key, token=token), region, get_client_profile())
        self._client_v2 = WedataClientV2(credential.Credential(secret_id, secret_key, token=token), region, get_client_profile())

    def CreateOnlineFeatureTable(self, request: models.CreateOnlineFeatureTableRequest) -> 'models.CreateOnlineFeatureTableResponse':
        """
        创建在线特征表
        Args:
            request: 创建请求参数

        Returns:
            创建结果响应
        """
        logger = get_logger()
        if is_mock():
            logger.debug("Mock CreateOnlineFeatureTable API")
            return models.CreateOnlineFeatureTableResponse()
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            logger.debug(f"CreateOnlineFeatureTable params: {params}")
            logger.debug(f"CreateOnlineFeatureTable headers: {headers}")
            self._client._apiVersion = "2021-08-20"
            body = self._client.call("CreateOnlineFeatureTable", params, headers=headers)
            response = json.loads(body)
            model = models.CreateOnlineFeatureTableResponse()
            model._deserialize(response["Response"])
            logger.debug(f"CreateOnlineFeatureTable Response: {response}")
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def DescribeNormalSchedulerExecutorGroups(self, request: models.DescribeNormalSchedulerExecutorGroupsRequest) -> 'models.DescribeNormalSchedulerExecutorGroupsResponse':
        """
        查询普通调度器执行器组
        Args:
            request: 查询请求参数

        Returns:
            查询结果响应
        """
        logger = get_logger()
        if is_mock():
            logger.debug("Mock DescribeNormalSchedulerExecutorGroups API")
            return models.DescribeNormalSchedulerExecutorGroupsResponse()

        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            logger.debug(f"DescribeNormalSchedulerExecutorGroups params: {params}")
            logger.debug(f"DescribeNormalSchedulerExecutorGroups headers: {headers}")
            self._client._apiVersion = "2021-08-20"
            body = self._client.call("DescribeNormalSchedulerExecutorGroups", params, headers=headers)
            response = json.loads(body)
            model = models.DescribeNormalSchedulerExecutorGroupsResponse()
            model._deserialize(response["Response"])
            logger.debug(f"DescribeNormalSchedulerExecutorGroups Response: {response}")
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def RefreshFeatureTable(self, request: models.RefreshFeatureTableRequest) -> 'models.RefreshFeatureTableResponse':
        """
        刷新特征表
        Args:
            request: 刷新请求参数
        Returns:
            刷新结果响应
        """
        logger = get_logger()
        if is_mock():
            logger.debug("Mock RefreshFeatureTable API")
            return models.RefreshFeatureTableResponse()
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            logger.debug(f"RefreshFeatureTable params: {params}")
            logger.debug(f"RefreshFeatureTable headers: {headers}")
            self._client_v2._apiVersion = "2025-08-06"
            body = self._client_v2.call("RefreshFeatureTable", params, headers=headers)
            response = json.loads(body)
            model = models.RefreshFeatureTableResponse()
            model._deserialize(response["Response"])
            logger.debug(f"RefreshFeatureTable Response: {response}")
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def DescribeFeatureStoreDatabases(self, request: models.DescribeFeatureStoreDatabasesRequest) -> 'models.DescribeFeatureStoreDatabasesResponse':
        """
        查询特征库列表
        Args:
            request: 查询请求参数
        Returns:
            查询结果响应
        """
        logger = get_logger()
        if is_mock():
            logger.debug("Mock DescribeFeatureStoreDatabases API")
            return models.DescribeFeatureStoreDatabasesResponse()
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            logger.debug(f"DescribeFeatureStoreDatabases params: {params}")
            logger.debug(f"DescribeFeatureStoreDatabases headers: {headers}")
            self._client_v2._apiVersion = "2021-08-20"
            body = self._client_v2.call("DescribeFeatureStoreDatabases", params, headers=headers)
            response = json.loads(body)
            model = models.DescribeFeatureStoreDatabasesResponse()
            model._deserialize(response["Response"])
            logger.debug(f"DescribeFeatureStoreDatabases Response: {response}")
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def CreateExploreScriptByOwnerUin(self, request: models.CreateExploreScriptRequest) -> 'models.CreateExploreScriptResponse':
        """
        创建数据探索脚本（按 OwnerUin）
        Args:
            request: 创建请求参数
        Returns:
            创建结果响应
        """
        logger = get_logger()
        if is_mock():
            logger.debug("Mock CreateExploreScriptByOwnerUin API")
            return models.CreateExploreScriptResponse()
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            print(f"CreateExploreScriptByOwnerUin headers: {headers}")
            print(f"CreateExploreScriptByOwnerUin params: {params}")
            logger.debug(f"CreateExploreScriptByOwnerUin params: {params}")
            logger.debug(f"CreateExploreScriptByOwnerUin headers: {headers}")
            self._client._apiVersion = "2021-08-20"
            body = self._client.call("CreateExploreScriptByOwnerUin", params, headers=headers)
            response = json.loads(body)
            model = models.CreateExploreScriptResponse()
            model._deserialize(response["Response"])
            logger.debug(f"CreateExploreScriptByOwnerUin Response: {response}")
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def SaveExploreScriptContent(self, request: models.SaveExploreScriptContentRequest) -> 'models.SaveExploreScriptContentResponse':
        """
        保存数据探索脚本内容

        在调用 CreateExploreScript 创建脚本后，使用此方法保存脚本内容。
        返回的 VersionId 可与 ScriptId (FileId) 组合生成访问路径。

        Args:
            request: 保存请求参数
                - ProjectId: 项目ID
                - ScriptId: 脚本ID (CreateExploreScript返回的)
                - ScriptContent: 脚本内容 (notebook的JSON字符串)
                - ExtensionType: 扩展类型 (如 "code_studio")

        Returns:
            保存结果响应，包含 VersionId 等信息
        """
        logger = get_logger()
        if is_mock():
            logger.debug("Mock SaveExploreScriptContent API")
            return models.SaveExploreScriptContentResponse()
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            print(f"SaveExploreScriptContent headers: {headers}")
            print(f"SaveExploreScriptContent params: {params}")
            logger.debug(f"SaveExploreScriptContent params: {params}")
            logger.debug(f"SaveExploreScriptContent headers: {headers}")
            self._client._apiVersion = "2021-08-20"
            body = self._client.call("SaveExploreScriptContent", params, headers=headers)
            response = json.loads(body)
            model = models.SaveExploreScriptContentResponse()
            model._deserialize(response["Response"])
            logger.debug(f"SaveExploreScriptContent Response: {response}")
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))
