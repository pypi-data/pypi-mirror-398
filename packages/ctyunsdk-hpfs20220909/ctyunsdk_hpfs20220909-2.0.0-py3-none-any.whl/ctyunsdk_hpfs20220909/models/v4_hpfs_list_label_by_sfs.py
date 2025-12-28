from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListLabelBySfsRequest(CtyunOpenAPIRequest):
    sfsUID: str  # 并行文件唯一ID
    regionID: str  # 资源池ID
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListLabelBySfsResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListLabelBySfsReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListLabelBySfsReturnObj:
    labelList: Optional[List['V4HpfsListLabelBySfsReturnObjLabelList']] = None  # 文件系统绑定的标签集合
    totalCount: Optional[int] = None  # 指定并行文件绑定的标签总数
    currentCount: Optional[int] = None  # 当前页码的元素个数
    pageSize: Optional[int] = None  # 每页个数
    pageNo: Optional[int] = None  # 当前页数


@dataclass_json
@dataclass
class V4HpfsListLabelBySfsReturnObjLabelList:
    key: Optional[str] = None  # 标签键
    value: Optional[str] = None  # 标签值
