from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import ASCI_MINUTES


class ASCIConfigCollector:
    def __init__(self) -> None:
        pass

    def describe(self) -> Iterable:
        return []

    def collect(self) -> Iterable:
        metric = GaugeMetricFamily("epo_asci_config_minutes", "Agent-Server Communication Interval (minutes)")
        metric.add_metric([], float(ASCI_MINUTES))
        yield metric


