from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsUpdateLabelRequest(CtyunOpenAPIRequest):
    sfsUID: str  # 并行文件唯一ID
    regionID: str  # 资源池ID
    labelList: List['V4HpfsUpdateLabelRequestLabelList']  # 标签和相应的操作类型

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsUpdateLabelRequestLabelList:
    key: str  # 标签键，长度不能超过128个字符，首尾不能为空字符
    value: str  # 标签值，长度不能超过128个字符，首尾不能为空字符
    operateType: str  # 操作类型 绑定 BIND/ 解绑 UNBIND


@dataclass_json
@dataclass
class V4HpfsUpdateLabelResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional[object] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


