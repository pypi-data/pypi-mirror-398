from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4CdaSwitchListRequest(CtyunOpenAPIRequest):
    resourcePool: Optional[str] = None  # 资源池ID

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaSwitchListResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4CdaSwitchListReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaSwitchListReturnObj:
    totalCount: Optional[int] = None  # 数量总数
    result: Optional[List['V4CdaSwitchListReturnObjResult']] = None  # 交换机列表
    errorMsg: Optional[str] = None  # 错误信息
    errorCode: Optional[str] = None  # 错误码
    traceID: Optional[str] = None  # 日志跟踪ID


@dataclass_json
@dataclass
class V4CdaSwitchListReturnObjResult:
    switchID: Optional[str] = None  # 交换机ID
    switchName: Optional[str] = None  # 交换机名字
    factory: Optional[str] = None  # 厂商（RUIJIE、华三）
    resourcePool: Optional[str] = None  # 资源池ID
    resourceName: Optional[str] = None  # 资源池名字
    hostname: Optional[str] = None  # 交换机hostname
    ip: Optional[str] = None  # 交换机IP
    loginPort: Optional[str] = None  # 登录port
    vtepIp: Optional[str] = None  # VTEP IP
    vtepVlan: Optional[str] = None  # VTEP VLAN
    deviceModel: Optional[str] = None  # 设备型号
    accessPoint: Optional[str] = None  # 接入点
    as: Optional[int] = None  # as号
    hasBleafRoute: Optional[bool] = None  # 标记交换机是否要配置BLEAF路由，默认为false（只有部分锐捷交换机需要配置）
    sysMac: Optional[str] = None  # 交换机mac（多az并且是锐捷交换机则必填）（mac是查交换机配置查出来）
    resourceType: Optional[str] = None  # 资源池类型
    azone: Optional[str] = None  # 可用区
    status: Optional[str] = None  # 状态
