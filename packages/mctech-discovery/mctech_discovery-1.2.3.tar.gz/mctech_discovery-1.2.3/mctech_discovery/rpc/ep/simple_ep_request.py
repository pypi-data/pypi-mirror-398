from __future__ import absolute_import
import websocket
from typing import Iterable, AsyncIterable

from .ep_request import EndPointRequest
from .internal_rpc import execute as rpc_execute, stream as rpc_stream, ws as rpc_ws, \
    execute_async as rpc_execute_async, stream_async as rpc_stream_async, ws_async as rpc_ws_async

from .._rpc_types import EndPoint, RpcResponseResult


class SimpleEndPointRequest (EndPointRequest):
    async def execute_async(self, ep: EndPoint) -> RpcResponseResult:
        resultData = await rpc_execute_async(self.context, ep)
        return resultData

    async def stream_async(self, ep: EndPoint) -> AsyncIterable[bytes]:
        resultStream = await rpc_stream_async(self.context, ep)
        return resultStream

    async def ws_async(self, ep: EndPoint) -> websocket.WebSocket:
        conn = await rpc_ws_async(self.context, ep)
        return conn

    def execute(self, ep: EndPoint) -> RpcResponseResult:
        resultData = rpc_execute(self.context, ep)
        return resultData

    def stream(self, ep: EndPoint) -> Iterable[bytes]:
        resultStream = rpc_stream(self.context, ep)
        return resultStream

    def ws(self, ep: EndPoint) -> websocket.WebSocket:
        conn = rpc_ws(self.context, ep)
        return conn
