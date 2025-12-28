from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListFilesetRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    azName: Optional[str] = None  # 多可用区下，可用区的名称，不传为查询全部
    filesetStatus: Optional[str] = None  # FILESET状态：available（可用）、unusable（异常）
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListFilesetResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListFilesetReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListFilesetReturnObj:
    filesetList: Optional[List['V4HpfsListFilesetReturnObjFilesetList']] = None  # 返回的FILESET列表
    totalCount: Optional[int] = None  # 资源池下用户FILESET总数
    currentCount: Optional[int] = None  # 当前页码下查询回来的用户FILESET数
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)
    pageNo: Optional[int] = None  # 列表的分页页码


@dataclass_json
@dataclass
class V4HpfsListFilesetReturnObjFilesetList:
    regionID: Optional[str] = None  # 资源池ID
    filesetID: Optional[str] = None  # FILESET唯一ID
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    filesetStatus: Optional[str] = None  # FILESET状态：available（可用）、unusable（异常）
    filesetPath: Optional[str] = None  # FILESET在文件系统中的绝对路径
    capacityQuota: Optional[int] = None  # FILESET的容量配额限制，单位GB
    fileCountQuota: Optional[int] = None  # FILESET数量配额限制
    capacityQuotaUsed: Optional[int] = None  # FILESET已使用的容量配额，单位GB，向上取整
    fileCountQuotaUsed: Optional[int] = None  # FILESET已使用的数量配额
    filesetDescription: Optional[str] = None  # FILESET的描述
    createTime: Optional[int] = None  # FILESET的创建时间
    azName: Optional[str] = None  # 可用区名称
    dataflowID: Optional[str] = None  # FILESET对应数据流动策略的ID
