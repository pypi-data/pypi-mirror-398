from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsNewProtocolServiceRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: str  # 并行文件唯一ID
    protocolSpec: str  # 协议服务规格，目前仅支持general（通用型）
    protocolType: str  # 协议服务的协议类型，目前仅支持nfs
    vpcID: str  # 虚拟网 ID
    subnetID: Optional[str] = None  # 子网 ID，3.0资源池必填，4.0资源池若isVpce为true则必填
    isVpce: Optional[bool] = None  # 是否创建终端节点，默认false，仅4.0资源池生效
    ipVersion: Optional[int] = None  # 终端节点的类型，0:ipv4,1:ipv6,2:双栈，默认为0，仅isVpce为true时生效，仅4.0资源池生效
    protocolDescrption: Optional[str] = None  # 协议服务的描述，最高支持128字符

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewProtocolServiceResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsNewProtocolServiceReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewProtocolServiceReturnObj:
    regionID: Optional[str] = None  # 资源所属资源池 ID
    resources: Optional[List['V4HpfsNewProtocolServiceReturnObjResources']] = None  # 资源明细


@dataclass_json
@dataclass
class V4HpfsNewProtocolServiceReturnObjResources:
    sfsUID: Optional[str] = None  # 并行文件唯一 ID
    protocolServiceID: Optional[str] = None  # 协议服务唯一ID
