
from tencentcloud.common.abstract_model import AbstractModel
import typing
import warnings
from wedata_automl.utils.cloud_sdk_client.utils import is_warning


class OfflineFeatureConfiguration(AbstractModel):
    """
    创建在线表时的离线特征部分描述
    """

    def __init__(self):
        self._DatasourceName = None
        self._TableName = None
        self._DatasourceType = None
        self._PrimaryKeys = None
        self._TimestampColumn = None
        self._DatabaseName = None
        self._EngineName = None

    @property
    def DatasourceName(self):
        return self._DatasourceName

    @DatasourceName.setter
    def DatasourceName(self, DatasourceName):
        self._DatasourceName = DatasourceName

    @property
    def TableName(self):
        return self._TableName

    @TableName.setter
    def TableName(self, TableName):
        self._TableName = TableName

    @property
    def DatasourceType(self):
        return self._DatasourceType

    @DatasourceType.setter
    def DatasourceType(self, DatasourceType):
        self._DatasourceType = DatasourceType

    @property
    def PrimaryKeys(self):
        return self._PrimaryKeys

    @PrimaryKeys.setter
    def PrimaryKeys(self, PrimaryKeys):
        self._PrimaryKeys = PrimaryKeys

    @property
    def TimestampColumn(self):
        return self._TimestampColumn

    @TimestampColumn.setter
    def TimestampColumn(self, TimestampColumn):
        self._TimestampColumn = TimestampColumn

    @property
    def DatabaseName(self):
        return self._DatabaseName

    @DatabaseName.setter
    def DatabaseName(self, DatabaseName):
        self._DatabaseName = DatabaseName

    @property
    def EngineName(self):
        return self._EngineName

    @EngineName.setter
    def EngineName(self, EngineName):
        self._EngineName = EngineName

    def _deserialize(self, params):
        self._DatasourceName = params.get("DatasourceName")
        self._TableName = params.get("TableName")
        self._DatasourceType = params.get("DatasourceType")
        self._PrimaryKeys = params.get("PrimaryKeys")
        self._TimestampColumn = params.get("TimestampColumn")
        self._DatabaseName = params.get("DatabaseName")
        self._EngineName = params.get("EngineName")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            property_name = name[1:]
            if property_name in member_set:
                member_set.remove(property_name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class TaskSchedulerConfiguration(AbstractModel):
    """
    创建在线特征表时的调度信息描述
    CycleType: 调度周期类型
    ScheduleTimeZone: 调度时区
    StartTime: 调度开始时间
    EndTime: 调度结束时间
    ExecutionStartTime: 执行开始时间
    ExecutionEndTime: 执行结束时间
    RunPriority: 运行优先级
    CrontabExpression: cron表达式
    """

    def __init__(self):
        self._CycleType = None
        self._ScheduleTimeZone = None
        self._StartTime = None
        self._EndTime = None
        self._ExecutionStartTime = None
        self._ExecutionEndTime = None
        self._RunPriority = None
        self._CrontabExpression = None

    @property
    def CycleType(self):
        return self._CycleType

    @CycleType.setter
    def CycleType(self, CycleType):
        self._CycleType = CycleType

    @property
    def ScheduleTimeZone(self):
        return self._ScheduleTimeZone

    @ScheduleTimeZone.setter
    def ScheduleTimeZone(self, ScheduleTimeZone):
        self._ScheduleTimeZone = ScheduleTimeZone

    @property
    def StartTime(self):
        return self._StartTime

    @StartTime.setter
    def StartTime(self, StartTime):
        self._StartTime = StartTime

    @property
    def EndTime(self):
        return self._EndTime

    @EndTime.setter
    def EndTime(self, EndTime):
        self._EndTime = EndTime

    @property
    def ExecutionStartTime(self):
        return self._ExecutionStartTime

    @ExecutionStartTime.setter
    def ExecutionStartTime(self, ExecutionStartTime):
        self._ExecutionStartTime = ExecutionStartTime

    @property
    def ExecutionEndTime(self):
        return self._ExecutionEndTime

    @ExecutionEndTime.setter
    def ExecutionEndTime(self, ExecutionEndTime):
        self._ExecutionEndTime = ExecutionEndTime

    @property
    def RunPriority(self):
        return self._RunPriority

    @RunPriority.setter
    def RunPriority(self, RunPriority):
        self._RunPriority = RunPriority

    @property
    def CrontabExpression(self):
        return self._CrontabExpression

    @CrontabExpression.setter
    def CrontabExpression(self, CrontabExpression):
        self._CrontabExpression = CrontabExpression

    def _deserialize(self, params):
        self.CycleType = params.get("CycleType")
        self.ScheduleTimeZone = params.get("ScheduleTimeZone")
        self.StartTime = params.get("StartTime")
        self.EndTime = params.get("EndTime")
        self.ExecutionStartTime = params.get("ExecutionStartTime")
        self.ExecutionEndTime = params.get("ExecutionEndTime")
        self.RunPriority = params.get("RunPriority")
        self.CrontabExpression = params.get("CrontabExpression")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            property_name = name[1:]
            if property_name in member_set:
                member_set.remove(property_name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class OnlineFeatureConfiguration(AbstractModel):
    """
    在线特征信息
    """

    def __init__(self):
        self._UseDefault = None
        self._DatasourceName = None
        self._DB = None
        self._Host = None
        self._Port = None

    @property
    def UserDefault(self):
        return self._UseDefault

    @UserDefault.setter
    def UserDefault(self, UseDefault):
        self._UseDefault = UseDefault

    @property
    def DataSourceName(self):
        return self._DataSourceName

    @DataSourceName.setter
    def DataSourceName(self, DataSourceName):
        self._DataSourceName = DataSourceName

    @property
    def DB(self):
        return self._DB

    @DB.setter
    def DB(self, DB):
        self._DB = DB

    @property
    def Host(self):
        return self._Host

    @Host.setter
    def Host(self, Host: str):
        self._Host = Host

    @property
    def Port(self):
        return self._Port

    @Port.setter
    def Port(self, Port: int):
        self._Port = Port

    def _deserialize(self, params):
        self.UseDefault = params.get("UseDefault")
        self.DataSourceName = params.get("DataSourceName")
        self.DB = params.get("DB")
        self.Host = params.get("Host")
        self.Port = params.get("Port")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            property_name = name[1:]
            if property_name in member_set:
                member_set.remove(property_name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class CreateOnlineFeatureTableRequest(AbstractModel):
    """
    创建在线特征表
    ProjectId
    ResourceGroupId
    OfflineFeatureConfiguration
    TaskSchedulerConfiguration
    OnlineFeatureConfiguration
    RequestFromSource
    """

    def __init__(self):
        self._ProjectId = None
        self._ResourceGroupId = None
        self._OfflineFeatureConfiguration = None
        self._TaskSchedulerConfiguration = None
        self._OnlineFeatureConfiguration = None
        self._RequestSource = None

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    @property
    def ResourceGroupId(self):
        return self._ResourceGroupId

    @ResourceGroupId.setter
    def ResourceGroupId(self, ResourceGroupId):
        self._ResourceGroupId = ResourceGroupId

    @property
    def OfflineFeatureConfiguration(self):
        return self._OfflineFeatureConfiguration

    @OfflineFeatureConfiguration.setter
    def OfflineFeatureConfiguration(self, OfflineFeatureConfiguration):
        self._OfflineFeatureConfiguration = OfflineFeatureConfiguration

    @property
    def TaskSchedulerConfiguration(self):
        return self._TaskSchedulerConfiguration

    @TaskSchedulerConfiguration.setter
    def TaskSchedulerConfiguration(self, TaskSchedulerConfiguration):
        self._TaskSchedulerConfiguration = TaskSchedulerConfiguration

    @property
    def OnlineFeatureConfiguration(self):
        return self._OnlineFeatureConfiguration

    @OnlineFeatureConfiguration.setter
    def OnlineFeatureConfiguration(self, OnlineFeatureConfiguration):
        self._OnlineFeatureConfiguration = OnlineFeatureConfiguration

    def _deserialize(self, params):
        self.ProjectId = params.get("ProjectId")
        self.ResourceGroupId = params.get("ResourceGroupId")
        if params.get("OfflineFeatureConfiguration") is not None:
            self.OfflineFeatureConfiguration = OfflineFeatureConfiguration()
            self.OfflineFeatureConfiguration._deserialize(params.get("OfflineFeatureConfiguration"))
        if params.get("TaskSchedulerConfiguration") is not None:
            self.TaskSchedulerConfiguration = TaskSchedulerConfiguration()
            self.TaskSchedulerConfiguration._deserialize(params.get("TaskSchedulerConfiguration"))
        if params.get("OnlineFeatureConfiguration") is not None:
            self._OnlineFeatureConfiguration = OnlineFeatureConfiguration()
            self._OnlineFeatureConfiguration._deserialize(params.get("OnlineFeatureConfiguration"))
        member_set = set(params.keys())
        for name, value in vars(self).items():
            property_name = name[1:]
            if property_name in member_set:
                member_set.remove(property_name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class CreateOnlineFeatureTableRsp(AbstractModel):
    """
    创建在线特征表返回包
    """

    def __init__(self):
        self._OfflineTableId = None
        self._OnlineTableId = None

    @property
    def OfflineTableId(self):
        return self._OfflineTableId

    @OfflineTableId.setter
    def OfflineTableId(self, OfflineTableId):
        self._OfflineTableId = OfflineTableId

    @property
    def OnlineTableId(self):
        return self._OnlineTableId

    @OnlineTableId.setter
    def OnlineTableId(self, OnlineTableId):
        self._OnlineTableId = OnlineTableId

    def _deserialize(self, params):
        self._OfflineTableId = params.get("OfflineTableId")
        self._OnlineTableId = params.get("OnlineTableId")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            property_name = name[1:]
            if property_name in member_set:
                member_set.remove(property_name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class CreateOnlineFeatureTableResponse(AbstractModel):
    """
    创建在线特征表返回包
    """

    def __init__(self):
        self._Data = None

    @property
    def Data(self) -> CreateOnlineFeatureTableRsp:
        return self._Data

    @Data.setter
    def Data(self, Data):
        self._Data = Data

    def _deserialize(self, params):
        self.Data = CreateOnlineFeatureTableRsp()
        self.Data._deserialize(params.get("Data"))
        member_set = set(params.keys())
        for name, value in vars(self).items():
            property_name = name[1:]
            if property_name in member_set:
                member_set.remove(property_name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class DescribeNormalSchedulerExecutorGroupsData(AbstractModel):
    """
    执行资源组管理-可用的调度资源组列表
    ExecutorGroupId
    ExecutorGroupName
    ExecutorGroupDesc
    Available
    PythonSubVersions
    EnvJson
    """

    def __init__(self):
        self._ExecutorGroupId = None
        self._ExecutorGroupName = None
        self._ExecutorGroupDesc = None
        self._Available = None
        self._PythonSubVersions = None
        self._EnvJson = None

    @property
    def ExecutorGroupId(self):
        return self._ExecutorGroupId

    @ExecutorGroupId.setter
    def ExecutorGroupId(self, ExecutorGroupId):
        self._ExecutorGroupId = ExecutorGroupId

    @property
    def ExecutorGroupName(self):
        return self._ExecutorGroupName

    @ExecutorGroupName.setter
    def ExecutorGroupName(self, ExecutorGroupName):
        self._ExecutorGroupName = ExecutorGroupName

    @property
    def ExecutorGroupDesc(self):
        return self._ExecutorGroupDesc

    @ExecutorGroupDesc.setter
    def ExecutorGroupDesc(self, ExecutorGroupDesc):
        self._ExecutorGroupDesc = ExecutorGroupDesc

    @property
    def Available(self):
        return self._Available

    @Available.setter
    def Available(self, Available):
        self._Available = Available

    @property
    def PythonSubVersions(self):
        return self._PythonSubVersions

    @PythonSubVersions.setter
    def PythonSubVersions(self, PythonSubVersions):
        self._PythonSubVersions = PythonSubVersions

    @property
    def EnvJson(self):
        return self._EnvJson

    @EnvJson.setter
    def EnvJson(self, EnvJson):
        self._EnvJson = EnvJson

    def _deserialize(self, params):
        self._ExecutorGroupId = params.get("ExecutorGroupId")
        self._ExecutorGroupName = params.get("ExecutorGroupName")
        self._ExecutorGroupDesc = params.get("ExecutorGroupDesc")
        self._Available = params.get("Available")
        self._PythonSubVersions = params.get("PythonSubVersions")
        self._EnvJson = params.get("EnvJson")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class DescribeNormalSchedulerExecutorGroupsResponse(AbstractModel):
    """
    查询可用的调度执行资源
    """

    def __init__(self):
        self._Data = None

    @property
    def Data(self) -> list[DescribeNormalSchedulerExecutorGroupsData]:
        return self._Data

    @Data.setter
    def Data(self, Data):
        self._Data = Data

    def _deserialize(self, params):
        if params.get("Data") is not None:
            self._Data = []
            for item in params.get("Data", []):
                obj = DescribeNormalSchedulerExecutorGroupsData()
                obj._deserialize(item)
                self._Data.append(obj)
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class DescribeNormalSchedulerExecutorGroupsRequest(AbstractModel):
    """
    查询可用的调度执行资源
    """

    def __init__(self):
        self._ProjectId = None
        self._OnlyAvailable = None

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId: str):
        self._ProjectId = ProjectId

    @property
    def OnlyAvailable(self):
        return self._OnlyAvailable

    @OnlyAvailable.setter
    def OnlyAvailable(self, OnlyAvailable: bool):
        self._OnlyAvailable = OnlyAvailable

    def _deserialize(self, params):
        self._ProjectId = params.get("ProjectId")
        self._OnlyAvailable = params.get("OnlyAvailable")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class RefreshFeatureTableRequest(AbstractModel):
    """
    刷新特征表
    Property:
        ProjectId: 项目ID
        ActionName: 行为:Create-创建;Delete-删除
        DatabaseName: 特征库名称
        TableName: 特征表名称
        DatasourceName: 数据源名称
        DatasourceType: 数据源类型: EMR/DLC
        EngineName: 引擎名称
        IsTry: 是否尝试操作
    """
    def __init__(self):
        self._ProjectId = None
        self._ActionName = None
        self._DatabaseName = None
        self._TableName = None
        self._DatasourceName = None
        self._DatasourceType = None
        self._EngineName = None
        self._IsTry = None

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    @property
    def ActionName(self):
        return self._ActionName

    @ActionName.setter
    def ActionName(self, ActionName):
        self._ActionName = ActionName

    @property
    def DatabaseName(self):
        return self._DatabaseName

    @DatabaseName.setter
    def DatabaseName(self, DatabaseName):
        self._DatabaseName = DatabaseName

    @property
    def TableName(self):
        return self._TableName

    @TableName.setter
    def TableName(self, TableName):
        self._TableName = TableName

    @property
    def DatasourceName(self):
        return self._DatasourceName

    @DatasourceName.setter
    def DatasourceName(self, DatasourceName):
        self._DatasourceName = DatasourceName

    @property
    def DatasourceType(self):
        return self._DatasourceType

    @DatasourceType.setter
    def DatasourceType(self, DatasourceType):
        self._DatasourceType = DatasourceType

    @property
    def EngineName(self):
        return self._EngineName

    @EngineName.setter
    def EngineName(self, EngineName):
        self._EngineName = EngineName

    @property
    def IsTry(self):
        return self._IsTry

    @IsTry.setter
    def IsTry(self, IsTry):
        self._IsTry = IsTry

    def _deserialize(self, params):
        self._ProjectId = params.get("ProjectId")
        self._ActionName = params.get("ActionName")
        self._DatabaseName = params.get("DatabaseName")
        self._TableName = params.get("TableName")
        self._DatasourceName = params.get("DatasourceName")
        self._DatasourceType = params.get("DatasourceType")
        self._EngineName = params.get("EngineName")
        self._IsTry = params.get("IsTry")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class RefreshFeatureTableResponse(AbstractModel):
    """
    刷新特征表
    Property:
        Data: 结果
    """
    def __init__(self):
        self._Data = None

    @property
    def Data(self):
        return self._Data

    @Data.setter
    def Data(self, Data):
        self._Data = Data

    def _deserialize(self, params):
        self._Data = params.get("Data")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class FeatureStoreDatabase(AbstractModel):
    """
    特征存储库
    Property:
        DatabaseName: 特征库名称
        DatasourceType：数据源类型: EMR/DLC
        EngineName: 引擎名称
        ProjectId: 项目ID
        IsDefault: 是否默认库
        IsExistDatabase: 是否存在库
        DatasourceId: 数据源ID
        OnlineMode: 在线模式: 0-离线; 1-在线
        DatasourceName: 数据源名称
    """
    def __init__(self):
        self._DatabaseName = None
        self._DatasourceType = None
        self._EngineName = None
        self._ProjectId = None
        self._IsDefault = None
        self._IsExistDatabase = None
        self._DatasourceId = None
        self._OnlineMode = None
        self._DatasourceName = None

    @property
    def DatabaseName(self):
        return self._DatabaseName

    @DatabaseName.setter
    def DatabaseName(self, DatabaseName):
        self._DatabaseName = DatabaseName

    @property
    def DatasourceType(self):
        return self._DatasourceType

    @DatasourceType.setter
    def DatasourceType(self, DatasourceType):
        self._DatasourceType = DatasourceType

    @property
    def EngineName(self):
        return self._EngineName

    @EngineName.setter
    def EngineName(self, EngineName):
        self._EngineName = EngineName

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    @property
    def IsDefault(self):
        return self._IsDefault

    @IsDefault.setter
    def IsDefault(self, IsDefault):
        self._IsDefault = IsDefault

    @property
    def IsExistDatabase(self):
        return self._IsExistDatabase

    @IsExistDatabase.setter
    def IsExistDatabase(self, IsExistDatabase):
        self._IsExistDatabase = IsExistDatabase

    @property
    def DatasourceId(self):
        return self._DatasourceId

    @DatasourceId.setter
    def DatasourceId(self, DatasourceId):
        self._DatasourceId = DatasourceId

    @property
    def OnlineMode(self):
        return self._OnlineMode

    @OnlineMode.setter
    def OnlineMode(self, OnlineMode):
        self._OnlineMode = OnlineMode

    @property
    def DatasourceName(self):
        return self._DatasourceName

    @DatasourceName.setter
    def DatasourceName(self, DatasourceName):
        self._DatasourceName = DatasourceName

    def _deserialize(self, params):
        self._DatabaseName = params.get("DatabaseName")
        self._DatasourceType = params.get("DatasourceType")
        self._EngineName = params.get("EngineName")
        self._ProjectId = params.get("ProjectId")
        self._IsDefault = params.get("IsDefault")
        self._IsExistDatabase = params.get("IsExistDatabase")
        self._DatasourceId = params.get("DatasourceId")
        self._OnlineMode = params.get("OnlineMode")
        self._DatasourceName = params.get("DatasourceName")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class DescribeFeatureStoreDatabasesResponse(AbstractModel):
    """
    描述特征库
    Property:
        Data: 结果
    """
    def __init__(self):
        self._Data = None

    @property
    def Data(self) -> typing.List[FeatureStoreDatabase]:
        return self._Data

    @Data.setter
    def Data(self, Data):
        self._Data = Data

    def _deserialize(self, params):
        self._Data = []
        for item in params.get("Data", []):
            obj = FeatureStoreDatabase()
            obj._deserialize(item)
            self._Data.append(obj)
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class DescribeFeatureStoreDatabasesRequest(AbstractModel):
    """
    Property:
       ProjectId: 项目ID
    """
    def __init__(self):
        self._ProjectId = None

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    def _deserialize(self, params):
        self._ProjectId = params.get("ProjectId")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class EngineClusterInfo(AbstractModel):
    """
    引擎集群信息
    Property:
        ClusterId: 引擎集群id
        ClusterName: 引擎集群名称
        ClusterType: 引擎类型
        ComputeResource: 计算资源
        DlcRoleArn: DLC spark作业引擎的role-arn
        Params: 引擎技术参数
        Region: 地域
        ResourceGroup: 资源组
    """
    def __init__(self):
        self._ClusterId = None
        self._ClusterName = None
        self._ClusterType = None
        self._ComputeResource = None
        self._DlcRoleArn = None
        self._Params = None
        self._Region = None
        self._ResourceGroup = None

    @property
    def ClusterId(self):
        return self._ClusterId

    @ClusterId.setter
    def ClusterId(self, ClusterId):
        self._ClusterId = ClusterId

    @property
    def ClusterName(self):
        return self._ClusterName

    @ClusterName.setter
    def ClusterName(self, ClusterName):
        self._ClusterName = ClusterName

    @property
    def ClusterType(self):
        return self._ClusterType

    @ClusterType.setter
    def ClusterType(self, ClusterType):
        self._ClusterType = ClusterType

    @property
    def ComputeResource(self):
        return self._ComputeResource

    @ComputeResource.setter
    def ComputeResource(self, ComputeResource):
        self._ComputeResource = ComputeResource

    @property
    def DlcRoleArn(self):
        return self._DlcRoleArn

    @DlcRoleArn.setter
    def DlcRoleArn(self, DlcRoleArn):
        self._DlcRoleArn = DlcRoleArn

    @property
    def Params(self):
        return self._Params

    @Params.setter
    def Params(self, Params):
        self._Params = Params

    @property
    def Region(self):
        return self._Region

    @Region.setter
    def Region(self, Region):
        self._Region = Region

    @property
    def ResourceGroup(self):
        return self._ResourceGroup

    @ResourceGroup.setter
    def ResourceGroup(self, ResourceGroup):
        self._ResourceGroup = ResourceGroup

    def _deserialize(self, params):
        self._ClusterId = params.get("ClusterId")
        self._ClusterName = params.get("ClusterName")
        self._ClusterType = params.get("ClusterType")
        self._ComputeResource = params.get("ComputeResource")
        self._DlcRoleArn = params.get("DlcRoleArn")
        self._Params = params.get("Params")
        self._Region = params.get("Region")
        self._ResourceGroup = params.get("ResourceGroup")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class ResourceSpecInfo(AbstractModel):
    """
    资源组规格参数信息
    Property:
        ExecutorSpec: Executor规格，例如2CU
        DriverSpec: Driver规格，例如2CU
        ExecutorNum: Executor数量
        ExecutorMinNum: Executor最小个数
        ExecutorMaxNum: Executor最大个数
    """
    def __init__(self):
        self._ExecutorSpec = None
        self._DriverSpec = None
        self._ExecutorNum = None
        self._ExecutorMinNum = None
        self._ExecutorMaxNum = None

    @property
    def ExecutorSpec(self):
        return self._ExecutorSpec

    @ExecutorSpec.setter
    def ExecutorSpec(self, ExecutorSpec):
        self._ExecutorSpec = ExecutorSpec

    @property
    def DriverSpec(self):
        return self._DriverSpec

    @DriverSpec.setter
    def DriverSpec(self, DriverSpec):
        self._DriverSpec = DriverSpec

    @property
    def ExecutorNum(self):
        return self._ExecutorNum

    @ExecutorNum.setter
    def ExecutorNum(self, ExecutorNum):
        self._ExecutorNum = ExecutorNum

    @property
    def ExecutorMinNum(self):
        return self._ExecutorMinNum

    @ExecutorMinNum.setter
    def ExecutorMinNum(self, ExecutorMinNum):
        self._ExecutorMinNum = ExecutorMinNum

    @property
    def ExecutorMaxNum(self):
        return self._ExecutorMaxNum

    @ExecutorMaxNum.setter
    def ExecutorMaxNum(self, ExecutorMaxNum):
        self._ExecutorMaxNum = ExecutorMaxNum

    def _deserialize(self, params):
        self._ExecutorSpec = params.get("ExecutorSpec")
        self._DriverSpec = params.get("DriverSpec")
        self._ExecutorNum = params.get("ExecutorNum")
        self._ExecutorMinNum = params.get("ExecutorMinNum")
        self._ExecutorMaxNum = params.get("ExecutorMaxNum")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class NotebookSessionInfo(AbstractModel):
    """
    Jupyter session信息
    Property:
        SessionId: 会话ID
        SessionName: 会话名称
        KernelId: 内核ID
        KernelName: 内核名称
        Path: 内核工作路径
    """
    def __init__(self):
        self._SessionId = None
        self._SessionName = None
        self._KernelId = None
        self._KernelName = None
        self._Path = None

    @property
    def SessionId(self):
        return self._SessionId

    @SessionId.setter
    def SessionId(self, SessionId):
        self._SessionId = SessionId

    @property
    def SessionName(self):
        return self._SessionName

    @SessionName.setter
    def SessionName(self, SessionName):
        self._SessionName = SessionName

    @property
    def KernelId(self):
        return self._KernelId

    @KernelId.setter
    def KernelId(self, KernelId):
        self._KernelId = KernelId

    @property
    def KernelName(self):
        return self._KernelName

    @KernelName.setter
    def KernelName(self, KernelName):
        self._KernelName = KernelName

    @property
    def Path(self):
        return self._Path

    @Path.setter
    def Path(self, Path):
        self._Path = Path

    def _deserialize(self, params):
        self._SessionId = params.get("SessionId")
        self._SessionName = params.get("SessionName")
        self._KernelId = params.get("KernelId")
        self._KernelName = params.get("KernelName")
        self._Path = params.get("Path")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class ExploreScriptConfig(AbstractModel):
    """
    数据探索脚本配置
    Property:
        DatasourceId: 数据源Id
        ComputeResource: 计算资源
        ExecutorGroupId: 执行资源组
        Params: 高级运行参数,变量替换，map-json String,String
        AdvanceConfig: 高级设置，执行配置参数，map-json String,String
        ExtraParams: 额外参数，map-json String,String
        DatasourceEnv: 数据源环境
        ClusterInfo: 引擎集群信息
        ResourceSpecInfo: 资源组规格参数信息
        NotebookSessionInfo: jupyter session信息
    """
    def __init__(self):
        self._DatasourceId = None
        self._ComputeResource = None
        self._ExecutorGroupId = None
        self._Params = None
        self._AdvanceConfig = None
        self._ExtraParams = None
        self._DatasourceEnv = None
        self._ClusterInfo = None
        self._ResourceSpecInfo = None
        self._NotebookSessionInfo = None

    @property
    def DatasourceId(self):
        return self._DatasourceId

    @DatasourceId.setter
    def DatasourceId(self, DatasourceId):
        self._DatasourceId = DatasourceId

    @property
    def ComputeResource(self):
        return self._ComputeResource

    @ComputeResource.setter
    def ComputeResource(self, ComputeResource):
        self._ComputeResource = ComputeResource

    @property
    def ExecutorGroupId(self):
        return self._ExecutorGroupId

    @ExecutorGroupId.setter
    def ExecutorGroupId(self, ExecutorGroupId):
        self._ExecutorGroupId = ExecutorGroupId

    @property
    def Params(self):
        return self._Params

    @Params.setter
    def Params(self, Params):
        self._Params = Params

    @property
    def AdvanceConfig(self):
        return self._AdvanceConfig

    @AdvanceConfig.setter
    def AdvanceConfig(self, AdvanceConfig):
        self._AdvanceConfig = AdvanceConfig

    @property
    def ExtraParams(self):
        return self._ExtraParams

    @ExtraParams.setter
    def ExtraParams(self, ExtraParams):
        self._ExtraParams = ExtraParams

    @property
    def DatasourceEnv(self):
        return self._DatasourceEnv

    @DatasourceEnv.setter
    def DatasourceEnv(self, DatasourceEnv):
        self._DatasourceEnv = DatasourceEnv

    @property
    def ClusterInfo(self):
        return self._ClusterInfo

    @ClusterInfo.setter
    def ClusterInfo(self, ClusterInfo):
        self._ClusterInfo = ClusterInfo

    @property
    def ResourceSpecInfo(self):
        return self._ResourceSpecInfo

    @ResourceSpecInfo.setter
    def ResourceSpecInfo(self, ResourceSpecInfo):
        self._ResourceSpecInfo = ResourceSpecInfo

    @property
    def NotebookSessionInfo(self):
        return self._NotebookSessionInfo

    @NotebookSessionInfo.setter
    def NotebookSessionInfo(self, NotebookSessionInfo):
        self._NotebookSessionInfo = NotebookSessionInfo

    def _deserialize(self, params):
        self._DatasourceId = params.get("DatasourceId")
        self._ComputeResource = params.get("ComputeResource")
        self._ExecutorGroupId = params.get("ExecutorGroupId")
        self._Params = params.get("Params")
        self._AdvanceConfig = params.get("AdvanceConfig")
        self._ExtraParams = params.get("ExtraParams")
        self._DatasourceEnv = params.get("DatasourceEnv")
        if params.get("ClusterInfo") is not None:
            self._ClusterInfo = EngineClusterInfo()
            self._ClusterInfo._deserialize(params.get("ClusterInfo"))
        if params.get("ResourceSpecInfo") is not None:
            self._ResourceSpecInfo = ResourceSpecInfo()
            self._ResourceSpecInfo._deserialize(params.get("ResourceSpecInfo"))
        if params.get("NotebookSessionInfo") is not None:
            self._NotebookSessionInfo = NotebookSessionInfo()
            self._NotebookSessionInfo._deserialize(params.get("NotebookSessionInfo"))
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class CreateExploreScriptRequest(AbstractModel):
    """
    创建数据探索脚本请求
    Property:
        ScriptName: 脚本名称
        ExtensionType: 脚本扩展类型 sql
        ParentFolderId: 父文件夹Id
        ScriptConfig: 数据探索脚本配置
        ScriptContent: 脚本内容
        ProjectId: 项目Id
        AccessScope: 权限范围：SHARED, PRIVATE
        WorkspaceMappingId: 工作空间映射id,脚本对应的notebook工作空间
        BundleId: 绑定的bundleId
        BundleInfo: 绑定的BundleInfo
    """
    def __init__(self):
        self._ScriptName = None
        self._ExtensionType = None
        self._ParentFolderId = None
        self._ScriptConfig = None
        self._ScriptContent = None
        self._ProjectId = None
        self._AccessScope = None
        self._WorkspaceMappingId = None
        self._BundleId = None
        self._BundleInfo = None

    @property
    def ScriptName(self):
        return self._ScriptName

    @ScriptName.setter
    def ScriptName(self, ScriptName):
        self._ScriptName = ScriptName

    @property
    def ExtensionType(self):
        return self._ExtensionType

    @ExtensionType.setter
    def ExtensionType(self, ExtensionType):
        self._ExtensionType = ExtensionType

    @property
    def ParentFolderId(self):
        return self._ParentFolderId

    @ParentFolderId.setter
    def ParentFolderId(self, ParentFolderId):
        self._ParentFolderId = ParentFolderId

    @property
    def ScriptConfig(self):
        return self._ScriptConfig

    @ScriptConfig.setter
    def ScriptConfig(self, ScriptConfig):
        self._ScriptConfig = ScriptConfig

    @property
    def ScriptContent(self):
        return self._ScriptContent

    @ScriptContent.setter
    def ScriptContent(self, ScriptContent):
        self._ScriptContent = ScriptContent

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    @property
    def AccessScope(self):
        return self._AccessScope

    @AccessScope.setter
    def AccessScope(self, AccessScope):
        self._AccessScope = AccessScope

    @property
    def WorkspaceMappingId(self):
        return self._WorkspaceMappingId

    @WorkspaceMappingId.setter
    def WorkspaceMappingId(self, WorkspaceMappingId):
        self._WorkspaceMappingId = WorkspaceMappingId

    @property
    def BundleId(self):
        return self._BundleId

    @BundleId.setter
    def BundleId(self, BundleId):
        self._BundleId = BundleId

    @property
    def BundleInfo(self):
        return self._BundleInfo

    @BundleInfo.setter
    def BundleInfo(self, BundleInfo):
        self._BundleInfo = BundleInfo

    def _deserialize(self, params):
        self._ScriptName = params.get("ScriptName")
        self._ExtensionType = params.get("ExtensionType")
        self._ParentFolderId = params.get("ParentFolderId")
        if params.get("ScriptConfig") is not None:
            self._ScriptConfig = ExploreScriptConfig()
            self._ScriptConfig._deserialize(params.get("ScriptConfig"))
        self._ScriptContent = params.get("ScriptContent")
        self._ProjectId = params.get("ProjectId")
        self._AccessScope = params.get("AccessScope")
        self._WorkspaceMappingId = params.get("WorkspaceMappingId")
        self._BundleId = params.get("BundleId")
        self._BundleInfo = params.get("BundleInfo")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class ExploreScript(AbstractModel):
    """
    数据探索脚本
    Property:
        ScriptId: 脚本id
        ScriptName: 脚本名称
        ScriptOwnerUin: 脚本所有者 uin
        ExtensionType: 脚本文件扩展类型
        ParentFolderId: 脚本所属文件夹Id
        ScriptConfig: 脚本配置
        ScriptContent: 脚本内容
        ScriptSource: 脚本数据来源db,cos
        Status: 脚本存续状态 active, deleted
        WorkspaceMappingId: 工作空间映射id,脚本对应的notebook工作空间
        NodeIdPath: id树,由各个节点的id组成
        UserUin: 最近一次操作人
        OwnerUin: 主账号人 uin
        AppId: 主账号app id
        ProjectId: 项目id
        UpdateTime: 更新时间 yyyy-MM-dd hh:mm:ss
        CreateTime: 创建时间 yyyy-MM-dd hh:mm:ss
        AccessScope: 权限范围：SHARED, PRIVATE
        NodePath: 节点全路径，由各个节点的名称组成
        BundleId: 绑定bundleId
        BundleInfo: 绑定的bundleInfo
        FileAbsolutePath: 脚本在工作空间中的绝对路径
        VersionId: 文件版本id
        VersionValue: 文件版本号
    """
    def __init__(self):
        self._ScriptId = None
        self._ScriptName = None
        self._ScriptOwnerUin = None
        self._ExtensionType = None
        self._ParentFolderId = None
        self._ScriptConfig = None
        self._ScriptContent = None
        self._ScriptSource = None
        self._Status = None
        self._WorkspaceMappingId = None
        self._NodeIdPath = None
        self._UserUin = None
        self._OwnerUin = None
        self._AppId = None
        self._ProjectId = None
        self._UpdateTime = None
        self._CreateTime = None
        self._AccessScope = None
        self._NodePath = None
        self._BundleId = None
        self._BundleInfo = None
        self._FileAbsolutePath = None
        self._VersionId = None
        self._VersionValue = None

    @property
    def ScriptId(self):
        return self._ScriptId

    @ScriptId.setter
    def ScriptId(self, ScriptId):
        self._ScriptId = ScriptId

    @property
    def ScriptName(self):
        return self._ScriptName

    @ScriptName.setter
    def ScriptName(self, ScriptName):
        self._ScriptName = ScriptName

    @property
    def ScriptOwnerUin(self):
        return self._ScriptOwnerUin

    @ScriptOwnerUin.setter
    def ScriptOwnerUin(self, ScriptOwnerUin):
        self._ScriptOwnerUin = ScriptOwnerUin

    @property
    def ExtensionType(self):
        return self._ExtensionType

    @ExtensionType.setter
    def ExtensionType(self, ExtensionType):
        self._ExtensionType = ExtensionType

    @property
    def ParentFolderId(self):
        return self._ParentFolderId

    @ParentFolderId.setter
    def ParentFolderId(self, ParentFolderId):
        self._ParentFolderId = ParentFolderId

    @property
    def ScriptConfig(self):
        return self._ScriptConfig

    @ScriptConfig.setter
    def ScriptConfig(self, ScriptConfig):
        self._ScriptConfig = ScriptConfig

    @property
    def ScriptContent(self):
        return self._ScriptContent

    @ScriptContent.setter
    def ScriptContent(self, ScriptContent):
        self._ScriptContent = ScriptContent

    @property
    def ScriptSource(self):
        return self._ScriptSource

    @ScriptSource.setter
    def ScriptSource(self, ScriptSource):
        self._ScriptSource = ScriptSource

    @property
    def Status(self):
        return self._Status

    @Status.setter
    def Status(self, Status):
        self._Status = Status

    @property
    def WorkspaceMappingId(self):
        return self._WorkspaceMappingId

    @WorkspaceMappingId.setter
    def WorkspaceMappingId(self, WorkspaceMappingId):
        self._WorkspaceMappingId = WorkspaceMappingId

    @property
    def NodeIdPath(self):
        return self._NodeIdPath

    @NodeIdPath.setter
    def NodeIdPath(self, NodeIdPath):
        self._NodeIdPath = NodeIdPath

    @property
    def UserUin(self):
        return self._UserUin

    @UserUin.setter
    def UserUin(self, UserUin):
        self._UserUin = UserUin

    @property
    def OwnerUin(self):
        return self._OwnerUin

    @OwnerUin.setter
    def OwnerUin(self, OwnerUin):
        self._OwnerUin = OwnerUin

    @property
    def AppId(self):
        return self._AppId

    @AppId.setter
    def AppId(self, AppId):
        self._AppId = AppId

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    @property
    def UpdateTime(self):
        return self._UpdateTime

    @UpdateTime.setter
    def UpdateTime(self, UpdateTime):
        self._UpdateTime = UpdateTime

    @property
    def CreateTime(self):
        return self._CreateTime

    @CreateTime.setter
    def CreateTime(self, CreateTime):
        self._CreateTime = CreateTime

    @property
    def AccessScope(self):
        return self._AccessScope

    @AccessScope.setter
    def AccessScope(self, AccessScope):
        self._AccessScope = AccessScope

    @property
    def NodePath(self):
        return self._NodePath

    @NodePath.setter
    def NodePath(self, NodePath):
        self._NodePath = NodePath

    @property
    def BundleId(self):
        return self._BundleId

    @BundleId.setter
    def BundleId(self, BundleId):
        self._BundleId = BundleId

    @property
    def BundleInfo(self):
        return self._BundleInfo

    @BundleInfo.setter
    def BundleInfo(self, BundleInfo):
        self._BundleInfo = BundleInfo

    @property
    def FileAbsolutePath(self):
        return self._FileAbsolutePath

    @FileAbsolutePath.setter
    def FileAbsolutePath(self, FileAbsolutePath):
        self._FileAbsolutePath = FileAbsolutePath

    @property
    def VersionId(self):
        return self._VersionId

    @VersionId.setter
    def VersionId(self, VersionId):
        self._VersionId = VersionId

    @property
    def VersionValue(self):
        return self._VersionValue

    @VersionValue.setter
    def VersionValue(self, VersionValue):
        self._VersionValue = VersionValue

    def _deserialize(self, params):
        self._ScriptId = params.get("ScriptId")
        self._ScriptName = params.get("ScriptName")
        self._ScriptOwnerUin = params.get("ScriptOwnerUin")
        self._ExtensionType = params.get("ExtensionType")
        self._ParentFolderId = params.get("ParentFolderId")
        if params.get("ScriptConfig") is not None:
            self._ScriptConfig = ExploreScriptConfig()
            self._ScriptConfig._deserialize(params.get("ScriptConfig"))
        self._ScriptContent = params.get("ScriptContent")
        self._ScriptSource = params.get("ScriptSource")
        self._Status = params.get("Status")
        self._WorkspaceMappingId = params.get("WorkspaceMappingId")
        self._NodeIdPath = params.get("NodeIdPath")
        self._UserUin = params.get("UserUin")
        self._OwnerUin = params.get("OwnerUin")
        self._AppId = params.get("AppId")
        self._ProjectId = params.get("ProjectId")
        self._UpdateTime = params.get("UpdateTime")
        self._CreateTime = params.get("CreateTime")
        self._AccessScope = params.get("AccessScope")
        self._NodePath = params.get("NodePath")
        self._BundleId = params.get("BundleId")
        self._BundleInfo = params.get("BundleInfo")
        self._FileAbsolutePath = params.get("FileAbsolutePath")
        self._VersionId = params.get("VersionId")
        self._VersionValue = params.get("VersionValue")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class CreateExploreScriptResponse(AbstractModel):
    """
    创建数据探索脚本响应
    Property:
        Data: 创建的脚本信息
    """
    def __init__(self):
        self._Data = None

    @property
    def Data(self) -> ExploreScript:
        return self._Data

    @Data.setter
    def Data(self, Data):
        self._Data = Data

    def _deserialize(self, params):
        if params.get("Data") is not None:
            self._Data = ExploreScript()
            self._Data._deserialize(params.get("Data"))
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))


class SaveExploreScriptContentRequest(AbstractModel):
    """
    保存数据探索脚本内容请求
    Property:
        ProjectId: 项目ID
        ScriptId: 脚本ID (CreateExploreScript返回的ScriptId)
        ScriptContent: 脚本内容 (notebook的JSON字符串)
        ExtensionType: 扩展类型 (如 "code_studio")
    """
    def __init__(self):
        self._ProjectId = None
        self._ScriptId = None
        self._ScriptContent = None
        self._ExtensionType = None

    @property
    def ProjectId(self):
        return self._ProjectId

    @ProjectId.setter
    def ProjectId(self, ProjectId):
        self._ProjectId = ProjectId

    @property
    def ScriptId(self):
        return self._ScriptId

    @ScriptId.setter
    def ScriptId(self, ScriptId):
        self._ScriptId = ScriptId

    @property
    def ScriptContent(self):
        return self._ScriptContent

    @ScriptContent.setter
    def ScriptContent(self, ScriptContent):
        self._ScriptContent = ScriptContent

    @property
    def ExtensionType(self):
        return self._ExtensionType

    @ExtensionType.setter
    def ExtensionType(self, ExtensionType):
        self._ExtensionType = ExtensionType

    def _serialize(self):
        params = {}
        if self._ProjectId is not None:
            params["ProjectId"] = self._ProjectId
        if self._ScriptId is not None:
            params["ScriptId"] = self._ScriptId
        if self._ScriptContent is not None:
            params["ScriptContent"] = self._ScriptContent
        if self._ExtensionType is not None:
            params["ExtensionType"] = self._ExtensionType
        return params


class SaveExploreScriptContentResponse(AbstractModel):
    """
    保存数据探索脚本内容响应
    Property:
        Data: 返回的脚本信息 (ExploreScript 结构)
        RequestId: 请求ID
    """
    def __init__(self):
        self._Data = None
        self._RequestId = None

    @property
    def Data(self) -> ExploreScript:
        return self._Data

    @Data.setter
    def Data(self, Data):
        self._Data = Data

    @property
    def RequestId(self):
        return self._RequestId

    @RequestId.setter
    def RequestId(self, RequestId):
        self._RequestId = RequestId

    def _deserialize(self, params):
        if params.get("Data") is not None:
            self._Data = ExploreScript()
            self._Data._deserialize(params.get("Data"))
        self._RequestId = params.get("RequestId")
        member_set = set(params.keys())
        for name, value in vars(self).items():
            if name in member_set:
                member_set.remove(name)
        if len(member_set) > 0 and is_warning():
            warnings.warn("%s fields are useless." % ",".join(member_set))
