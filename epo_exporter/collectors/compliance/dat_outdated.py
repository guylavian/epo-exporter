import time
from typing import Iterable

from prometheus_client.core import GaugeMetricFamily

from ...config import Q_DAT_OUTDATED
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase


class DatOutdatedCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        metric = GaugeMetricFamily(
            "epo_dat_outdated_total",
            "Endpoints that have not received the latest DAT (per product)",
            labels=["product"],
        )
        if not Q_DAT_OUTDATED:
            return [metric]

        rows = q(Q_DAT_OUTDATED)
        if isinstance(rows, list):
            for r in rows:
                product = get_str(r.get("Product") or r.get("AnalyzerName") or (r.get("attributes") or {}).get("Product"))
                count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                if product and count is not None:
                    metric.add_metric([product], count)
        return [metric]

    def collect(self) -> Iterable:
        return super().collect()


