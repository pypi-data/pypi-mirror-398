from __future__ import absolute_import
from typing import Dict, Any
from datetime import datetime
from py_eureka_client.eureka_client import EurekaClient

from mctech_actuator import Health, HealthBuilder, Status, CompositeHealthIndicator


class EurekaDiscoveryCompositeHealthIndicator(CompositeHealthIndicator):
    def __init__(self, client: EurekaClient, instanceConfig: Dict[str, Any], clientConfig: Dict[str, Any]):
        super().__init__()

        discovery = EurekaDiscoveryClientHealthIndicator(client)
        eureka = EurekaHealthIndicator(client, instanceConfig, clientConfig)

        self.add_indicator(discovery._name, discovery)
        self.add_indicator(eureka.name, eureka)

    @property
    def name(self) -> str:
        return 'discoveryComposite'


class EurekaDiscoveryClientHealthIndicator:
    _name: str
    _client: EurekaClient
    _discovery_initialized: bool

    def __init__(self, client: EurekaClient):
        self._name = 'discoveryClient'
        self._client = client
        self._discovery_initialized = False

        # @ts-ignore 本来继承自EventEmitter，但是导出类型描述没有添加
        # client.once('registered', () => {
        #   this._discovery_initialized = true
        # })

    def health(self) -> Health:
        builder = Health.new_builder('UNKNOWN')
        if self._discovery_initialized:
            services = [app.name for app in self._client.applications.applications]
            builder \
                .status('UP', description='Node Cloud Eureka Discovery Client') \
                .add_detail('services', services)
        else:
            builder.status('UNKNOWN', description='Discovery Client not initialized')
        return builder.build()


class EurekaHealthIndicator:
    name: str
    _client: EurekaClient
    _instanceConfig: Dict[str, Any]
    _clientConfig: Dict[str, Any]
    _last_successful_registry_fetch_timestamp: int

    def __init__(self, client: EurekaClient, instanceConfig: Dict[str, Any], clientConfig: Dict[str, Any]):
        self.name = 'eureka'

        self._client = client
        self._instanceConfig = instanceConfig
        self._clientConfig = clientConfig
        self._last_successful_registry_fetch_timestamp = -1
        # @ts-ignore 本来继承自EventEmitter，但是导出类型描述没有添加
        # client.on('heartbeat', () => {
        #   this.last_successful_timestamp = Date.now()
        # })

    def health(self) -> Health:
        builder = Health.unknown()
        status = self._get_status(builder)
        return builder \
            .status(status) \
            .add_detail('applications', self._get_applications()) \
            .build()

    def _get_applications(self):
        services = [app.name for app in self._client.applications.applications]

        apps = {}
        for key in services:
            apps[key] = len(self._client.applications.get_application(key).instances)
        return apps

    def _get_instance_remote_status(self):
        if self._client.should_discover:
            app = self._client.applications.get_application(self._client.__instance['app'])
            if app:
                instance = app.get_instance(self._client.__instance['instanceId'])
                if instance:
                    return instance.status
        return 'UNKNOWN'

    def _get_status(self, builder: HealthBuilder) -> Status:
        status = Status(self._get_instance_remote_status(), 'Remote status from Eureka server')
        if self._clientConfig['fetchRegistry']:
            last_fetch = self._last_successful_registry_fetch_timestamp
            if last_fetch > 0:
                last_fetch = round(datetime.now().timestamp()) - self._last_successful_registry_fetch_timestamp

            if last_fetch < 0:
                status = Status(
                    'UP',
                    'Eureka discovery client has not yet successfully connected to a Eureka server'
                )
            elif last_fetch > self._clientConfig['registryFetchInterval'] * 2000:
                status = Status(
                    'UP',
                    'Eureka discovery client is reporting failures to connect to a Eureka server'
                )

                # 分析源码后可知 __heartbeat_interval 与 __instance['leaseInfo']['renewalIntervalInSecs'] 值完全相同
                builder.add_detail('renewalPeriod', self._instanceConfig['leaseInfo']['renewalIntervalInSecs'] or 30)
                builder.add_detail('failCount', round(last_fetch / self._clientConfig['registryFetchInterval']))

        return status
