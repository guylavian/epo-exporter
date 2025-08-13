from typing import Iterable

from prometheus_client.core import GaugeMetricFamily

from ...config import Q_POLICY_ASSIGNMENTS
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase


class PolicyCoverageCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        pol_assigned = GaugeMetricFamily(
            "epo_policy_assigned_systems",
            "Number of endpoints assigned to the policy",
            labels=["product", "policy"],
        )
        if Q_POLICY_ASSIGNMENTS:
            rows = q(Q_POLICY_ASSIGNMENTS)
            if isinstance(rows, list):
                for r in rows:
                    product = get_str(r.get("Product") or (r.get("attributes") or {}).get("Product"))
                    policy = get_str(r.get("Policy") or r.get("PolicyName") or (r.get("attributes") or {}).get("Policy"))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if product and policy and count is not None:
                        pol_assigned.add_metric([product, policy], count)
        return [pol_assigned]

    def collect(self) -> Iterable:
        return super().collect()


