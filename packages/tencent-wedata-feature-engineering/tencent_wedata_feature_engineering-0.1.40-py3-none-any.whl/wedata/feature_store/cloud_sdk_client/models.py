
from tencentcloud.common.abstract_model import AbstractModel
import typing
import warnings
from wedata.feature_store.cloud_sdk_client.utils import is_warning


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
