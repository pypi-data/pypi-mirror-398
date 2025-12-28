from __future__ import absolute_import
import websocket

from datetime import datetime
from log4py import logging
from typing import Iterable, AsyncIterable

from ._lb_types import ServiceLoadBalancer
from ..request_context import InternalRequestContext
from ..ep import EndPointRequest
from ..rule import WeightedResponseTimeRule
from ...discovery import get_discovery

from .._rpc_types import Invoker, RpcServiceInfo, EndPoint, MixedMethod, RpcResponseResult

log = logging.getLogger('python.cloud.rpc.loadbalancer')


class DiscoveryServiceLoadBalancer(ServiceLoadBalancer):
    '''
    通过Eureka服务动态获取可用的服务端地址的实现
    '''

    def __init__(self, service_id: str, app_name: str, product_line: str):
        super().__init__()
        self.service_id = service_id
        self.app_name = app_name
        self.product_line = product_line
        self._rule = WeightedResponseTimeRule(service_id, get_discovery().client)

    def check_alive(self) -> bool:
        # 重新计算各节点权重值
        try:
            if self._rule.check_alive():
                self._rule.compute()
                return True
        except Exception as err:
            log.error('Error calculating server weights', err)

        # 目标服务例不在线或者计算权重失败时都返回false
        return False

    def choose_one(self) -> EndPoint:
        inst = self._rule.choose_server()
        return inst

    def create_context(self,
                       method: MixedMethod,
                       invoker: Invoker,
                       service: RpcServiceInfo) -> InternalRequestContext:
        return InternalRequestContext(method, invoker, service, self.app_name, self.product_line)

    async def execute_async(self, req: EndPointRequest) -> RpcResponseResult:
        async def cb(inst: EndPoint) -> RpcResponseResult:
            result_data = await req.execute_async(inst)
            return result_data
        return await self._execute_with_scope_async(cb)

    async def stream_async(self, req: EndPointRequest) -> AsyncIterable[bytes]:
        async def cb(inst: EndPoint) -> AsyncIterable[bytes]:
            result_stream = await req.stream_async(inst)
            return result_stream
        return await self._execute_with_scope_async(cb)

    async def ws_async(self, req: EndPointRequest) -> websocket.WebSocket:
        async def cb(inst: EndPoint) -> websocket.WebSocket:
            conn = await req.ws_async(inst)
            return conn
        return await self._execute_with_scope_async(cb)

    def execute(self, req: EndPointRequest) -> RpcResponseResult:
        def cb(inst: EndPoint) -> RpcResponseResult:
            result_data = req.execute(inst)
            return result_data
        return self._execute_with_scope(cb)

    def stream(self, req: EndPointRequest) -> Iterable[bytes]:
        def cb(inst: EndPoint) -> Iterable[bytes]:
            result_stream = req.stream(inst)
            return result_stream
        return self._execute_with_scope(cb)

    def ws(self, req: EndPointRequest) -> websocket.WebSocket:
        def cb(inst: EndPoint) -> websocket.WebSocket:
            conn = req.ws(inst)
            return conn
        return self._execute_with_scope(cb)

    async def _execute_with_scope_async(self, callback):
        inst = self._rule.choose_server()

        if log.isEnabledFor(logging.DEBUG):
            log.debug('获取到服务实例: ' + inst.id)
        begin = datetime.now()
        try:
            ret = await callback(inst)
            return ret
        finally:
            end = datetime.now()
            duration = end - begin
            self._rule.record_stats(inst.id, duration.total_seconds())

    def _execute_with_scope(self, callback):
        inst = self._rule.choose_server()
        assert inst is not None, '没有可用的服务实例:' + self.service_id

        if log.isEnabledFor(logging.DEBUG):
            log.debug('获取到服务实例: ' + inst.id)
        begin = datetime.now()
        try:
            ret = callback(inst)
            return ret
        finally:
            end = datetime.now()
            duration = end - begin
            self._rule.record_stats(inst.id, duration.total_seconds())
