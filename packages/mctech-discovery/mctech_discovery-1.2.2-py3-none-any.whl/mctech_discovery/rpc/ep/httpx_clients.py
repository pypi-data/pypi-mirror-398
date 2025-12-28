from __future__ import absolute_import
from threading import Lock
from typing import Optional, TypeVar, Generic, Callable
from functools import partial

from httpx._client import BaseClient
from httpx import Client, AsyncClient, Request, Timeout, USE_CLIENT_DEFAULT

from .._rpc_types import Seconds


_CLIENT_RPC_TIMEOUT = Timeout(10.0, connect=3.0)
_ACCEPT_VALUE = 'application/json, application/xml, */*'

_DEFAULT_HEADERS = {
    'Accept': _ACCEPT_VALUE,
    'Accept-Language': 'zh-CN',
    'Accept-Encoding': 'gzip,deflate',
    'User-Agent': 'nodejs rest client',
    # 表示异步调用
    'X-Client-Ajax': 'true'
}

_for_request = BaseClient(headers=_DEFAULT_HEADERS, timeout=_CLIENT_RPC_TIMEOUT)


TClient = TypeVar("TClient")


class _Atomic(Generic[TClient]):
    _lock = Lock()
    _value: Optional[TClient]

    def __init__(self, lazy_create: Callable[[bool], TClient], *kargs):
        self._lazy_create = partial(lazy_create, *kargs)
        self._value = None

    def pop(self) -> Optional[TClient]:
        v = self._value
        if v:
            with self._lock:
                self._value = None
        return v

    def get(self) -> TClient:
        if self._value is None:
            with self._lock:
                if self._value is None:
                    self._value = self._lazy_create()
        return self._value


class _Clients(Generic[TClient]):
    _client: _Atomic[TClient]
    _disable_verify_client: _Atomic[TClient]

    def __init__(self, cls):
        self._client = _Atomic(
            lambda v: cls(headers=_DEFAULT_HEADERS, verify=v, timeout=_CLIENT_RPC_TIMEOUT),
            True
        )
        self._disable_verify_client = _Atomic(
            lambda v: cls(headers=_DEFAULT_HEADERS, verify=v, timeout=_CLIENT_RPC_TIMEOUT),
            False
        )

    def build_request(self, **kwargs) -> Request:
        # 所有的client创建的Request的方法都是一样的，这里随便选择了一个
        return _for_request.build_request(**kwargs)

    def create_timeout(self, timeout: Optional[Seconds]):
        if timeout is None:
            return USE_CLIENT_DEFAULT
        return Timeout(_CLIENT_RPC_TIMEOUT, read=timeout)

    def get_client(self, verify: bool) -> TClient:
        if verify:
            return self._client.get()
        return self._disable_verify_client.get()


class Clients(_Clients[Client]):
    def __init__(self):
        super().__init__(Client)

    def close(self):
        c = self._client.pop()
        if c:
            c.close()
        c = self._disable_verify_client.pop()
        if c:
            c.close()


class AsyncClients(_Clients[AsyncClient]):
    def __init__(self):
        super().__init__(AsyncClient)

    async def aclose(self):
        c = self._client.pop()
        if c:
            await c.aclose()
        c = self._disable_verify_client.pop()
        if c:
            await c.aclose()


clients = Clients()
async_clients = AsyncClients()
