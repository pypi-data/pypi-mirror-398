from __future__ import absolute_import
import websocket
from typing import Iterable, AsyncIterable
from abc import ABC, abstractmethod

from ..request_context import RequestContext

from .._rpc_types import EndPoint, RpcResponseResult


class EndPointRequest(ABC):
    def __init__(self, context: RequestContext):
        self.context = context

    @abstractmethod
    async def execute_async(self, ep: EndPoint) -> RpcResponseResult:
        pass

    @abstractmethod
    async def stream_async(self, ep: EndPoint) -> AsyncIterable[bytes]:
        pass

    @abstractmethod
    async def ws_async(self, ep: EndPoint) -> websocket.WebSocket:
        pass

    @abstractmethod
    def execute(self, ep: EndPoint) -> RpcResponseResult:
        pass

    @abstractmethod
    def stream(self, ep: EndPoint) -> Iterable[bytes]:
        pass

    @abstractmethod
    def ws(self, ep: EndPoint) -> websocket.WebSocket:
        pass
