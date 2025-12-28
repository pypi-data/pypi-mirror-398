from __future__ import absolute_import
import os

from fastapi.responses import JSONResponse
from typing import Dict
from urllib.parse import urlparse
from threading import Timer

from mctech_core import get_configure
from mctech_actuator import get_health_manager, MetricIndicator

from .direct_loadbalancer import DirectLoadBalancer
from .discovery_service_loadbalancer import DiscoveryServiceLoadBalancer
from .local_service_loadabalancer import LocalServiceLoadBalancer
from .retry_loadbalancer import RetryLoadBalancer
from ...discovery import get_discovery

from .._rpc_types import RpcServiceInfo, EndPoint
from ._lb_types import LoadBalancer, ServiceLoadBalancer

# gateway = GatewayLoadBalancer()
_direct = DirectLoadBalancer()


_load_balance_cache: Dict[str, ServiceLoadBalancer] = {}
_local_service: Dict[str, EndPoint] = {}
_dependencies: Dict[str, bool] = {}


async def _metric_endpoint():
    return JSONResponse([v for v in _load_balance_cache.keys()])


get_health_manager().add_metric(MetricIndicator(
    # 相对于/actuator/metrics的路径，必须以'/'开头
    path='/dependencies',
    endpoint=_metric_endpoint
))

CHECK_ALIVE_INTERVAL = 5

# 定时检查目标服务的信息是否还有效，如果不存在了，则会移除


def print_time():
    invalidates = []
    for serviceId, lb in _load_balance_cache.items():
        if not lb.check_alive():
            invalidates.append(serviceId)

    # 存在失效的服务，从缓存中移除
    if len(invalidates) > 0:
        for service_id in invalidates:
            del _load_balance_cache[service_id]


# 指定1秒后执行print_time函数
t = Timer(CHECK_ALIVE_INTERVAL, print_time)
t.start()


app_name = 'unknown'
product_line = 'unknown'


def _load_config():
    configure = get_configure()
    config = configure.get_config('mctech.rpc.service')
    global app_name, product_line
    app_name = configure.get_app_info().get('name') or 'unknown'

    k8s = os.environ.get("KUBERNETES_SERVICE_HOST")
    if k8s:
        # 在k8s运行环境，服务名称使用k8s带名字空间的完整名称
        product_line = os.environ.get("PRODUCT_LINE") or 'unknown'

    for service_id, service_url in config.items():
        result = urlparse(service_url)
        _local_service[service_id] = EndPoint(
            id=service_id,
            vip_address=False,
            host=result.hostname,
            port=result.port
        )


def create(retry: int, service: RpcServiceInfo) -> LoadBalancer:
    if not app_name:
        _load_config()

    retry = retry or 0
    rpc_type = service.rpc_type if service.rpc_type else 'internal'

    # lb: LoadBalancer
    # if type == 'gateway':
    #   lb = gateway
    # el
    if rpc_type == 'internal':
        lb = _direct if not service.service_id else _get_service_loadbalancer(service.service_id)
    else:
        raise RuntimeError('不支持的调用方式')

    if retry > 0:
        lb = RetryLoadBalancer(lb)
    return lb


def _get_service_loadbalancer(service_id: str) -> ServiceLoadBalancer:
    lb = _load_balance_cache.get(service_id)
    if not lb:
        inst = _local_service.get(service_id)
        if inst:
            lb = LocalServiceLoadBalancer(inst, app_name, product_line)
        elif not get_discovery().isLocal:
            lb = DiscoveryServiceLoadBalancer(service_id, app_name, product_line)
        else:
            raise RuntimeError(
                "本地调用配置中未找到service_id为: '%s'的服务" % service_id
            )

        _load_balance_cache[service_id] = lb
        _dependencies[service_id] = True
    return lb


def get_service_info(service_id: str) -> EndPoint:
    '''
    获取内部服务注册信息
    '''
    lb = _get_service_loadbalancer(service_id)
    inst = lb.choose_one()
    return inst


__all__ = [
    "create",
    "get_service_info"
]
