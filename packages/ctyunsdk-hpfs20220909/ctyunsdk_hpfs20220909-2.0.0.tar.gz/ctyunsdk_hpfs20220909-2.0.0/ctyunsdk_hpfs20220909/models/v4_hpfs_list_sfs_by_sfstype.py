from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsListSfsBySfstypeRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsType: str  # 存储类型
    azName: Optional[str] = None  # 可用区名称，不传为查询全部
    projectID: Optional[str] = None  # 资源所属企业项目 ID，不传为查询全部
    pageSize: Optional[int] = None  # 每页包含的元素个数范围(1-50)，默认值为10
    pageNo: Optional[int] = None  # 列表的分页页码，默认值为1

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListSfsBySfstypeResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4HpfsListSfsBySfstypeReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsListSfsBySfstypeReturnObj:
    list: Optional[List['V4HpfsListSfsBySfstypeReturnObjList']] = None  # 文件系统详情列表
    total: Optional[int] = None  # 资源池指定条件下用户并行文件总数
    totalCount: Optional[int] = None  # 资源池指定条件下用户并行文件总数
    currentCount: Optional[int] = None  # 当前页码的元素个数
    pageSize: Optional[int] = None  # 每页个数
    pageNo: Optional[int] = None  # 当前页数


@dataclass_json
@dataclass
class V4HpfsListSfsBySfstypeReturnObjList:
    sfsName: Optional[str] = None  # 并行文件名称
    sfsUID: Optional[str] = None  # 并行文件唯一 ID
    sfsSize: Optional[int] = None  # 大小（GB）
    sfsType: Optional[str] = None  # 类型，hpfs_perf(HPC性能型)
    sfsProtocol: Optional[str] = None  # 挂载协议，nfs/hpfs
    sfsStatus: Optional[str] = None  # 并行文件状态。包括creating（创建中）、available（可用）、unusable（冻结）
    usedSize: Optional[int] = None  # 已用大小（MB）
    createTime: Optional[int] = None  # 创建时刻，epoch 时戳，精度毫秒
    updateTime: Optional[int] = None  # 更新时刻，epoch 时戳，精度毫秒
    expireTime: Optional[int] = None  # 过期时刻，epoch 时戳，精度毫秒
    projectID: Optional[str] = None  # 资源所属企业项目 ID
    isEncrypt: Optional[bool] = None  # 是否加密盘
    kmsUUID: Optional[str] = None  # 加密盘密钥 UUID
    onDemand: Optional[bool] = None  # 是否按需订购
    regionID: Optional[str] = None  # 资源池 ID
    azName: Optional[str] = None  # 多可用区下的可用区名字
    clusterName: Optional[str] = None  # 集群名称
    baseline: Optional[str] = None  # 性能基线（MB/s/TB）
    sharePath: Optional[str] = None  # Linux 主机共享路径
    sharePathV6: Optional[str] = None  # Linux 主机 IPv6 共享路径
    windowsSharePath: Optional[str] = None  # Windows 主机共享路径
    windowsSharePathV6: Optional[str] = None  # Windows 主机 IPv6 共享路径
    mountCount: Optional[int] = None  # 挂载点数量
    cephID: Optional[str] = None  # ceph底层id
    hpfsSharePath: Optional[str] = None  # HPFS文件系统共享路径(Linux)
    hpfsSharePathV6: Optional[str] = None  # HPFS文件系统 IPv6共享路径(Linux)
    secretKey: Optional[str] = None  # HPC型挂载需要的密钥
    dataflowList: Optional[List[str]] = None  # HPFS文件系统下的数据流动策略ID列表
    dataflowCount: Optional[int] = None  # HPFS文件系统下的数据流动策略数量
