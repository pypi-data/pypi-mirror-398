from __future__ import absolute_import
import socket
import netifaces
from log4py import logging
from typing import Optional

from mctech_core import get_configure

from .local_discovery_client import LocalDiscoveryClient, DiscoveryClient
from .eureka_discovery_client import EurekaDiscoveryClient

_log = logging.getLogger('python.eureka.discoveryClient')


def _get_ip_address():
    '''
    获取本机ip
    '''

    result = []
    for iface in netifaces.interfaces():
        alias = netifaces.ifaddresses(iface)
        ipv4 = alias.get(netifaces.AF_INET)
        if ipv4 is None:
            continue
        for addr_info in ipv4:
            address = addr_info["addr"]
            if address == '127.0.0.1':
                continue
            result.append(addr_info["addr"])

    if len(result) == 0:
        raise RuntimeError('未找到合适的ipv4地址')

    if len(result) > 1:
        _log.warning('找到多个符合条件的ipv4地址: %s' % result)

    selected_address = result[0]
    _log.info('当前使用的ip地址: ' + selected_address)

    return selected_address


def __create_discovery_client() -> DiscoveryClient:
    ip_address = _get_ip_address()
    host_name = socket.gethostname()

    eureka_config = get_configure().get_config('eureka', {'enabled': True})
    discovery = EurekaDiscoveryClient(ip_address, host_name) if eureka_config["enabled"] \
        else LocalDiscoveryClient(ip_address, host_name)
    return discovery


_discovery_client: Optional[DiscoveryClient] = None


def get_discovery() -> DiscoveryClient:
    global _discovery_client
    if not _discovery_client:
        _discovery_client = __create_discovery_client()
    return _discovery_client


__all__ = [
    "get_discovery",
    "DiscoveryClient"
]
