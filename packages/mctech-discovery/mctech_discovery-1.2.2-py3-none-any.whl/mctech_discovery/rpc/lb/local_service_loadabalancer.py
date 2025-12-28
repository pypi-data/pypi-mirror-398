from __future__ import absolute_import
import websocket
from typing import Iterable, AsyncIterable

from ._lb_types import ServiceLoadBalancer
from ..request_context import InternalRequestContext
from ..ep import EndPointRequest

from .._rpc_types import Invoker, RpcServiceInfo, EndPoint, MixedMethod, RpcResponseResult


class LocalServiceLoadBalancer(ServiceLoadBalancer):
    '''
    显示指定了调用的目标地址的LoadBalancer实现方式
    '''

    def __init__(self, inst: EndPoint, app_name: str, product_line: str):
        super().__init__()
        self._inst = inst
        self.app_name = app_name
        self.product_line = product_line

    def check_alive(self) -> bool:
        return True

    def choose_one(self) -> EndPoint:
        return self._inst

    def create_context(self,
                       method: MixedMethod,
                       invoker: Invoker,
                       service: RpcServiceInfo) -> InternalRequestContext:
        return InternalRequestContext(method, invoker, service, self.app_name, self.product_line)

    async def execute_async(self, req: EndPointRequest) -> RpcResponseResult:
        result_data = await req.execute_async(self._inst)
        return result_data

    async def stream_async(self, req: EndPointRequest) -> AsyncIterable[bytes]:
        result_stream = await req.stream_async(self._inst)
        return result_stream

    async def ws_async(self, req: EndPointRequest) -> websocket.WebSocket:
        conn = await req.ws_async(self._inst)
        return conn

    def execute(self, req: EndPointRequest) -> RpcResponseResult:
        result_data = req.execute(self._inst)
        return result_data

    def stream(self, req: EndPointRequest) -> Iterable[bytes]:
        result_stream = req.stream(self._inst)
        return result_stream

    def ws(self, req: EndPointRequest) -> websocket.WebSocket:
        conn = req.ws(self._inst)
        return conn
