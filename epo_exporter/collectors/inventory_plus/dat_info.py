from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_DAT_INFO
from ...api.client import call_onprem_api
from ...metrics import get_str
import time


class DatInfoCollector:
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache_until = 0.0
        self._cached = None

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        metric = GaugeMetricFamily("epo_dat_info", "DAT version info (1 for present)", labels=["product", "version"])
        if not Q_DAT_INFO:
            return [metric]
        rows = call_onprem_api("core.executeQuery", {"queryId": Q_DAT_INFO})
        if isinstance(rows, list):
            for r in rows:
                product = get_str(r.get("Product") or (r.get("attributes") or {}).get("Product"))
                version = get_str(r.get("Version") or r.get("DATVersion") or (r.get("attributes") or {}).get("Version"))
                if product and version:
                    metric.add_metric([product, version], 1)
        return [metric]

    def collect(self) -> Iterable:
        now = time.time()
        if self.cache_ttl_seconds and now < self._cache_until and self._cached is not None:
            for x in self._cached:
                yield x
            return
        metrics = self._collect_now()
        self._cached = metrics
        self._cache_until = now + self.cache_ttl_seconds
        for x in metrics:
            yield x


