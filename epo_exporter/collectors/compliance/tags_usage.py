from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_TAG_USAGE
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase
from ...runtime.utils import topn_with_other, sanitize_label
import os
import time


TOPN = int(os.getenv("EPO_TOPN", "50"))


class TagsUsageCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        super().__init__(cache_ttl_seconds)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        metric = GaugeMetricFamily("epo_tag_usage_count", "Number of systems per tag", labels=["tag"])
        if not Q_TAG_USAGE:
            return [metric]
        rows = q(Q_TAG_USAGE) or []
        if isinstance(rows, list):
            head, other = topn_with_other(rows, key=lambda r: get_int(r.get("COUNT") or 0) or 0, n=TOPN)
            for r in head:
                tag = sanitize_label(get_str(r.get("Tag") or r.get("TagName") or (r.get("attributes") or {}).get("Tag")))
                count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                if tag and count is not None:
                    metric.add_metric([tag], count)
            if other:
                metric.add_metric(["other"], other)
        return [metric]

    def collect(self) -> Iterable:
        return super().collect()


