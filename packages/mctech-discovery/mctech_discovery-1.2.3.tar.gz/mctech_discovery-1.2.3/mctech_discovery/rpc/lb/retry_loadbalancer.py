from __future__ import absolute_import
import websocket
from typing import Iterable, AsyncIterable

from ._lb_types import LoadBalancer
from ..request_context import RequestContext
from ..ep import EndPointRequest

from .._rpc_types import Invoker, RpcServiceInfo, MixedMethod, RpcResponseResult


class RetryLoadBalancer(LoadBalancer):

    def __init__(self, lb: LoadBalancer):
        super().__init__()
        self._lb = lb

    def check_alive(self) -> bool:
        return self._lb.check_alive()

    def create_context(self,
                       method: MixedMethod,
                       invoker: Invoker,
                       service: RpcServiceInfo) -> RequestContext:
        return self._lb.create_context(method, invoker, service)

    async def execute_async(self, req: EndPointRequest) -> RpcResponseResult:
        result_data = await self._lb.execute_async(req)
        return result_data

    async def stream_async(self, req: EndPointRequest) -> AsyncIterable[bytes]:
        result_stream = await self._lb.stream_async(req)
        return result_stream

    async def ws_async(self, req: EndPointRequest) -> websocket.WebSocket:
        conn = await self._lb.ws_async(req)
        return conn

    def execute(self, req: EndPointRequest) -> RpcResponseResult:
        result_data = self._lb.execute(req)
        return result_data

    def stream(self, req: EndPointRequest) -> Iterable[bytes]:
        result_stream = self._lb.stream(req)
        return result_stream

    def ws(self, req: EndPointRequest) -> websocket.WebSocket:
        conn = self._lb.ws(req)
        return conn
