import time
from typing import Dict, Iterable, Optional

from prometheus_client.core import (
    REGISTRY,
    GaugeMetricFamily,
    HistogramMetricFamily,
)

from .config import (
    ASCI_MINUTES,
    ASCI_OVERDUE_MULTIPLIER,
    EPO_HOST,
    Q_EVENTS_BY_PRODUCT,
    Q_INSTALLED_BY_PRODUCT,
    Q_MANAGED_COMM,
    Q_POLICY_ASSIGNMENTS,
    Q_REPORTING_ENDPOINTS_BY_PRODUCT,
)
from .executor import call_onprem_api
from .metrics import get_int, get_str, parse_epoch_or_iso


class EPOCollector:
    def __init__(self) -> None:
        self._last_scrape_seconds = 0.0

    def describe(self) -> Iterable:
        return []

    def collect(self) -> Iterable:
        start = time.time()

        # base health
        up = GaugeMetricFamily("epo_up", "Whether the ePO server is responding (1) or not (0)")
        version = call_onprem_api("core.getVersion")
        if version is None:
            up.add_metric([], 0)
            yield up
            yield from self._yield_scrape_duration(start)
            return
        up.add_metric([], 1)
        yield up

        # info metric (labels only)
        info = GaugeMetricFamily(
            "epo_exporter_build_info",
            "Build/info labels",
            labels=["host"],
        )
        info.add_metric([EPO_HOST], 1)
        yield info

        # API response time histogram per command (synthetic)
        rt_hist = HistogramMetricFamily(
            "epo_api_response_time_seconds",
            "Response time of ePO API calls",
            labels=["command"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
        )

        def timed(command: str, **kwargs):
            t0 = time.time()
            res = call_onprem_api(command, kwargs)
            dt = time.time() - t0
            # accumulate histogram observation via manual samples
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "0.1"}, 1 if dt <= 0.1 else 0)
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "0.5"}, 1 if dt <= 0.5 else 0)
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "1.0"}, 1 if dt <= 1.0 else 0)
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "2.0"}, 1 if dt <= 2.0 else 0)
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "5.0"}, 1 if dt <= 5.0 else 0)
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "10.0"}, 1 if dt <= 10.0 else 0)
            rt_hist.add_sample("epo_api_response_time_seconds_bucket", {"command": command, "le": "+Inf"}, 1)
            rt_hist.add_sample("epo_api_response_time_seconds_sum", {"command": command}, dt)
            rt_hist.add_sample("epo_api_response_time_seconds_count", {"command": command}, 1)
            return res

        # managed systems / policies / tags (snapshots)
        managed_cnt = GaugeMetricFamily("epo_managed_systems_count", "Number of managed systems")
        systems = timed("system.find", searchText="")
        if isinstance(systems, list):
            managed_cnt.add_metric([], len(systems))
        else:
            managed_cnt.add_metric([], 0)
        yield managed_cnt

        policies_cnt = GaugeMetricFamily("epo_policies_count", "Number of policies configured in ePO")
        policies = timed("policy.find")
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
        yield policies_cnt

        tags_cnt = GaugeMetricFamily("epo_tags_count_total", "Number of tags defined in ePO")
        tags = timed("system.listTags")
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
        yield tags_cnt

        # events per product + rate source (window)
        if Q_EVENTS_BY_PRODUCT:
            events_g = GaugeMetricFamily(
                "epo_events_total", "Number of threat events in the saved query window (by product)", labels=["product"]
            )
            rows = timed("core.executeQuery", queryId=Q_EVENTS_BY_PRODUCT)
            if isinstance(rows, list):
                for r in rows:
                    product = get_str(r.get("AnalyzerName") or r.get("analyzerName") or (r.get("attributes") or {}).get("AnalyzerName"))
                    count = r.get("COUNT") or r.get("count") or r.get("Total")
                    ival = get_int(count)
                    if product and ival is not None:
                        events_g.add_metric([product], ival)
            yield events_g

        # product gap: installed vs reporting
        if Q_INSTALLED_BY_PRODUCT:
            installed_g = GaugeMetricFamily(
                "epo_product_installed_endpoints", "Installed endpoints per product", labels=["product"]
            )
            rows = timed("core.executeQuery", queryId=Q_INSTALLED_BY_PRODUCT)
            installed_map: Dict[str, int] = {}
            if isinstance(rows, list):
                for r in rows:
                    product = get_str(r.get("Product") or r.get("ProductName") or (r.get("attributes") or {}).get("Product"))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if product and count is not None:
                        installed_map[product] = count
                        installed_g.add_metric([product], count)
            yield installed_g

            reporting_map: Dict[str, int] = {}
            reporting_g = GaugeMetricFamily(
                "epo_product_reporting_endpoints", "Reporting endpoints per product (in window)", labels=["product"]
            )
            if Q_REPORTING_ENDPOINTS_BY_PRODUCT:
                rows2 = timed("core.executeQuery", queryId=Q_REPORTING_ENDPOINTS_BY_PRODUCT)
                if isinstance(rows2, list):
                    for r in rows2:
                        product = get_str(r.get("AnalyzerName") or r.get("analyzerName") or (r.get("attributes") or {}).get("AnalyzerName"))
                        count = get_int(r.get("DistinctSystems") or r.get("distinct") or r.get("COUNT") or r.get("count"))
                        if product and count is not None:
                            reporting_map[product] = count
                            reporting_g.add_metric([product], count)
                yield reporting_g

            gap_g = GaugeMetricFamily("epo_product_gap", "Installed - Reporting endpoints per product", labels=["product"])
            for p, inst in installed_map.items():
                rep = reporting_map.get(p, 0)
                gap_g.add_metric([p], max(inst - rep, 0))
            yield gap_g

        # policy coverage & mismatch
        if Q_POLICY_ASSIGNMENTS:
            pol_assigned = GaugeMetricFamily(
                "epo_policy_assigned_systems",
                "Number of endpoints assigned to the policy",
                labels=["product", "policy"],
            )
            rows = timed("core.executeQuery", queryId=Q_POLICY_ASSIGNMENTS)
            if isinstance(rows, list):
                for r in rows:
                    product = get_str(r.get("Product") or (r.get("attributes") or {}).get("Product"))
                    policy = get_str(r.get("Policy") or r.get("PolicyName") or (r.get("attributes") or {}).get("Policy"))
                    count = get_int(r.get("COUNT") or r.get("count") or (r.get("attributes") or {}).get("COUNT"))
                    if product and policy and count is not None:
                        pol_assigned.add_metric([product, policy], count)
            yield pol_assigned

        if Q_MANAGED_COMM:
            overdue_threshold_secs = int(ASCI_MINUTES * 60 * ASCI_OVERDUE_MULTIPLIER)
            now = time.time()
            pol_mismatch = GaugeMetricFamily(
                "epo_policy_mismatch_total", "Endpoints with stale/uneffective policy", labels=["product", "policy"]
            )
            agents_overdue = GaugeMetricFamily("epo_agents_overdue_total", "Agents overdue (no communication)", labels=[])
            overdue_count = 0
            rows = timed("core.executeQuery", queryId=Q_MANAGED_COMM)
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
            yield pol_mismatch
            yield agents_overdue

        # expose the synthetic histogram
        yield rt_hist

        # scrape duration
        yield from self._yield_scrape_duration(start)

    def _yield_scrape_duration(self, start: float):
        dur = time.time() - start
        duration = HistogramMetricFamily(
            "epo_scrape_duration_seconds", "Exporter scrape duration (seconds)", buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
        )
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "0.1"}, 1 if dur <= 0.1 else 0)
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "0.5"}, 1 if dur <= 0.5 else 0)
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "1.0"}, 1 if dur <= 1.0 else 0)
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "2.0"}, 1 if dur <= 2.0 else 0)
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "5.0"}, 1 if dur <= 5.0 else 0)
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "10.0"}, 1 if dur <= 10.0 else 0)
        duration.add_sample("epo_scrape_duration_seconds_bucket", {"le": "+Inf"}, 1)
        duration.add_sample("epo_scrape_duration_seconds_sum", {}, dur)
        duration.add_sample("epo_scrape_duration_seconds_count", {}, 1)
        yield duration


