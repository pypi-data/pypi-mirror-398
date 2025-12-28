from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsNewDataflowRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: str  # 并行文件唯一ID
    sfsDirectory: str  # 并行文件FILESET目录，目录名仅允许数字、字母、下划线、连接符、中文组成，每级目录最大长度为255字节，最大全路径长度为4096字节，如果参数为mydir/、mydir、/mydir或/mydir/，则都视为输入/mydir/的目录
    bucketName: str  # 对象存储的桶名称
    autoImport: bool  # 是否打开自动导入
    autoExport: bool  # 是否打开自动导出
    bucketPrefix: Optional[str] = None  # 对象存储桶的前缀
    importDataType: Optional[str] = None  # 导入的数据类型，data/metadata，自动导入开关打开时必填
    exportDataType: Optional[str] = None  # 导出的数据类型，仅支持data，自动导出开关打开时必填
    importTrigger: Optional[str] = None  # 导入的触发条件，仅支持new（新增），自动导入开关打开时必填
    exportTrigger: Optional[str] = None  # 导出的触发条件，支持new（新增）/changed（新增+修改），自动导出开关打开时必填
    dataflowDescription: Optional[str] = None  # 数据流动策略的描述，最高支持128字符

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewDataflowResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsNewDataflowReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewDataflowReturnObj:
    regionID: Optional[str] = None  # 资源所属资源池 ID
    resources: Optional[List['V4HpfsNewDataflowReturnObjResources']] = None  # 资源明细


@dataclass_json
@dataclass
class V4HpfsNewDataflowReturnObjResources:
    dataflowID: Optional[str] = None  # 数据流动策略ID
    sfsUID: Optional[str] = None  # 并行文件唯一ID
