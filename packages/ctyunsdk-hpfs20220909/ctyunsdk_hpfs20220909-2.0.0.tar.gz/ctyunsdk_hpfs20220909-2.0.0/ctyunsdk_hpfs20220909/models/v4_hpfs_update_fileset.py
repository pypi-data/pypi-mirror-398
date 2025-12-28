from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsUpdateFilesetRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    filesetID: str  # FILESET唯一ID
    capacityQuota: Optional[int] = None  # FILESET的容量限制，单位：GiB，起步 10GiB 且最小不低于FILESET已使用容量，步长为1GiB，最大不超过文件系统可用容量 + 此FILESET已分配容量
    fileCountQuota: Optional[int] = None  # FILESET的文件数限制，单位：个，起步 1 万个且最小不低于FILESET已使用文件数量，步长为1千个，最大不超过文件系统可用文件数量 + 此FILESET已分配文件数量
    filesetDescription: Optional[str] = None  # FILESET的描述，长度为0~128个字符

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsUpdateFilesetResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsUpdateFilesetReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsUpdateFilesetReturnObj:
    regionID: Optional[str] = None  # 资源所属资源池 ID
    resources: Optional[List['V4HpfsUpdateFilesetReturnObjResources']] = None  # 资源明细


@dataclass_json
@dataclass
class V4HpfsUpdateFilesetReturnObjResources:
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    filesetID: Optional[str] = None  # FILESET唯一ID
