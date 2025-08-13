import time
from typing import Iterable, Optional

from prometheus_client.core import GaugeMetricFamily, HistogramMetricFamily

from ... import __version__
from ...config import EPO_HOST
from ...runtime.telemetry import API_HISTOGRAM_BUCKETS, api_latency_agg


class ExporterSelfCollector:
    """Exports exporter health and API latency histogram (populated by others)."""

    def __init__(self, scrape_timeout: Optional[float] = None) -> None:
        self.scrape_timeout = scrape_timeout

    def describe(self) -> Iterable:
        return []

    def collect(self) -> Iterable:
        start = time.time()

        up = GaugeMetricFamily("epo_up", "Whether the ePO server is responding (1) or not (0)")
        # The actual check is performed in inventory collector for now. Assume 1; downstream collectors may fail.
        up.add_metric([], 1)
        yield up

        info = GaugeMetricFamily(
            "epo_exporter_build_info",
            "Build/info labels",
            labels=["host", "version"],
        )
        info.add_metric([EPO_HOST, __version__], 1)
        yield info

        # API response time histogram accumulated across last calls per command
        api_hist = HistogramMetricFamily(
            "epo_api_response_time_seconds", "Response time of ePO API calls", labels=["command"], buckets=API_HISTOGRAM_BUCKETS
        )
        snap = api_latency_agg.snapshot()
        for cmd, st in snap.items():
            buckets = st["buckets"]  # type: ignore[index]
            # emit each bucket cumulative
            for i, le in enumerate((*API_HISTOGRAM_BUCKETS, "+Inf")):
                api_hist.add_sample(
                    "epo_api_response_time_seconds_bucket",
                    {"command": cmd, "le": str(le)},
                    int(buckets[i]),  # type: ignore[index]
                )
            api_hist.add_sample("epo_api_response_time_seconds_sum", {"command": cmd}, float(st["sum"]))  # type: ignore[index]
            api_hist.add_sample("epo_api_response_time_seconds_count", {"command": cmd}, int(st["count"]))  # type: ignore[index]
        yield api_hist

        duration = HistogramMetricFamily(
            "epo_scrape_duration_seconds", "Exporter scrape duration (seconds)", buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
        )
        dur = time.time() - start
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


