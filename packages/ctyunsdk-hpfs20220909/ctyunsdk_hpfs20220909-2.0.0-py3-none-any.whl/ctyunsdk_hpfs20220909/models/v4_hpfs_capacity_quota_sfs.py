from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsCapacityQuotaSfsRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsCapacityQuotaSfsResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsCapacityQuotaSfsReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsCapacityQuotaSfsReturnObj:
    totalCapacityQuota: Optional[int] = None  # 总容量配额，单位GB，-1表示无限制
    usedCapacityQuota: Optional[int] = None  # 已使⽤容量配额，单位GB
    avlCapacityQuota: Optional[int] = None  # 剩余容量配额，单位GB，-1表示无限制
