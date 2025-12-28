from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsRefundSfsRequest(CtyunOpenAPIRequest):
    sfsUID: str  # 并行文件唯一ID
    regionID: str  # 资源池 ID
    clientToken: Optional[str] = None  # 客户端存根，用于保证订单幂等性。要求单个云平台账户内唯一

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsRefundSfsResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsRefundSfsReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsRefundSfsReturnObj:
    masterOrderID: Optional[str] = None  # 退订订单号，可以使用该订单号确认资源的最终退订状态
    masterOrderNO: Optional[str] = None  # 订单号
    regionID: Optional[str] = None  # 资源所属资源池 ID
