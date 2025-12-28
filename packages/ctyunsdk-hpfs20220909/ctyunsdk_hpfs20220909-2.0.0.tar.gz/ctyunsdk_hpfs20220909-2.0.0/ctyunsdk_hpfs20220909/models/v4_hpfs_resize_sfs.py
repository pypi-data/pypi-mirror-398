from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsResizeSfsRequest(CtyunOpenAPIRequest):
    sfsSize: int  # 变配后的大小，单位 GB， 起始容量512，步长为512
    sfsUID: str  # 并行文件唯一ID
    regionID: str  # 资源池 ID
    clientToken: Optional[str] = None  # 客户端存根，用于保证订单幂等性。要求单个云平台账户内唯一

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsResizeSfsResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsResizeSfsReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsResizeSfsReturnObj:
    masterOrderID: Optional[str] = None  # 订单 ID。调用方在拿到 masterOrderID 之后，在若干错误情况下，可以使用 masterOrderID 进一步确认订单状态及资源状态
    masterOrderNO: Optional[str] = None  # 订单号
    regionID: Optional[str] = None  # 资源所属资源池 ID
