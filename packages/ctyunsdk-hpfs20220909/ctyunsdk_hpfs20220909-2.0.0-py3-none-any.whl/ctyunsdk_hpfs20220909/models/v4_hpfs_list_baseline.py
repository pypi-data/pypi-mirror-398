from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListBaselineRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsType: str  # 类型，hpfs_perf(HPC性能型)
    azName: Optional[str] = None  # 多可用区下的可用区名字，4.0资源池必填
    clusterName: Optional[str] = None  # 集群名称
    pageNo: Optional[int] = None  # 列表的分页页码 ，默认值为1
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListBaselineResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListBaselineReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListBaselineReturnObj:
    baselineList: Optional[List['V4HpfsListBaselineReturnObjBaselineList']] = None  # 返回的性能基线列表
    totalCount: Optional[int] = None  # 指定条件下性能基线总数
    currentCount: Optional[int] = None  # 当前页码下查询回来的基线数
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)
    pageNo: Optional[int] = None  # 列表的分页页码


@dataclass_json
@dataclass
class V4HpfsListBaselineReturnObjBaselineList:
    baseline: Optional[str] = None  # 性能基线（MB/s/TB）
    storageType: Optional[str] = None  # 支持类型，hpfs_perf(HPC性能型)
    azName: Optional[str] = None  # 多可用区下可用区名称
    clusterNames: Optional[List[str]] = None  # 集群列表
