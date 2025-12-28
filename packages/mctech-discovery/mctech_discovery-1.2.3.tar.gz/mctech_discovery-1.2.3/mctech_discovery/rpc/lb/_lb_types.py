from __future__ import absolute_import
import websocket
from typing import Iterable, AsyncIterable
from abc import ABC, abstractmethod

from ..request_context import RequestContext
from ..ep import EndPointRequest

from .._rpc_types import Invoker, RpcServiceInfo, EndPoint, MixedMethod, RpcResponseResult, CallMode


class LoadBalancer(ABC):
    @abstractmethod
    def create_context(self,
                       method: MixedMethod,
                       invoker: Invoker,
                       service: RpcServiceInfo) -> RequestContext:
        pass

    @abstractmethod
    def check_alive(self) -> bool:
        pass

    def request_async(self, method: CallMode, req: EndPointRequest):
        if method == 'execute':
            return self.execute_async(req)
        elif method == 'stream':
            return self.stream_async(req)
        elif method == 'ws':
            return self.ws_async(req)  # 底层创建websocket用的是同步方法，当前返回值会转换成异步调用的包装
        raise RuntimeError('不支持的方法:' + method)

    def request(self, method: CallMode, req: EndPointRequest):
        if method == 'execute':
            return self.execute(req)
        elif method == 'stream':
            return self.stream(req)
        elif method == 'ws':
            return self.ws(req)  # 底层创建websocket用的是同步方法，当前返回值会转换成异步调用的包装
        raise RuntimeError('不支持的方法:' + method)

    @abstractmethod
    async def execute_async(self, req: EndPointRequest) -> RpcResponseResult:
        pass

    @abstractmethod
    async def stream_async(self, req: EndPointRequest) -> AsyncIterable[bytes]:
        pass

    @abstractmethod
    async def ws_async(self, req: EndPointRequest) -> websocket.WebSocket:
        pass

    @abstractmethod
    def execute(self, req: EndPointRequest) -> RpcResponseResult:
        pass

    @abstractmethod
    def stream(self, req: EndPointRequest) -> Iterable[bytes]:
        pass

    @abstractmethod
    def ws(self, req: EndPointRequest) -> websocket.WebSocket:
        pass


class ServiceLoadBalancer(LoadBalancer):
    @abstractmethod
    def choose_one(self) -> EndPoint:
        pass
