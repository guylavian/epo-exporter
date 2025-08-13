from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...config import Q_ATP_RULES, Q_ATP_DAC
from ...api.endpoints import q
from ...metrics import get_int, get_str
from ...runtime.base import CachingCollectorBase
from ...runtime.utils import topn_with_other, sanitize_label
import os
import time


TOPN = int(os.getenv("EPO_TOPN", "50"))


class ATPCollector(CachingCollectorBase):
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        super().__init__(cache_ttl_seconds)

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        rules = GaugeMetricFamily("epo_atp_rules_triggered_total", "ATP rule triggers (window count)", labels=["rule", "action"])
        dac = GaugeMetricFamily("epo_atp_dac_actions_total", "ATP Dynamic Application Containment actions", labels=["action"])

        if Q_ATP_RULES:
            rows = q(Q_ATP_RULES) or []
            if isinstance(rows, list):
                head, other = topn_with_other(rows, key=lambda r: get_int(r.get("COUNT") or 0) or 0, n=TOPN)
                for r in head:
                    rule = sanitize_label(get_str(r.get("RuleName") or r.get("Rule") or (r.get("attributes") or {}).get("RuleName")))
                    action = sanitize_label(get_str(r.get("ActionTaken") or r.get("Action") or (r.get("attributes") or {}).get("ActionTaken")))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if rule and action and count is not None:
                        rules.add_metric([rule, action], count)
                if other:
                    rules.add_metric(["other", "other"], other)

        if Q_ATP_DAC:
            rows = q(Q_ATP_DAC)
            if isinstance(rows, list):
                for r in rows:
                    action = sanitize_label(get_str(r.get("Action") or (r.get("attributes") or {}).get("Action")))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if action and count is not None:
                        dac.add_metric([action], count)

        return [rules, dac]

    def collect(self) -> Iterable:
        return super().collect()


