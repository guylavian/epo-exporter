from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_QUARANTINE_ITEMS
from ...api.client import call_onprem_api
from ...metrics import get_int, get_str
import time


class QuarantineCollector:
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache_until = 0.0
        self._cached = None

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        metric = GaugeMetricFamily("epo_quarantine_items_total", "Quarantine items (window) by product", labels=["product"])
        if not Q_QUARANTINE_ITEMS:
            return [metric]
        rows = call_onprem_api("core.executeQuery", {"queryId": Q_QUARANTINE_ITEMS})
        if isinstance(rows, list):
            for r in rows:
                product = get_str(r.get("Product") or r.get("AnalyzerName") or (r.get("attributes") or {}).get("Product"))
                count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                if product and count is not None:
                    metric.add_metric([product], count)
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


