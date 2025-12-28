from typing import Optional, List, Dict

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListDataflowRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    azName: Optional[str] = None  # 多可用区下的可用区名字，不传为查询全部
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListDataflowResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListDataflowReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListDataflowReturnObj:
    dataflowList: Optional[List['V4HpfsListDataflowReturnObjDataflowList']] = None  # 返回的数据流动策略列表
    totalCount: Optional[int] = None  # 指定条件下用户数据流动策略总数
    currentCount: Optional[int] = None  # 当前页码下查询回来的用户数据流动策略数
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)
    pageNo: Optional[int] = None  # 列表的分页页码


@dataclass_json
@dataclass
class V4HpfsListDataflowReturnObjDataflowList:
    regionID: Optional[str] = None  # 资源池ID
    dataflowID: Optional[str] = None  # 数据流动策略ID
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    sfsDirectory: Optional[str] = None  # 并行文件FILESET目录
    bucketName: Optional[str] = None  # 对象存储的桶名称
    bucketPrefix: Optional[str] = None  # 对象存储桶的前缀
    autoImport: Optional[bool] = None  # 是否打开自动导入
    autoExport: Optional[bool] = None  # 是否打开自动导出
    importDataType: Optional[str] = None  # 导入的数据类型
    exportDataType: Optional[str] = None  # 导出的数据类型
    importTrigger: Optional[str] = None  # 导入的触发条件
    exportTrigger: Optional[str] = None  # 导出的触发条件
    dataflowDescription: Optional[str] = None  # 数据流动策略的描述
    createTime: Optional[int] = None  # 数据流动策略创建时间
    dataflowStatus: Optional[str] = None  # 数据流动策略的状态，creating/updating/available/syncing/deleting/fail/error。creating：策略创建中；updating：策略更新中；available：策略可用（未打开自动导入导出开关）；syncing：策略同步中（打开了自动导入或自动导出，数据持续流动中，即使没有数据正在流动也是同步中）；deleting：策略删除中；fail：策略异常（异常原因可见failMsg，该状态的策略可更新、可恢复）；error：策略创建失败（异常原因可见failMsg，该状态的策略只能删除，无法恢复）
    failTime: Optional[int] = None  # 数据流动策略异常发生时间
    failMsg: Optional[str] = None  # 数据流动策略异常原因
    azName: Optional[str] = None  # 多可用区下的可用区名字
    filesetID: Optional[str] = None  # 数据流动所使用的FILESET的ID
