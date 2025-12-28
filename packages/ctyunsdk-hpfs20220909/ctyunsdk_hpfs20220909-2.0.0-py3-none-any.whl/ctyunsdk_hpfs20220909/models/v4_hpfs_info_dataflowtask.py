from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsInfoDataflowtaskRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    taskID: str  # 数据流动任务ID

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsInfoDataflowtaskResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsInfoDataflowtaskReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsInfoDataflowtaskReturnObj:
    regionID: Optional[str] = None  # 资源池ID
    taskID: Optional[str] = None  # 数据流动任务ID
    dataflowID: Optional[str] = None  # 数据流动策略ID
    sfsUID: Optional[str] = None  # 并行文件唯一ID
    sfsDirectory: Optional[str] = None  # 并行文件FILESET目录
    bucketName: Optional[str] = None  # 对象存储的桶名称
    bucketPrefix: Optional[str] = None  # 对象存储桶的前缀
    taskType: Optional[str] = None  # 任务类型（import_data/import_metadata/export_data）
    taskDescription: Optional[str] = None  # 数据流动任务的描述
    taskStatus: Optional[str] = None  # 数据流动任务的状态，creating/executing/completed/canceling/fail。creating：任务创建中；executing：任务执行中；completed：任务已完成；canceling：任务取消中（可能是任务失败正在取消，也可能是策略删除任务正在取消）；fail：任务异常（异常原因可见failMsg，异常的任务不可恢复）
    createTime: Optional[int] = None  # 数据流动任务创建时间
    startTime: Optional[int] = None  # 数据流动任务开始时间
    completeTime: Optional[int] = None  # 数据流动任务完成时间
    updateTime: Optional[int] = None  # 数据流动任务更新时间
    cancelTime: Optional[int] = None  # 数据流动任务取消时间
    failTime: Optional[int] = None  # 数据流动任务异常发生时间
    failMsg: Optional[str] = None  # 数据流动任务异常原因
    azName: Optional[str] = None  # 多可用区下的可用区名字
    totalFileCount: Optional[int] = None  # 需处理文件数
    completedFileCount: Optional[int] = None  # 已成功文件数
    failedFileCount: Optional[int] = None  # 未成功文件数
    reportPath: Optional[str] = None  # 任务报告地址
