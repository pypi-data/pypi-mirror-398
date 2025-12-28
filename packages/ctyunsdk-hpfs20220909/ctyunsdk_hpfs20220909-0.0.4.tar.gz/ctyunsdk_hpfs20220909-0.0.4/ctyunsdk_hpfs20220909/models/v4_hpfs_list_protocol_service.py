from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListProtocolServiceRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    azName: Optional[str] = None  # 多可用区下的可用区名字，不传为查询全部
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    protocolServiceStatus: Optional[str] = None  # 协议服务的状态，creating/available//deleting/create_fail/agent_err。creating：协议服务创建中；available：协议服务可用；deleting：协议服务删除中；create_fail：协议服务创建失败；agent_err：底层协议服务组件异常（该异常状态可恢复）
    protocolSpec: Optional[str] = None  # 协议规格，当前仅支持general（通用型）
    protocolType: Optional[str] = None  # 协议类型，当前仅支持nfs
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListProtocolServiceResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListProtocolServiceReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListProtocolServiceReturnObj:
    list: Optional[List['V4HpfsListProtocolServiceReturnObjList']] = None  # 返回的协议列表
    totalCount: Optional[int] = None  # 指定条件下协议服务总数
    currentCount: Optional[int] = None  # 当前页码下查询回来的协议服务数
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)
    pageNo: Optional[int] = None  # 列表的分页页码


@dataclass_json
@dataclass
class V4HpfsListProtocolServiceReturnObjList:
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
