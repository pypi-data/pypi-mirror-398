from __future__ import absolute_import
import websocket
from typing import Iterable, AsyncIterable

from ._lb_types import LoadBalancer
from ..request_context import InternalRequestContext
from ..ep import EndPointRequest

from .._rpc_types import Invoker, RpcServiceInfo, EndPoint, MixedMethod, RpcResponseResult


class DirectLoadBalancer(LoadBalancer):
    '''
    显示指定了调用的目标地址的LoadBalancer实现方式
    '''

    def __init__(self):
        super().__init__()

    def check_alive(self):
        return True

    def create_context(self,
                       method: MixedMethod,
                       invoker: Invoker,
                       service: RpcServiceInfo) -> InternalRequestContext:
        return InternalRequestContext(method, invoker, service, None, None)

    @property
    def type(self):
        return 'direct'

    async def execute_async(self, req: EndPointRequest) -> RpcResponseResult:
        ep = self._get_end_point(req)
        result_data = await req.execute_async(ep)
        return result_data

    async def stream_async(self, req: EndPointRequest) -> AsyncIterable[bytes]:
        ep = self._get_end_point(req)
        result_stream = await req.stream_async(ep)
        return result_stream

    async def ws_async(self, req: EndPointRequest) -> websocket.WebSocket:
        ep = self._get_end_point(req)
        conn = await req.ws_async(ep)
        return conn

    def execute(self, req: EndPointRequest) -> RpcResponseResult:
        ep = self._get_end_point(req)
        result_data = req.execute(ep)
        return result_data

    def stream(self, req: EndPointRequest) -> Iterable[bytes]:
        ep = self._get_end_point(req)
        result_stream = req.stream(ep)
        return result_stream

    def ws(self, req: EndPointRequest) -> websocket.WebSocket:
        ep = self._get_end_point(req)
        conn = req.ws(ep)
        return conn

    def _get_end_point(self, req: EndPointRequest) -> EndPoint:
        target_url = req.context.url
        return EndPoint(
            id="%s:%s" % (self.type, req.context.service.url),
            vip_address=False,
            host=target_url.host,
            port=target_url.port or (80 if target_url.scheme == 'http' else 443)
        )
