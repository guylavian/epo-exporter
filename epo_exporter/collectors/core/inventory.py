from typing import Dict, Iterable

from prometheus_client.core import GaugeMetricFamily

from ...api.endpoints import system_find, policy_find, system_list_tags
from ...runtime.base import CachingCollectorBase


class InventoryCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: float | None = None) -> None:
        super().__init__(cache_ttl_seconds, scrape_timeout)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        managed_cnt = GaugeMetricFamily("epo_managed_systems_count", "Number of managed systems")
        policies_cnt = GaugeMetricFamily("epo_policies_count", "Number of policies configured in ePO")
        tags_cnt = GaugeMetricFamily("epo_tags_count_total", "Number of tags defined in ePO")

        systems = system_find("")
        if isinstance(systems, list):
            managed_cnt.add_metric([], len(systems))
        else:
            managed_cnt.add_metric([], 0)

        policies = policy_find()
        if isinstance(policies, list):
            policies_cnt.add_metric([], len(policies))
        elif isinstance(policies, dict):
            for key in ("policies", "policyList"):
                arr = policies.get(key)
                if isinstance(arr, list):
                    policies_cnt.add_metric([], len(arr))
                    break
            else:
                policies_cnt.add_metric([], 0)
        else:
            policies_cnt.add_metric([], 0)

        tags = system_list_tags()
        if isinstance(tags, list):
            tags_cnt.add_metric([], len(tags))
        elif isinstance(tags, dict):
            for key in ("tags", "tagList"):
                arr = tags.get(key)
                if isinstance(arr, list):
                    tags_cnt.add_metric([], len(arr))
                    break
            else:
                tags_cnt.add_metric([], 0)
        else:
            tags_cnt.add_metric([], 0)

        return [managed_cnt, policies_cnt, tags_cnt]

    def collect(self) -> Iterable:
        return super().collect()


