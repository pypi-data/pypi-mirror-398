from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4CdaVpcAddRequest(CtyunOpenAPIRequest):
    regionID: str  # 资源池ID
    vpcName: str  # VPC Name
    vpcID: str  # VPC ID
    ipVersion: str  # IPV4 （默认)/DUALSTACK/IPV6(三选一)
    bandwidth: int  # 带宽(M)
    account: str  # 天翼云账号
    vrfName: str  # 专线网关ID
    vpcNetworkSegment: Optional[str] = None  # VPC网段(IPv4或DUALSTACK必填)
    vpcNetworkSegmentIPv6: Optional[str] = None  # VPC网段(IPv6和DUALSTACK必填)
    vpcSubnet: Optional[List[str]] = None  # vpc ipv4子网列表(IPv4和DUALSTACK必填)
    vpcSubnetIPv6: Optional[List[str]] = None  # vpc ipv6子网列表(IPv6和DUALSTACK必填)

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaVpcAddResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional[object] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


