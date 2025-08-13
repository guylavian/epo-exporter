from typing import Iterable
from prometheus_client.core import GaugeMetricFamily
from ...api.client import call_onprem_api
from ...metrics import get_int, get_str, parse_epoch_or_iso
import time

"""
Collector: Agent Handler
שולף ישירות מ-Web API:
  GET /remote/agentmgmt.listAgentHandlers?:output=json

מטריקות:
  - epo_handler_up{handler}                       1/0
  - epo_handler_agents_connected{handler}         מספר תחנות משויכות/מחוברות
  - epo_handler_event_backlog{handler}            גודל התור (אם זמין)
  - epo_handler_last_contact_timestamp{handler}   epoch seconds

הערה: אין תלות ב-Saved Query. הפריסה גמישה לשמות שדות שונים בין גרסאות.
"""


class AgentHandlerCollector:
    def __init__(self, cache_ttl_seconds: float = 0.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache_until = 0.0
        self._cached = None

    def describe(self) -> Iterable:
        return []

    def _collect_now(self):
        up = GaugeMetricFamily("epo_handler_up", "Agent Handler up (1) / down (0)", labels=["handler"])
        agents = GaugeMetricFamily("epo_handler_agents_connected", "Agents connected per handler", labels=["handler"])
        backlog = GaugeMetricFamily("epo_handler_event_backlog", "Event backlog per handler", labels=["handler"])
        last_contact = GaugeMetricFamily(
            "epo_handler_last_contact_timestamp",
            "Last contact timestamp per handler (epoch seconds)",
            labels=["handler"],
        )

        rows = call_onprem_api("agentmgmt.listAgentHandlers")
        if isinstance(rows, list):
            for r in rows:
                name = get_str(
                    r.get("HandlerName")
                    or r.get("Name")
                    or (r.get("attributes") or {}).get("HandlerName")
                    or (r.get("attributes") or {}).get("Name")
                )
                status = get_str(
                    r.get("Status")
                    or (r.get("attributes") or {}).get("Status")
                )
                connected = get_int(
                    r.get("ConnectedAgents")
                    or r.get("SystemsConnected")
                    or (r.get("attributes") or {}).get("ConnectedAgents")
                    or (r.get("attributes") or {}).get("SystemsConnected")
                )
                bl = get_int(
                    r.get("Backlog")
                    or r.get("EventBacklog")
                    or (r.get("attributes") or {}).get("Backlog")
                    or (r.get("attributes") or {}).get("EventBacklog")
                )
                lc_raw = (
                    r.get("LastContact")
                    or r.get("LastUpdate")
                    or (r.get("attributes") or {}).get("LastContact")
                    or (r.get("attributes") or {}).get("LastUpdate")
                )
                lc = parse_epoch_or_iso(lc_raw) or 0

                if name:
                    is_up = 1 if (status or "").lower() in ("up", "running", "ok", "online", "healthy") else 0
                    up.add_metric([name], is_up)
                    if connected is not None:
                        agents.add_metric([name], connected)
                    if bl is not None:
                        backlog.add_metric([name], bl)
                    if lc:
                        last_contact.add_metric([name], lc)

        return [up, agents, backlog, last_contact]

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


