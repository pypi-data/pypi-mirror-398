from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsDataflowQuotaSfsRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: str  # 并行文件唯一ID

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsDataflowQuotaSfsResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsDataflowQuotaSfsReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsDataflowQuotaSfsReturnObj:
    totalDataflowQuota: Optional[int] = None  # 文件系统数据流动策略配额总数
    usedDataflowQuota: Optional[int] = None  # 文件系统已用数据流动策略配额数
    avlDataflowQuota: Optional[int] = None  # 文件系统剩余可用数据流动策略配额数
