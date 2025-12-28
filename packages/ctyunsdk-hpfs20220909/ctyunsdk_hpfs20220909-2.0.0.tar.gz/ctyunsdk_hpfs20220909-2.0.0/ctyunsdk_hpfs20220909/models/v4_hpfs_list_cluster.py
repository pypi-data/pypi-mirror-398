from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListClusterRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsType: Optional[str] = None  # 类型，hpfs_perf(HPC性能型)
    azName: Optional[str] = None  # 多可用区下的可用区名字
    ebmDeviceType: Optional[str] = None  # 裸金属设备规格
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListClusterResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListClusterReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListClusterReturnObj:
    clusterList: Optional[List['V4HpfsListClusterReturnObjClusterList']] = None  # 返回的集群列表
    totalCount: Optional[int] = None  # 某资源池指定条件下集群总数
    currentCount: Optional[int] = None  # 当前页码下查询回来的集群数
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)
    pageNo: Optional[int] = None  # 列表的分页页码


@dataclass_json
@dataclass
class V4HpfsListClusterReturnObjClusterList:
    clusterName: Optional[str] = None  # 集群名称
    remainingStatus: Optional[bool] = None  # 该集群是否可以售卖
    storageType: Optional[str] = None  # 集群的存储类型，包括hpfs_perf(HPC性能型)
    azName: Optional[str] = None  # 多可用区下的可用区名字
    protocolType: Optional[List[str]] = None  # 集群支持的协议列表，包括nfs、hpfs
    baselines: Optional[List[str]] = None  # 集群支持的性能基线列表（仅当资源池支持性能基线时返回）
    networkType: Optional[str] = None  # 集群的网络类型（tcp/o2ib）
    ebmDeviceTypes: Optional[List[str]] = None  # 集群支持的裸金属设备规格列表
    features: Optional[List[str]] = None  # 集群支持的功能，包括dataflow(数据流动)，protocolService（协议服务）,fileset(FILESET)
