from typing import Iterable

from prometheus_client.core import GaugeMetricFamily

from ...config import Q_EVENTS_BY_PRODUCT
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase


class ProductEventsCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        events_g = GaugeMetricFamily(
            "epo_events_total", "Number of threat events in the saved query window (by product)", labels=["product"]
        )
        if Q_EVENTS_BY_PRODUCT:
            rows = q(Q_EVENTS_BY_PRODUCT)
            if isinstance(rows, list):
                for r in rows:
                    product = get_str(r.get("AnalyzerName") or r.get("analyzerName") or (r.get("attributes") or {}).get("AnalyzerName"))
                    count = r.get("COUNT") or r.get("count") or r.get("Total")
                    ival = get_int(count)
                    if product and ival is not None:
                        events_g.add_metric([product], ival)
        return [events_g]


