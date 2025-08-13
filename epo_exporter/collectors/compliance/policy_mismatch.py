from typing import Dict, Iterable

from prometheus_client.core import GaugeMetricFamily

from ...config import ASCI_MINUTES, ASCI_OVERDUE_MULTIPLIER, Q_MANAGED_COMM
from ...api.endpoints import q
from ...metrics import get_str, parse_epoch_or_iso
from ...runtime.base import CachingCollectorBase


class PolicyMismatchCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        pol_mismatch = GaugeMetricFamily(
            "epo_policy_mismatch_total", "Endpoints with stale/uneffective policy", labels=["product", "policy"]
        )
        agents_overdue = GaugeMetricFamily("epo_agents_overdue_total", "Agents overdue (no communication)")

        overdue_threshold_secs = int(ASCI_MINUTES * 60 * ASCI_OVERDUE_MULTIPLIER)
        now = time.time()

        overdue_count = 0
        if Q_MANAGED_COMM:
            rows = q(Q_MANAGED_COMM)
            if isinstance(rows, list):
                mismatch_map: Dict[tuple, int] = {}
                for r in rows:
                    product = get_str(r.get("Product") or (r.get("attributes") or {}).get("Product"))
                    policy = get_str(r.get("Policy") or r.get("PolicyName") or (r.get("attributes") or {}).get("Policy"))
                    last_comm = r.get("LastCommunication") or (r.get("attributes") or {}).get("LastCommunication")
                    last_policy = r.get("LastPolicyUpdate") or (r.get("attributes") or {}).get("LastPolicyUpdate")

                    lc = parse_epoch_or_iso(last_comm)
                    lp = parse_epoch_or_iso(last_policy)
                    if lc is None:
                        continue
                    if (now - lc) > overdue_threshold_secs:
                        overdue_count += 1
                    if lp is not None and lc is not None and lp < (lc - 1):
                        key = (product or "unknown", policy or "unknown")
                        mismatch_map[key] = mismatch_map.get(key, 0) + 1

                for (prod, pol), cnt in mismatch_map.items():
                    pol_mismatch.add_metric([prod, pol], cnt)

        agents_overdue.add_metric([], overdue_count)
        return [pol_mismatch, agents_overdue]

    def collect(self) -> Iterable:
        return super().collect()


