from ctyun_python_sdk_core import CtyunClient, Credential, ClientConfig, CtyunRequestException

from .models import *


class CdaClient:
    def __init__(self, client_config: ClientConfig):
        self.endpoint = client_config.endpoint
        self.credential = Credential(client_config.access_key_id, client_config.access_key_secret)
        self.ctyun_client = CtyunClient(client_config.verify_tls)

    def v4_cda_vpc_list(self, request: V4CdaVpcListRequest) -> V4CdaVpcListResponse:
        """查询用户专线网关下添加的VPC信息"""
        url = f"{self.endpoint}/v4/cda/vpc/list"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaVpcListResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_physical_line_update(self, request: V4CdaPhysicalLineUpdateRequest) -> V4CdaPhysicalLineUpdateResponse:
        """修改物理专线云端口信息"""
        url = f"{self.endpoint}/v4/cda/physical-line/update"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaPhysicalLineUpdateResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_physical_line_bind(self, request: V4CdaPhysicalLineBindRequest) -> V4CdaPhysicalLineBindResponse:
        """专线网关绑定已创建的物理专线"""
        url = f"{self.endpoint}/v4/cda/physical-line/bind"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaPhysicalLineBindResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_switch_count(self, request: V4CdaSwitchCountRequest) -> V4CdaSwitchCountResponse:
        """查询用记名下资源池的专线交换机数量"""
        url = f"{self.endpoint}/v4/cda/switch/count"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaSwitchCountResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_switch_list(self, request: V4CdaSwitchListRequest) -> V4CdaSwitchListResponse:
        """查询已创建的云专线交换机。"""
        url = f"{self.endpoint}/v4/cda/switch/list"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaSwitchListResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_vpc_count(self, request: V4CdaVpcCountRequest) -> V4CdaVpcCountResponse:
        """查询用户专线网关下的VPC数量"""
        url = f"{self.endpoint}/v4/cda/vpc/count"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaVpcCountResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_gateway_add(self, request: V4CdaGatewayAddRequest) -> V4CdaGatewayAddResponse:
        """创建的云专线(Cloud Dedicated Access)网关。"""
        url = f"{self.endpoint}/v4/cda/gateway/add"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaGatewayAddResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_gateway_delete(self, request: V4CdaGatewayDeleteRequest) -> V4CdaGatewayDeleteResponse:
        """删除已创建的云专线网关。"""
        url = f"{self.endpoint}/v4/cda/gateway/delete"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaGatewayDeleteResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_gateway_count(self, request: V4CdaGatewayCountRequest) -> V4CdaGatewayCountResponse:
        """查询用户已创建的专线网关数量"""
        url = f"{self.endpoint}/v4/cda/gateway/count"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaGatewayCountResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_ec_info(self, request: V4CdaEcInfoRequest) -> V4CdaEcInfoResponse:
        """查询专线网关已绑定云间高速信息"""
        url = f"{self.endpoint}/v4/cda/ec/info"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaEcInfoResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_vpc_info(self, request: V4CdaVpcInfoRequest) -> V4CdaVpcInfoResponse:
        """获取指定vpc的详细信息和能访问该vpc的物理专线信息"""
        url = f"{self.endpoint}/v4/cda/vpc/info"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaVpcInfoResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_health_check_update(self, request: V4CdaHealthCheckUpdateRequest) -> V4CdaHealthCheckUpdateResponse:
        """更新用户专线网关的健康检查：发包间隔、报文探测个数和自动路由切换。"""
        url = f"{self.endpoint}/v4/cda/health-check/update"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaHealthCheckUpdateResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_health_check_add(self, request: V4CdaHealthCheckAddRequest) -> V4CdaHealthCheckAddResponse:
        """用户为专线网关创建健康检查"""
        url = f"{self.endpoint}/v4/cda/health-check/add"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaHealthCheckAddResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_health_check_status_get(self, request: V4CdaHealthCheckStatusGetRequest) -> V4CdaHealthCheckStatusGetResponse:
        """健康检查查询检查结果"""
        url = f"{self.endpoint}/v4/cda/health-check/status/get"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaHealthCheckStatusGetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_health_check_get(self, request: V4CdaHealthCheckGetRequest) -> V4CdaHealthCheckGetResponse:
        """专线网关查询健康检查设置项"""
        url = f"{self.endpoint}/v4/cda/health-check/get"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaHealthCheckGetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_link_probe_delete(self, request: V4CdaLinkProbeDeleteRequest) -> V4CdaLinkProbeDeleteResponse:
        """删除指定源目的ip的健康检查数据，支持批量删除"""
        url = f"{self.endpoint}/v4/cda/link-probe/delete"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaLinkProbeDeleteResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_link_probe_query(self, request: V4CdaLinkProbeQueryRequest) -> V4CdaLinkProbeQueryResponse:
        """展示指定vrf下的所有Ping测历史数据"""
        url = f"{self.endpoint}/v4/cda/link-probe/query"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaLinkProbeQueryResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_link_probe_add(self, request: V4CdaLinkProbeAddRequest) -> V4CdaLinkProbeAddResponse:
        """用户为专线网关创建健康检查"""
        url = f"{self.endpoint}/v4/cda/link-probe/add"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaLinkProbeAddResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_accountauth_other_list(self, request: V4CdaAccountauthOtherListRequest) -> V4CdaAccountauthOtherListResponse:
        """查询跨账号VPC授权给其他账号的网络实例"""
        url = f"{self.endpoint}/v4/cda/accountauth/other/list"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaAccountauthOtherListResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_accountauth_add(self, request: V4CdaAccountauthAddRequest) -> V4CdaAccountauthAddResponse:
        """云专线支持跨账号VPC互通，需要先创建跨账号的VPC授权。"""
        url = f"{self.endpoint}/v4/cda/accountauth/add"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaAccountauthAddResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_accountauth_own_list(self, request: V4CdaAccountauthOwnListRequest) -> V4CdaAccountauthOwnListResponse:
        """查询跨账号VPC授权给自己账号的网络实例"""
        url = f"{self.endpoint}/v4/cda/accountauth/own/list"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaAccountauthOwnListResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_accountauth_delete(self, request: V4CdaAccountauthDeleteRequest) -> V4CdaAccountauthDeleteResponse:
        """删除已创建的跨账号VPC授权。"""
        url = f"{self.endpoint}/v4/cda/accountauth/delete"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaAccountauthDeleteResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_accountauth_statistics(self, request: V4CdaAccountauthStatisticsRequest) -> V4CdaAccountauthStatisticsResponse:
        """统计账号下已授权的VPC及授权给专线网关数量。"""
        url = f"{self.endpoint}/v4/cda/accountauth/statistics"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaAccountauthStatisticsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_physical_line_unbind(self, request: V4CdaPhysicalLineUnbindRequest) -> V4CdaPhysicalLineUnbindResponse:
        """专线网关解绑物理专线"""
        url = f"{self.endpoint}/v4/cda/physical-line/unbind"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaPhysicalLineUnbindResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_vpc_add(self, request: V4CdaVpcAddRequest) -> V4CdaVpcAddResponse:
        """给已创建的云专线网关添加VPC。"""
        url = f"{self.endpoint}/v4/cda/vpc/add"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaVpcAddResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_vpc_update(self, request: V4CdaVpcUpdateRequest) -> V4CdaVpcUpdateResponse:
        """给已创建的云专线网关修改VPC。"""
        url = f"{self.endpoint}/v4/cda/vpc/update"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaVpcUpdateResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_vpc_delete(self, request: V4CdaVpcDeleteRequest) -> V4CdaVpcDeleteResponse:
        """给已创建的云专线网关删除VPC。"""
        url = f"{self.endpoint}/v4/cda/vpc/delete"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaVpcDeleteResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_static_route_delete(self, request: V4CdaStaticRouteDeleteRequest) -> V4CdaStaticRouteDeleteResponse:
        """删除已有的静态路由"""
        url = f"{self.endpoint}/v4/cda/static-route/delete"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaStaticRouteDeleteResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_static_route_list(self, request: V4CdaStaticRouteListRequest) -> V4CdaStaticRouteListResponse:
        """查询专线网关下的静态路由"""
        url = f"{self.endpoint}/v4/cda/static-route/list"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaStaticRouteListResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_bgp_route_delete(self, request: V4CdaBgpRouteDeleteRequest) -> V4CdaBgpRouteDeleteResponse:
        """删除已有的BGP动态路由"""
        url = f"{self.endpoint}/v4/cda/bgp-route/delete"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaBgpRouteDeleteResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_bgp_route_list(self, request: V4CdaBgpRouteListRequest) -> V4CdaBgpRouteListResponse:
        """查询用户专线网关下的BGP动态路由"""
        url = f"{self.endpoint}/v4/cda/bgp-route/list"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4CdaBgpRouteListResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_bgp_route_update(self, request: V4CdaBgpRouteUpdateRequest) -> V4CdaBgpRouteUpdateResponse:
        """更新BGP动态路由"""
        url = f"{self.endpoint}/v4/cda/bgp-route/update"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaBgpRouteUpdateResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_cda_static_route_update(self, request: V4CdaStaticRouteUpdateRequest) -> V4CdaStaticRouteUpdateResponse:
        """更新已有的静态路由"""
        url = f"{self.endpoint}/v4/cda/static-route/update"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4CdaStaticRouteUpdateResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))



