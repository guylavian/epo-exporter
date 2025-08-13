from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_REPOSITORY_STATUS
from ...api.client import call_onprem_api
from ...metrics import get_int, get_str
import time


class RepositoryStatusCollector:
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache_until = 0.0
        self._cached = None

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        status = GaugeMetricFamily("epo_repository_mirror_status", "Repository mirror status (1 ok, 0 error)", labels=["repo"])
        age = GaugeMetricFamily("epo_repository_mirror_age_seconds", "Repository mirror age in seconds", labels=["repo"])

        if not Q_REPOSITORY_STATUS:
            return [status, age]

        rows = call_onprem_api("core.executeQuery", {"queryId": Q_REPOSITORY_STATUS})
        if isinstance(rows, list):
            for r in rows:
                repo = get_str(r.get("Repository") or r.get("Repo") or (r.get("attributes") or {}).get("Repository"))
                st = get_str(r.get("Status") or (r.get("attributes") or {}).get("Status"))
                age_val = get_int(r.get("AgeSeconds") or (r.get("attributes") or {}).get("AgeSeconds"))
                if repo:
                    ok = 1 if (st or "").lower() in ("ok", "success", "synced", "healthy") else 0
                    status.add_metric([repo], ok)
                    if age_val is not None:
                        age.add_metric([repo], age_val)
        return [status, age]

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


