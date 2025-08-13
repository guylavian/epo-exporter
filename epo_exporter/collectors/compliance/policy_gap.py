from typing import Dict, Iterable

from prometheus_client.core import GaugeMetricFamily

from ...config import Q_INSTALLED_BY_PRODUCT, Q_REPORTING_ENDPOINTS_BY_PRODUCT
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase


class ProductGapCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        installed_g = GaugeMetricFamily(
            "epo_product_installed_endpoints", "Installed endpoints per product", labels=["product"]
        )
        reporting_g = GaugeMetricFamily(
            "epo_product_reporting_endpoints", "Reporting endpoints per product (in window)", labels=["product"]
        )
        gap_g = GaugeMetricFamily("epo_product_gap", "Installed - Reporting endpoints per product", labels=["product"])

        installed_map: Dict[str, int] = {}
        if Q_INSTALLED_BY_PRODUCT:
            rows = q(Q_INSTALLED_BY_PRODUCT)
            if isinstance(rows, list):
                for r in rows:
                    product = get_str(r.get("Product") or r.get("ProductName") or (r.get("attributes") or {}).get("Product"))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if product and count is not None:
                        installed_map[product] = count
                        installed_g.add_metric([product], count)

        reporting_map: Dict[str, int] = {}
        if Q_REPORTING_ENDPOINTS_BY_PRODUCT:
            rows2 = q(Q_REPORTING_ENDPOINTS_BY_PRODUCT)
            if isinstance(rows2, list):
                for r in rows2:
                    product = get_str(r.get("AnalyzerName") or r.get("analyzerName") or (r.get("attributes") or {}).get("AnalyzerName"))
                    count = get_int(r.get("DistinctSystems") or r.get("distinct") or r.get("COUNT") or r.get("count"))
                    if product and count is not None:
                        reporting_map[product] = count
                        reporting_g.add_metric([product], count)

        for p, inst in installed_map.items():
            rep = reporting_map.get(p, 0)
            gap_g.add_metric([p], max(inst - rep, 0))

        return [installed_g, reporting_g, gap_g]

    def collect(self) -> Iterable:
        return super().collect()


