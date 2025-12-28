from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsInfoProtocolServiceRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    protocolServiceID: str  # 协议服务唯一ID

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsInfoProtocolServiceResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsInfoProtocolServiceReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsInfoProtocolServiceReturnObj:
    regionID: Optional[str] = None  # 资源池ID
    sfsUID: Optional[str] = None  # 并行文件唯一 ID
    azName: Optional[str] = None  # 多可用区下可用区的名字
    protocolServiceID: Optional[str] = None  # 协议服务唯一ID
    protocolServiceStatus: Optional[str] = None  # 协议服务的状态，creating/available//deleting/create_fail/agent_err。creating：协议服务创建中；available：协议服务可用；deleting：协议服务删除中；create_fail：协议服务创建失败；agent_err：底层协议服务组件异常（该异常状态可恢复）
    protocolSpec: Optional[str] = None  # 协议规格
    protocolType: Optional[str] = None  # 协议类型
    vpcSharePath: Optional[str] = None  # vpc挂载地址(ipv4)
    vpcSharePathV6: Optional[str] = None  # vpc挂载地址(ipv6)
    vpceSharePath: Optional[str] = None  # vpce挂载地址（ipv4）
    vpceSharePathV6: Optional[str] = None  # vpce挂载地址（ipv6）
    vpcID: Optional[str] = None  # 虚拟网 ID
    vpcName: Optional[str] = None  # vpc名称
    subnetID: Optional[str] = None  # 子网ID
    createTime: Optional[int] = None  # 协议服务的创建时间
    failMsg: Optional[str] = None  # 协议服务的异常原因
    protocolDescription: Optional[str] = None  # 协议服务的描述
