from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4HpfsNewDirectoryRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池 ID
    sfsUID: str  # 并行文件唯一ID
    sfsDirectory: str  # 并行文件目录，目录名仅允许数字、字母、下划线、连接符、中文组成，每级目录最大长度为255字节，最大全路径长度为4096字节，最大目录层数为1000，如果参数为mydir/、mydir、/mydir或/mydir/，则都视为输入/mydir/的目录
    sfsDirectoryMode: Optional[str] = None  # 目录权限，默认值是755，若传入则必须为三位，每位的范围为0到7。第一位表示目录所有者的权限，第二位表示目录所属用户组的权限，第三位表示其他用户的权限。目录所有者由uid指定，目录所属用户组由gid指定，不是目录所有者且不在目录所属用户组的用户为其他用户。例如：755中第一位7代表该目录所有者对该目录具有读、写、执行权限；第二位5代表该目录所属用户组对该目录具有读、执行权限；第三位5代表其他用户对该目录具有读、执行权限
    sfsDirectoryUID: Optional[int] = None  # 目录所有者的用户id，默认值是0，取值范围是0到4,294,967,294（即2^32-2）
    sfsDirectoryGID: Optional[int] = None  # 目录所属用户组id，默认值是0，取值范围是0到4,294,967,294（即2^32-2）

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4HpfsNewDirectoryResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional[object] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


