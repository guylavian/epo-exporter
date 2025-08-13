from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_EVENTS_BY_PRODUCT_SEVERITY
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase


class EventsSeverityCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        metric = GaugeMetricFamily("epo_events_by_severity_total", "Threat events (window) by product and severity", labels=["product", "severity"])
        if not Q_EVENTS_BY_PRODUCT_SEVERITY:
            return [metric]
        rows = q(Q_EVENTS_BY_PRODUCT_SEVERITY)
        if isinstance(rows, list):
            for r in rows:
                product = get_str(r.get("AnalyzerName") or r.get("Product") or (r.get("attributes") or {}).get("AnalyzerName"))
                severity = get_str(r.get("Severity") or (r.get("attributes") or {}).get("Severity"))
                count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                if product and severity and count is not None:
                    metric.add_metric([product, severity], count)
        return [metric]

    def collect(self) -> Iterable:
        return super().collect()


