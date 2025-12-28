from __future__ import absolute_import
import math
import py_eureka_client.eureka_client as eureka_client

from time import sleep
from typing import List, Dict, Optional
from random import random
from log4py import logging

from .abstarct_rule import AbstractRule

log = logging.getLogger('python.cloud.rpc.rule')


class RoundRobinRule(AbstractRule):
    def check_alive(self):
        apps = self._eureka.applications.get_application(self._app_id_upper)
        return len(apps.up_instances) > 0

    def _choose(self):
        if not self.check_alive():
            return None

        app = self._eureka.applications.get_application(self._app_id_upper)
        index = 0 if len(app.up_instances) == 1 else math.floor(random() * len(app.up_instances))
        inst = app.up_instances[index]
        return inst


class WeightedResponseTimeRule(RoundRobinRule):
    _accumulated_weights: List[float]
    _stats: Dict[str, "ServerStats"]

    def __init__(self, app_id, eureka: eureka_client.EurekaClient):
        super().__init__(app_id, eureka)
        self._accumulated_weights = []
        self._stats = {}

    def _choose(self):
        # /** @type {import('@mctech/eureka-js-client').EurekaClient.EurekaInstanceConfig} */
        server: Optional[eureka_client.Instance] = None
        while not server:
            # get hold of the current reference in case it is changed from the other thread
            current_weights = self._accumulated_weights
            app = self._eureka.applications.get_application(self._app_id)

            server_count = len(app.up_instances)
            if server_count == 0:
                return None

            server_index = 0
            # last one in the list is the sum of all weights
            max_total_weight = 0 if len(current_weights) == 0 else current_weights[-1]
            # No server has been hit yet and total weight is not initialized
            # fallback to use round robin
            if max_total_weight < 0.001 or server_count != len(current_weights):
                server = super()._choose()
                if not server:
                    return server
            else:
                # generate a random weight between 0 (inclusive) to maxTotalWeight(exclusive)
                random_weight = random() * max_total_weight
                # pick the server index based on the randomIndex
                n = 0
                for d in current_weights:
                    if d >= random_weight:
                        server_index = n
                        break
                    else:
                        n = n + 1

                server = app.up_instances[server_index]

            if not server:
                # 短暂停顿下
                sleep(0.001)
        return server

    def compute(self):
        if log.isEnabledFor(logging.DEBUG):
            log.debug('Weight adjusting job started')
        total_response_time = 0
        app = self._eureka.applications.get_application(self._app_id)

        # find maximal 95 % response time
        for inst in app.up_instances:
            # this will automatically load the stats if not in cache
            ss = self._stats.get(inst.instanceId)
            if not ss:
                continue
            total_response_time += ss.get_response_time_avg()
        # weight for each server is (sum of responseTime of all servers - responseTime)
        # so that the longer the response time, the less the weight and the less likely to be chosen
        weight_so_far = 0.0

        # create new list and hot swap the reference
        final_weights: List[float] = []
        for inst in app.up_instances:
            ss = self._stats.get(inst.instanceId)
            if not ss:
                continue
            weight = total_response_time - ss.get_response_time_avg()
            weight_so_far += weight
            final_weights.append(weight_so_far)
        self._accumulated_weights = final_weights

    def record_stats(self, server_id: str, response_time: float):
        server_stats = self._stats.get(server_id)
        if not server_stats:
            server_stats = ServerStats(server_id)
            self._stats[server_id] = server_stats
        server_stats.note_response_time(response_time)


class ServerStats:
    id: str
    # 总请求数
    num_values: int
    # 总用时
    sum_values: float

    def __init__(self, id: str):
        self.id = id
        self.num_values = 0
        self.sum_values = 0

    def note_response_time(self, response_time: float):
        self.num_values = self.num_values + 1
        self.sum_values += response_time

    def get_response_time_avg(self):
        return self.sum_values / self.num_values
