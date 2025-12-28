from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsNewFilesetRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: str  # 并行文件唯一ID
    filesetPath: str  # 指定FILESET在文件系统中的绝对路径，路径限制见接口约束
    capacityQuota: int  # FILESET的容量限制，单位：GiB，起步 10 GiB，步长为 1 GiB，最大不超过文件系统可用容量（文件系统可用容量 = 文件系统总容量 - 非FILESET已用容量 - FILESET分配出去的容量）
    fileCountQuota: int  # FILESET的文件数限制，单位：个，起步 1 万个，步长为 1千个，最大不超过文件系统可用文件数量 （文件系统可用文件数量 = 文件系统总文件数量 - 非FILESET已用文件数量 - FILESET分配出去的文件数量）
    filesetDescription: Optional[str] = None  # FILESET的描述，长度为0~128个字符

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewFilesetResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsNewFilesetReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewFilesetReturnObj:
    regionID: Optional[str] = None  # 资源所属资源池 ID
    resources: Optional[List['V4HpfsNewFilesetReturnObjResources']] = None  # 资源明细


@dataclass_json
@dataclass
class V4HpfsNewFilesetReturnObjResources:
    sfsUID: Optional[str] = None  # 并行文件唯一 ID
    filesetID: Optional[str] = None  # FILESET唯一ID
