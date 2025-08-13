from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_AGENT_VERSION_DIST, Q_PRODUCT_VERSION_DIST
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase
from ...runtime.utils import topn_with_other, sanitize_label
import os


TOPN = int(os.getenv("EPO_TOPN", "50"))


class VersionDistributionCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        super().__init__(cache_ttl_seconds)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        agent = GaugeMetricFamily("epo_agent_version_distribution", "Agent version distribution", labels=["version"])
        prod = GaugeMetricFamily("epo_product_version_distribution", "Product version distribution", labels=["product", "version"])

        if Q_AGENT_VERSION_DIST:
            rows = q(Q_AGENT_VERSION_DIST) or []
            if isinstance(rows, list):
                head, other = topn_with_other(rows, key=lambda r: get_int(r.get("COUNT") or 0) or 0, n=TOPN)
                for r in head:
                    version = sanitize_label(get_str(r.get("AgentVersion") or r.get("Version") or (r.get("attributes") or {}).get("Version")))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if version and count is not None:
                        agent.add_metric([version], count)
                if other:
                    agent.add_metric(["other"], other)

        if Q_PRODUCT_VERSION_DIST:
            rows = q(Q_PRODUCT_VERSION_DIST) or []
            if isinstance(rows, list):
                head, other = topn_with_other(rows, key=lambda r: get_int(r.get("COUNT") or 0) or 0, n=TOPN)
                for r in head:
                    product = sanitize_label(get_str(r.get("Product") or (r.get("attributes") or {}).get("Product")))
                    version = sanitize_label(get_str(r.get("Version") or (r.get("attributes") or {}).get("Version")))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if product and version and count is not None:
                        prod.add_metric([product, version], count)
                if other:
                    prod.add_metric(["other", "other"], other)

        return [agent, prod]

    def collect(self) -> Iterable:
        return super().collect()


