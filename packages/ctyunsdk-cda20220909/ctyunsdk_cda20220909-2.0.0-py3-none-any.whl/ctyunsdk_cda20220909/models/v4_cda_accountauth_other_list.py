from typing import Optional, List

from ctyun_python_sdk_core.ctyun_openapi_request import CtyunOpenAPIRequest
from ctyun_python_sdk_core.ctyun_openapi_response import CtyunOpenAPIResponse
from dataclasses_json import dataclass_json
from dataclasses import dataclass


@dataclass_json
@dataclass
class V4CdaAccountauthOtherListRequest(CtyunOpenAPIRequest):
    def __post_init__(self):
        super().__init__()



@dataclass_json
@dataclass
class V4CdaAccountauthOtherListResponse(CtyunOpenAPIResponse):
    statusCode: Optional[int] = None  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str] = None  # 错误码，为product.module.code三段式码
    error: Optional[str] = None  # 错误码，为product.module.code三段式码
    message: Optional[str] = None  # 失败时的错误描述，一般为英文描述
    description: Optional[str] = None  # 失败时的错误描述，一般为中文描述
    returnObj: Optional['V4CdaAccountauthOtherListReturnObj'] = None  # 成功时返回的数据

    def __post_init__(self):
        super().__init__()


@dataclass_json
@dataclass
class V4CdaAccountauthOtherListReturnObj:
    totalCount: Optional[int] = None  # 总共数量
    currentCount: Optional[int] = None  # 当前数量
    accountAuthList: Optional[List['V4CdaAccountauthOtherListReturnObjAccountAuthList']] = None  # 专线网关列表


@dataclass_json
@dataclass
class V4CdaAccountauthOtherListReturnObjAccountAuthList:
    accountId: Optional[str] = None  # 当前账号ID
    account: Optional[str] = None  # 当前账号邮箱
    vpcID: Optional[str] = None  # 授权的VPC ID
    vpcName: Optional[str] = None  # 授权的VPC Name
    gatewayName: Optional[str] = None  # 授权VPC给专线网关ID
    displayName: Optional[str] = None  # 专线网关
    authAccountId: Optional[str] = None  # 对方账号ID，授权自己VPC给对方账号
    authAccount: Optional[str] = None  # 对方账号邮箱
    regionID: Optional[str] = None  # 资源池ID
    description: Optional[str] = None  # 描述
    dedicatedCloudID: Optional[str] = None  # 专属云资源池ID
    dedicatedCloudName: Optional[str] = None  # 专属云资源池名字
    updatedTime: Optional[str] = None  # 最近更新时间
