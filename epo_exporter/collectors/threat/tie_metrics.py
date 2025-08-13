from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_TIE_REP, Q_TIE_REP_BY_SOURCE, Q_TIE_UNKNOWN_PREVALENT
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase
from ...runtime.utils import topn_with_other, sanitize_label
import os


TOPN = int(os.getenv("EPO_TOPN", "50"))


class TIECollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        super().__init__(cache_ttl_seconds)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        rep = GaugeMetricFamily("epo_tie_reputation_total", "TIE reputation counts", labels=["reputation"])
        rep_source = GaugeMetricFamily("epo_tie_reputation_by_source_total", "TIE reputation by source", labels=["source", "reputation"])
        unknown_prev = GaugeMetricFamily("epo_tie_unknown_prevalent_total", "TIE unknown but prevalent items", labels=[])

        if Q_TIE_REP:
            rows = q(Q_TIE_REP)
            if isinstance(rows, list):
                for r in rows:
                    reputation = sanitize_label(get_str(r.get("Reputation") or (r.get("attributes") or {}).get("Reputation")))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if reputation and count is not None:
                        rep.add_metric([reputation], count)

        if Q_TIE_REP_BY_SOURCE:
            rows = q(Q_TIE_REP_BY_SOURCE) or []
            if isinstance(rows, list):
                head, other = topn_with_other(rows, key=lambda r: get_int(r.get("COUNT") or 0) or 0, n=TOPN)
                for r in head:
                    reputation = sanitize_label(get_str(r.get("Reputation") or (r.get("attributes") or {}).get("Reputation")))
                    source = sanitize_label(get_str(r.get("Source") or (r.get("attributes") or {}).get("Source")))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if source and reputation and count is not None:
                        rep_source.add_metric([source, reputation], count)
                if other:
                    rep_source.add_metric(["other", "other"], other)

        if Q_TIE_UNKNOWN_PREVALENT:
            rows = q(Q_TIE_UNKNOWN_PREVALENT)
            if isinstance(rows, list):
                total = 0
                for r in rows:
                    c = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if c is not None:
                        total += c
                unknown_prev.add_metric([], total)

        return [rep, rep_source, unknown_prev]

    def collect(self) -> Iterable:
        return super().collect()


