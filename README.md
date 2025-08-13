ePO Exporter (windows_exporter–style)

Production-grade Prometheus exporter for Trellix ePO (on‑prem). Modeled after windows_exporter: modular collectors toggled by flags and/or YAML, pull-on-scrape, low-cardinality metrics, docs and tests.

Quick start

1) Install deps:

```bash
pip install -r requirements.txt
```

2) Run (defaults to :9898 and /metrics):

```bash
python epo-exporter.py --collectors.enabled=exporter_self,inventory,product_events,product_gap,policy_coverage,policy_mismatch
```

3) Scrape:

```bash
curl http://localhost:9898/metrics
```

Flags (parity with windows_exporter)

- --web.listen-address (default :9898)
- --web.telemetry-path (default /metrics)
- --collectors.enabled=comma,separated (overrides defaults)
- --collector.disable-defaults (start from zero)
- --collector.<name> / --no-collector.<name>
- --config.file=path/to/config.yaml (merges with flags)
- --scrape.timeout=SECONDS (best-effort guard)
- --cache.ttl=SECONDS (reuse expensive results for a short TTL)
- --log.level (INFO by default)

Collectors

- exporter_self: epo_up, epo_scrape_duration_seconds, epo_api_response_time_seconds{command}, epo_exporter_build_info{host,version}
- inventory: epo_managed_systems_count, epo_policies_count, epo_tags_count_total
- product_events: epo_events_total{product}
- product_gap: epo_product_installed_endpoints{product}, epo_product_reporting_endpoints{product}, epo_product_gap{product}
- policy_coverage: epo_policy_assigned_systems{product,policy}
- policy_mismatch: epo_policy_mismatch_total{product,policy}, epo_agents_overdue_total

Configuration

Environment variables (for ePO): EPO_HOST, EPO_USERNAME, EPO_PASSWORD, EPO_IGNORE_SSL, EPO_TIMEOUT.

Saved Query IDs via env or config.yaml:

- EPO_Q_EVENTS_BY_PRODUCT
- EPO_Q_INSTALLED_BY_PRODUCT
- EPO_Q_REPORTING_ENDPOINTS_BY_PRODUCT
- EPO_Q_POLICY_ASSIGNMENTS
- EPO_Q_MANAGED_SYSTEMS_COMM

See docs/ for how to create these Saved Queries in ePO UI.

Examples

```bash
python epo-exporter.py --config.file examples/config.yaml --collector.disable-defaults --collector.inventory --collector.exporter_self
```

Docs

Reference and per-collector docs in docs/.


