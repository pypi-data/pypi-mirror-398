from __future__ import absolute_import
from abc import ABC, abstractmethod
from typing import Any

from mctech_core.config import AppInfo

from mctech_core import get_configure, Configure


class DiscoveryClient(ABC):
    @property
    @abstractmethod
    def isLocal(self) -> bool:
        pass

    @property
    @abstractmethod
    def local_instance(self) -> dict[str, Any]:
        pass

    @property
    @abstractmethod
    def client(self) -> Any:
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def register(self):
        pass

    @abstractmethod
    def unregister(self):
        pass

    @abstractmethod
    def load_config(self) -> Configure:
        pass


class LocalDiscoveryClient(DiscoveryClient):
    _info: AppInfo
    _local_address: str
    _host_name: str

    def __init__(self, local_address: str, host_name: str):
        self._info = get_configure().get_app_info()
        self._local_address = local_address
        self._host_name = host_name

    @property
    def local_instance(self):
        return {
            'hostName': self._host_name,
            'app': self._info.get("name"),
            'ipAddr': self._local_address,
            'port': self._info.get("port")
        }

    @property
    def isLocal(self):
        return True

    @property
    def client(self):
        raise RuntimeError('LocalDiscoveryClient不支持client属性')

    def start(self):
        # 什么也不做
        pass

    def register(self):
        # 什么也不做
        pass

    def unregister(self):
        # 什么也不做
        pass

    def load_config(self):
        return get_configure()
