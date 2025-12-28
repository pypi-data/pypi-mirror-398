from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsNewDataflowtaskRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: str  # 并行文件唯一ID
    dataflowID: str  # 数据流动策略ID
    taskType: str  # 数据流动任务类型（目前支持import_data/import_metadata/export_data）
    taskDescription: Optional[str] = None  # 数据流动任务的描述，最高支持128字符

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewDataflowtaskResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsNewDataflowtaskReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewDataflowtaskReturnObj:
    regionID: Optional[str] = None  # 资源所属资源池 ID
    resources: Optional[List['V4HpfsNewDataflowtaskReturnObjResources']] = None  # 资源明细


@dataclass_json
@dataclass
class V4HpfsNewDataflowtaskReturnObjResources:
    dataflowID: Optional[str] = None  # 数据流动策略ID
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    taskID: Optional[str] = None  # 数据流动任务ID
