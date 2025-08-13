exporter_self collector

Exports exporter health and internal timings.

Metrics

- epo_up — 1 if exporter is running.
- epo_exporter_build_info{host,version} — gauge set to 1 with labels.
- epo_scrape_duration_seconds — scrape duration histogram.
- epo_api_response_time_seconds{command} — ePO API call latency histogram aggregated during scrapes.

Flags

- Enabled by default.
- Toggle: --collector.exporter_self or --no-collector.exporter_self.

