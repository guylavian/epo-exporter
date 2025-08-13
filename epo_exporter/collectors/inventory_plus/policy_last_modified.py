from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_POLICY_LAST_MODIFIED
from ...api.client import call_onprem_api
from ...metrics import get_str, parse_epoch_or_iso
import time


class PolicyLastModifiedCollector:
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache_until = 0.0
        self._cached = None

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        metric = GaugeMetricFamily("epo_policy_last_modified_timestamp", "Policy last modified time", labels=["product", "policy"])
        if not Q_POLICY_LAST_MODIFIED:
            return [metric]
        rows = call_onprem_api("core.executeQuery", {"queryId": Q_POLICY_LAST_MODIFIED})
        if isinstance(rows, list):
            for r in rows:
                product = get_str(r.get("Product") or (r.get("attributes") or {}).get("Product"))
                policy = get_str(r.get("Policy") or r.get("PolicyName") or (r.get("attributes") or {}).get("Policy"))
                ts_raw = r.get("LastModified") or (r.get("attributes") or {}).get("LastModified")
                ts = parse_epoch_or_iso(ts_raw) or 0
                if product and policy and ts:
                    metric.add_metric([product, policy], ts)
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


