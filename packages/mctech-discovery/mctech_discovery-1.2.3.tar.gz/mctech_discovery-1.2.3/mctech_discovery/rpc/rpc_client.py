from __future__ import absolute_import

from typing import Callable, Iterable, AsyncIterable
from websocket import WebSocket

from .ep import EndPointRequest, SimpleEndPointRequest
from .request_context import RequestContext
from ..rpc import lb as lb_factory

from ._rpc_types import WebSocketInvoker, RpcInvoker, PipeRpcInvoker, Invoker, RpcServiceInfo, \
    HttpMethod, MixedMethod, RpcResponseResult, CallMode


RequestCreatorType = Callable[[RequestContext], EndPointRequest]


class AbstractClient:
    _request_creator: RequestCreatorType

    def __init__(self, creator: RequestCreatorType):
        self._request_creator = creator

    async def _do_rpc_request_async(self, method: HttpMethod, invoker: Invoker,
                                    service: RpcServiceInfo, mode: CallMode):
        if mode == 'stream' and not method:
            raise RuntimeError(method, '使用stream方法，invoker.method不能为空')
        r = await self._do_request_async(method, invoker, service, mode)
        assert not isinstance(r, WebSocket)
        return r

    async def _do_request_async(self, method: MixedMethod, invoker: Invoker,
                                service: RpcServiceInfo, mode: CallMode):
        retry = (invoker.retry or 0) if isinstance(invoker, RpcInvoker) else 0 or 0
        lb = lb_factory.create(retry, service)
        context = lb.create_context(method, invoker, service)
        ep_request = self._request_creator(context)

        return await lb.request_async(mode, ep_request)

    def _do_rpc_request(self, method: HttpMethod, invoker: Invoker,
                        service: RpcServiceInfo, mode: CallMode):
        if mode == 'stream' and not method:
            raise RuntimeError(method, '使用stream方法，invoker.method不能为空')
        r = self._do_request(method, invoker, service, mode)
        assert not isinstance(r, WebSocket)
        return r

    def _do_request(self, method: MixedMethod, invoker: Invoker,
                    service: RpcServiceInfo, mode: CallMode):
        retry = (invoker.retry or 0) if isinstance(invoker, RpcInvoker) else 0 or 0
        lb = lb_factory.create(retry, service)
        context = lb.create_context(method, invoker, service)
        ep_request = self._request_creator(context)

        return lb.request(mode, ep_request)


class RpcClient(AbstractClient):
    async def get_async(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = await self._do_rpc_request_async('get', invoker, service, 'execute')
        return r

    async def post_async(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = await self._do_rpc_request_async('post', invoker, service, 'execute')
        return r

    async def put_async(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = await self._do_rpc_request_async('put', invoker, service, 'execute')
        return r

    async def patch_async(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = await self._do_rpc_request_async('patch', invoker, service, 'execute')
        return r

    async def delete_async(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = await self._do_rpc_request_async('delete', invoker, service, 'execute')
        return r

    async def stream_async(self, invoker: PipeRpcInvoker, service: RpcServiceInfo) -> AsyncIterable[bytes]:
        r = await self._do_rpc_request_async(invoker.method, invoker, service, 'stream')
        assert isinstance(r, AsyncIterable)
        return r

    async def ws_async(self, invoker: WebSocketInvoker, service: RpcServiceInfo) -> WebSocket:
        r = await self._do_request_async('ws', invoker, service, 'ws')
        assert isinstance(r, WebSocket)
        return r

    def get(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = self._do_rpc_request('get', invoker, service, 'execute')
        return r

    def post(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = self._do_rpc_request('post', invoker, service, 'execute')
        return r

    def put(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = self._do_rpc_request('put', invoker, service, 'execute')
        return r

    def patch(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = self._do_rpc_request('patch', invoker, service, 'execute')
        return r

    def delete(self, invoker: RpcInvoker, service: RpcServiceInfo) -> RpcResponseResult:
        r = self._do_rpc_request('delete', invoker, service, 'execute')
        return r

    def stream(self, invoker: PipeRpcInvoker, service: RpcServiceInfo) -> Iterable[bytes]:
        r = self._do_rpc_request(invoker.method, invoker, service, 'stream')
        assert isinstance(r, Iterable)
        return r

    def ws(self, invoker: WebSocketInvoker, service: RpcServiceInfo) -> WebSocket:
        r = self._do_request('ws', invoker, service, 'ws')
        assert isinstance(r, WebSocket)
        return r

    def bind(self, service: RpcServiceInfo):
        '''
        需要调用的服务的信息
        '''
        return ServiceBindedRpcClient(self._request_creator, service)

    def set_creator(self, creator: RequestCreatorType):
        if not creator:
            raise RuntimeError('creator不能为空值')

        self._request_creator = creator


class ServiceBindedRpcClient(AbstractClient):
    _service: RpcServiceInfo

    def __init__(self, creator: RequestCreatorType, service: RpcServiceInfo):
        super().__init__(creator)
        self._service = service

    async def get_async(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = await self._do_rpc_request_async('get', invoker, self._service, 'execute')
        return r

    async def post_async(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = await self._do_rpc_request_async('post', invoker, self._service, 'execute')
        return r

    async def put_async(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = await self._do_rpc_request_async('put', invoker, self._service, 'execute')
        return r

    async def patch_async(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = await self._do_rpc_request_async('patch', invoker, self._service, 'execute')
        return r

    async def delete_async(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = await self._do_rpc_request_async('delete', invoker, self._service, 'execute')
        return r

    async def stream_async(self, invoker: PipeRpcInvoker) -> AsyncIterable[bytes]:
        r = await self._do_rpc_request_async(invoker.method, invoker, self._service, 'stream')
        assert isinstance(r, AsyncIterable)
        return r

    async def ws_async(self, invoker: WebSocketInvoker) -> WebSocket:
        r = await self._do_request_async('ws', invoker, self._service, 'ws')
        assert isinstance(r, WebSocket)
        return r

    def get(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = self._do_rpc_request('get', invoker, self._service, 'execute')
        return r

    def post(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = self._do_rpc_request('post', invoker, self._service, 'execute')
        return r

    def put(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = self._do_rpc_request('put', invoker, self._service, 'execute')
        return r

    def patch(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = self._do_rpc_request('patch', invoker, self._service, 'execute')
        return r

    def delete(self, invoker: RpcInvoker) -> RpcResponseResult:
        r = self._do_rpc_request('delete', invoker, self._service, 'execute')
        return r

    def stream(self, invoker: PipeRpcInvoker) -> Iterable[bytes]:
        r = self._do_rpc_request(invoker.method, invoker, self._service, 'stream')
        assert isinstance(r, Iterable)
        return r

    def ws(self, invoker: WebSocketInvoker) -> WebSocket:
        r = self._do_request('ws', invoker, self._service, 'execute')
        assert isinstance(r, WebSocket)
        return r


_rpc_client = RpcClient(lambda context: SimpleEndPointRequest(context))


def get_rpc_client() -> RpcClient:
    return _rpc_client
