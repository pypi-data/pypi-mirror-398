from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsNewSfsRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsType: str  # 并行文件类型，hpfs_perf(HPC性能型)
    sfsProtocol: str  # 协议类型，hpfs
    sfsName: str  # 并行文件名称。单账户单资源池下，命名需唯一，仅允许英文字母数字及-，开头必须为字母，结尾不允许为-，且长度为2-255字符
    sfsSize: int  # 大小，单位 GB， 起始容量512，步长为512
    clientToken: Optional[str] = None  # 客户端存根，用于保证订单幂等性。要求单个云平台账户内唯一
    projectID: Optional[str] = None  # 资源所属企业项目 ID，默认为"0"
    onDemand: Optional[bool] = None  # 是否按需下单。true/false，默认为 true
    cycleType: Optional[str] = None  # 包周期（subscription）类型，year/month。onDemand 为 false 时，必须指定
    cycleCount: Optional[int] = None  # 包周期数。onDemand 为 false 时必须指定。周期最大长度不能超过 3 年
    azName: Optional[str] = None  # 多可用区资源池下，必须指定可用区
    clusterName: Optional[str] = None  # 集群名称，仅资源池支持指定集群时可传入该参数
    baseline: Optional[str] = None  # 性能基线（MB/s/TB），仅资源池支持性能基线时可传入该参数
    vpc: Optional[str] = None  # 虚拟网 ID，hpfs协议不作校验
    subnet: Optional[str] = None  # 子网 ID，hpfs协议不作校验
    labelList: Optional[List['V4HpfsNewSfsRequestLabelList']] = None  # 设置并行文件标签列表，实际绑定标签的结果请根据[查询指定并行文件绑定的标签]接口返回的labelList返回值是否符合预期

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewSfsRequestLabelList:
    key: str  # 标签键，长度不能超过128个字符，首尾不能为空字符
    value: str  # 标签值，长度不能超过128个字符，首尾不能为空字符


@dataclass_json
@dataclass
class V4HpfsNewSfsResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsNewSfsReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewSfsReturnObj:
    masterOrderID: Optional[str] = None  # 订单 ID。调用方在拿到 masterOrderID 之后，在若干错误情况下，可以使用 materOrderID 进一步确认订单状态及资源状态
    masterOrderNO: Optional[str] = None  # 订单号
    masterResourceID: Optional[str] = None  # 主资源 ID
    masterResourceStatus: Optional[str] = None  # 主资源状态。参考主资源状态
    regionID: Optional[str] = None  # 资源所属资源池 ID
    resources: Optional[List['V4HpfsNewSfsReturnObjResources']] = None  # 资源明细


@dataclass_json
@dataclass
class V4HpfsNewSfsReturnObjResources:
    resourceID: Optional[str] = None  # 单项资源的变配、续订、退订等需要该资源项的 ID。比如某个云主机资源作为主资源，对其挂载
    resourceType: Optional[str] = None  # 资源类型
    orderID: Optional[str] = None  # 无需关心
    startTime: Optional[int] = None  # 启动时刻，epoch 时戳，毫秒精度。例：1589869069561
    createTime: Optional[int] = None  # 创建时刻，epoch 时戳，毫秒精度
    updateTime: Optional[int] = None  # 更新时刻，epoch 时戳，毫秒精度
    status: Optional[int] = None  # 资源状态
    isMaster: Optional[bool] = None  # 是否是主资源项
    itemValue: Optional[int] = None  # 资源大小
    sfsUID: Optional[str] = None  # 并行文件唯一 ID
    sfsStatus: Optional[str] = None  # 并行文件状态
    masterOrderID: Optional[str] = None  # 订单 ID
    sfsName: Optional[str] = None  # 并行文件名字
    masterResourceID: Optional[str] = None  # 主资源 ID
