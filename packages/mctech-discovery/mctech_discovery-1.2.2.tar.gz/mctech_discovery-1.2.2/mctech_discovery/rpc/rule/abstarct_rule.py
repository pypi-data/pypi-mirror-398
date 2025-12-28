from __future__ import absolute_import

import abc
import os
import py_eureka_client.eureka_client as eureka_client
from typing import Optional

from .._rpc_types import EndPoint

k8s = 'KUBERNETES_SERVICE_HOST' in os.environ


class AbstractRule:
    def __init__(self, app_id: str, eureka: eureka_client.EurekaClient):
        self._app_id = app_id
        self._app_id_upper = app_id.upper()
        self._eureka = eureka

    def choose_server(self) -> EndPoint:
        inst = self._choose()
        if not inst:
            raise RuntimeError('没有可用的服务实例: ' + self._app_id)

        if k8s and inst.vipAddress.endswith('.svc'):
            return EndPoint(id=inst.instanceId,
                            host=inst.vipAddress,
                            port=inst.port.port,
                            vip_address=True)

        return EndPoint(id=inst.instanceId,
                        host=inst.ipAddr,
                        port=inst.port.port,
                        vip_address=False)

    @abc.abstractmethod
    def _choose(self) -> Optional[eureka_client.Instance]:
        pass

    def compute(self):
        pass

    def record_stats(self, server_id: str, response_time: float):
        pass
