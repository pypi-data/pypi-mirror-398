from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListRegionRequest(CtyunOpenAPIRequest):
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListRegionResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListRegionReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListRegionReturnObj:
    regionList: Optional[List['V4HpfsListRegionReturnObjRegionList']] = None  # 查询的地域详情列表
    totalCount: Optional[int] = None  # 支持并行文件的地域总数
    currentCount: Optional[int] = None  # 当前页码的元素个数
    pageSize: Optional[int] = None  # 每页个数
    pageNo: Optional[int] = None  # 当前页数


@dataclass_json
@dataclass
class V4HpfsListRegionReturnObjRegionList:
    regionID: Optional[str] = None  # 资源池ID
    regionName: Optional[str] = None  # 资源池名字
