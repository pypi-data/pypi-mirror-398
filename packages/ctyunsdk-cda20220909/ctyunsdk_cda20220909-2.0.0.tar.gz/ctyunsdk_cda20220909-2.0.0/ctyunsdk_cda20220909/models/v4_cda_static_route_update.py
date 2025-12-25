from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4CdaStaticRouteUpdateRequest(CtyunOpenAPIRequest):
    SRID: str  # 静态路由ID
    ipVersion: str  # 本参数表示包周期类型。<br>取值范围：<br>IPV4<br>IPV6<br>DUALSTACK
    dstCidr: Optional[List[str]] = None  # 目的IPV4地址列表(全量传入)
    dstCidrV6: Optional[List[str]] = None  # 目的IPV6地址列表(全量传入)
    nextHop: Optional[List['V4CdaStaticRouteUpdateRequestNextHop']] = None  # 下一跳及优先级列表(全量传入)
    nextHopV6: Optional[List['V4CdaStaticRouteUpdateRequestNextHopV6']] = None  # 下一跳及优先级列表(全量传入)

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaStaticRouteUpdateRequestNextHop:
    remoteGatewayIp: str  # 下一跳，即物理专线的远端互联ip
    priority: int  # 优先级
    track: Optional[int] = None  # 0为关闭，1为开启
    bfd: Optional[bool] = None  # 是否开启bfd功能，ture为开启，false为关闭


@dataclass_json
@dataclass
class V4CdaStaticRouteUpdateRequestNextHopV6:
    remoteGatewayIp: str  # 下一跳，即物理专线的远端互联ip
    priority: int  # 优先级
    track: Optional[int] = None  # 0为关闭，1为开启
    bfd: Optional[bool] = None  # 是否开启bfd功能，ture为开启，false为关闭


@dataclass_json
@dataclass
class V4CdaStaticRouteUpdateResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4CdaStaticRouteUpdateReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaStaticRouteUpdateReturnObj:
    result: Optional[str] = None  # 1成功， 0失败
    data: Optional[str] = None  # 成功为空
    errorCode: Optional[str] = None  # 错误代码，成功为空
    errorMsg: Optional[str] = None  # 成功为空
    traceID: Optional[str] = None  # 日志跟踪ID
