from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListZoneRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListZoneResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListZoneReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListZoneReturnObj:
    zoneList: Optional[List['V4HpfsListZoneReturnObjZoneList']] = None  # 查询的可用区列表
    totalCount: Optional[int] = None  # 当前资源池下可用区总数
    currentCount: Optional[int] = None  # 当前页码的元素个数
    pageSize: Optional[int] = None  # 每页个数
    pageNo: Optional[int] = None  # 当前页数


@dataclass_json
@dataclass
class V4HpfsListZoneReturnObjZoneList:
    azName: Optional[str] = None  # 可用区名称，其他需要可用区参数的接口需要依赖该名称结果
    azDisplayName: Optional[str] = None  # 可用区展示名
    storageTypes: Optional[List[str]] = None  # 可用区支持的存储类型
