from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4CdaVpcListRequest(CtyunOpenAPIRequest):
    vrfName: str  # 专线网关ID

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaVpcListResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4CdaVpcListReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaVpcListReturnObj:
    vpcList: Optional[List['V4CdaVpcListReturnObjVpcList']] = None  # VPC列表


@dataclass_json
@dataclass
class V4CdaVpcListReturnObjVpcList:
    account: Optional[str] = None  # 天翼云账号
    vpcID: Optional[str] = None  # VPC  ID
    vrfName: Optional[str] = None  # 专线网关ID
    dcType: Optional[str] = None  # 本参数表示资源池类型。<br>取值范围：<br>MAZ<br>CNP
    vpcSubnet: Optional[str] = None  # VPC子网
    resourcePool: Optional[str] = None  # 资源池ID
    ipVersion: Optional[str] = None  # 本参数表示包周期类型。<br>取值范围：<br>IPV4<br>IPV6<br>DUALSTACK
    bandwidth: Optional[int] = None  # 虚拟带宽
    vpcName: Optional[str] = None  # VPC名字
    vpcSubnetIPv6: Optional[str] = None  # VPC IPv6子网
    vpcNetworkSegment: Optional[str] = None  # VPC网段
    ctUserId: Optional[str] = None  # 天翼云用户ID
    vpcNetworkSegmentIPv6: Optional[str] = None  # VPC IPv6网段
