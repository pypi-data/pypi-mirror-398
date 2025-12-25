from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4CdaBgpRouteUpdateRequest(CtyunOpenAPIRequest):
    BGPID: str  # BGP路由ID
    ipVersion: str  # 本参数表示包周期类型。<br>取值范围：<br>IPV4<br>IPV6<br>DUALSTACK
    networkCidr: Optional[List[str]] = None  # 客户侧子网列表(IPv4)，ipVersion为IPV4和DUALSTACK时必填
    networkCidrV6: Optional[List[str]] = None  # 客户侧子网列表(IPv6)，ipVersion为IPV6和DUALSTACK时必填
    BGPList: Optional[List['V4CdaBgpRouteUpdateRequestBGPList']] = None  # IPv4类型的BGP列表，ipVersion为IPV4和DUALSTACK时必填
    BGPIpv6List: Optional[List['V4CdaBgpRouteUpdateRequestBGPIpv6List']] = None  # IPv6类型的BGP列表，ipVersion为IPV6和DUALSTACK时必填
    multiPath: Optional[bool] = None  # 是否开启多路功能，ipVersion为IPV4和DUALSTACK时选填
    multiPathNum: Optional[str] = None  # Bgp多路功能序号(负载线路数)，ipVersion为IPV4和DUALSTACK时选填
    multiPathType: Optional[str] = None  # Bgp多路功能类型(IBGP/EBGP)
    multiPathIpv6: Optional[bool] = None  # 是否开启BGP-IPv6多路功能，ipVersion为IPV6和DUALSTACK时选填
    multiPathNumIpv6: Optional[str] = None  # BGP-IPv6多路功能序号(负载线路数)，ipVersion为IPV6和DUALSTACK时选填

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaBgpRouteUpdateRequestBGPList:
    BGPNeighbor: str  # BGP邻居名称
    BGPIP: str  # BGP邻居IP(物理专线的远端互联IP)
    lineID: str  # 物理专线ID
    peerAS: str  # Peer AS号
    bfd: bool  # 是否打开bfd 功能
    BGPKey: Optional[str] = None  # BGP密钥


@dataclass_json
@dataclass
class V4CdaBgpRouteUpdateRequestBGPIpv6List:
    BGPNeighbor: str  # BGP邻居名称
    BGPIP: str  # BGP邻居IP(物理专线的远端互联IP)
    lineID: str  # 物理专线ID
    peerAS: str  # Peer AS号
    bfd: bool  # 是否打开bfd 功能
    BGPKey: Optional[str] = None  # BGP密钥


@dataclass_json
@dataclass
class V4CdaBgpRouteUpdateResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4CdaBgpRouteUpdateReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaBgpRouteUpdateReturnObj:
    result: Optional[str] = None  # 1成功， 0失败
    data: Optional[str] = None  # 成功为空
    errorCode: Optional[str] = None  # 错误代码，成功为空
    errorMsg: Optional[str] = None  # 成功为空
    traceId: Optional[str] = None  # 日志跟踪ID
