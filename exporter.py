"""
Objects and methods to create Prometheus exporter instance
"""
from os import environ
from queue import Queue
from prometheus_client.core import GaugeMetricFamily


class DhcpdPoolsExporter:
    """
    Prometheus exporter
    """

    def __init__(self, metrics_queue: Queue) -> None:
        """
        Metrics collector for pool utilisation metrics.
        """
        self.host = environ["HOST"]
        self.metrics_queue = metrics_queue

    def collect(self) -> GaugeMetricFamily:
        """
        Collect metrics
        """
        if not self.metrics_queue.empty():
            self.stats = self.metrics_queue.get()
            self.gauge = GaugeMetricFamily(
                name="dhcpd_pools_util",
                documentation="DHCP server pools utilisation",
                labels=["host", "pool", "router"],
            )
            if self.stats:
                for pool in list(self.stats.keys()):
                    self.gauge.add_metric(
                        labels=[self.host, pool, self.stats[pool]["router"]],
                        value=self.stats[pool]["percentage"],
                    )
                yield self.gauge
