import argparse
import logging
import os
import sys
from typing import List, Optional, Set

from prometheus_client.core import CollectorRegistry

from epo_exporter import __version__
from epo_exporter.config import LOG_LEVEL
from epo_exporter.runtime_config import RuntimeConfig
from epo_exporter.registry import build_registry_with_collectors
from epo_exporter.server import serve_http


def parse_flags(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trellix ePO Prometheus exporter")

    # Web flags (parity with windows_exporter)
    parser.add_argument("--web.listen-address", dest="listen_address", default=":9898")
    parser.add_argument("--web.telemetry-path", dest="telemetry_path", default="/metrics")

    # Config file
    parser.add_argument("--config.file", dest="config_file", default=None)

    # Collectors toggles
    parser.add_argument("--collectors.enabled", dest="collectors_enabled_csv", default=None,
                        help="Comma-separated list of enabled collectors. Overrides defaults.")
    parser.add_argument("--collector.disable-defaults", dest="disable_defaults", action="store_true",
                        help="Disable default collectors; enable only those provided explicitly.")

    # node_exporter pattern support
    parser.add_argument("--collector.product_events", dest="collector_product_events", action="store_true")
    parser.add_argument("--collector.product_gap", dest="collector_product_gap", action="store_true")
    parser.add_argument("--collector.policy_coverage", dest="collector_policy_coverage", action="store_true")
    parser.add_argument("--collector.policy_mismatch", dest="collector_policy_mismatch", action="store_true")
    parser.add_argument("--collector.inventory", dest="collector_inventory", action="store_true")
    parser.add_argument("--collector.exporter_self", dest="collector_exporter_self", action="store_true")
    parser.add_argument("--collector.policy_not_applied", dest="collector_policy_not_applied", action="store_true")
    parser.add_argument("--collector.dat_outdated", dest="collector_dat_outdated", action="store_true")

    # negative toggles
    parser.add_argument("--no-collector.product_events", dest="no_collector_product_events", action="store_true")
    parser.add_argument("--no-collector.product_gap", dest="no_collector_product_gap", action="store_true")
    parser.add_argument("--no-collector.policy_coverage", dest="no_collector_policy_coverage", action="store_true")
    parser.add_argument("--no-collector.policy_mismatch", dest="no_collector_policy_mismatch", action="store_true")
    parser.add_argument("--no-collector.inventory", dest="no_collector_inventory", action="store_true")
    parser.add_argument("--no-collector.exporter_self", dest="no_collector_exporter_self", action="store_true")
    parser.add_argument("--no-collector.policy_not_applied", dest="no_collector_policy_not_applied", action="store_true")
    parser.add_argument("--no-collector.dat_outdated", dest="no_collector_dat_outdated", action="store_true")

    # Global behavior
    parser.add_argument("--scrape.timeout", dest="scrape_timeout", type=float, default=None)
    parser.add_argument("--cache.ttl", dest="cache_ttl", type=float, default=0.0)

    # Logging
    parser.add_argument("--log.level", dest="log_level", default=os.environ.get("EPO_LOG_LEVEL", LOG_LEVEL))

    return parser.parse_args(argv)


DEFAULT_COLLECTORS: Set[str] = {
    "exporter_self",
    "inventory",
    "product_gap",
    "policy_mismatch",
    "policy_not_applied",
    "dat_outdated",
}


def resolve_enabled_collectors(args: argparse.Namespace, rc: RuntimeConfig) -> Set[str]:
    if args.collectors_enabled_csv:
        return {c.strip() for c in args.collectors_enabled_csv.split(",") if c.strip()}

    enabled: Set[str] = set()
    if not args.disable_defaults:
        enabled |= set(DEFAULT_COLLECTORS)

    # positive flags
    if args.collector_product_events:
        enabled.add("product_events")
    if args.collector_product_gap:
        enabled.add("product_gap")
    if args.collector_policy_coverage:
        enabled.add("policy_coverage")
    if args.collector_policy_mismatch:
        enabled.add("policy_mismatch")
    if args.collector_inventory:
        enabled.add("inventory")
    if args.collector_exporter_self:
        enabled.add("exporter_self")
    if args.collector_policy_not_applied:
        enabled.add("policy_not_applied")
    if args.collector_dat_outdated:
        enabled.add("dat_outdated")

    # negative flags
    if args.no_collector_product_events:
        enabled.discard("product_events")
    if args.no_collector_product_gap:
        enabled.discard("product_gap")
    if args.no_collector_policy_coverage:
        enabled.discard("policy_coverage")
    if args.no_collector_policy_mismatch:
        enabled.discard("policy_mismatch")
    if args.no_collector_inventory:
        enabled.discard("inventory")
    if args.no_collector_exporter_self:
        enabled.discard("exporter_self")
    if args.no_collector_policy_not_applied:
        enabled.discard("policy_not_applied")
    if args.no_collector_dat_outdated:
        enabled.discard("dat_outdated")

    # config file can also specify enabled collectors; merge rules handled earlier
    if rc.enabled_collectors is not None:
        enabled = set(rc.enabled_collectors)

    return enabled


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_flags(argv)

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger("epo_exporter")

    # load YAML config if provided
    rc = RuntimeConfig.load_from_file(args.config_file) if args.config_file else RuntimeConfig()
    if rc.log_level and not args.log_level:
        logging.getLogger().setLevel(rc.log_level)

    enabled_collectors = resolve_enabled_collectors(args, rc)
    log.info("enabled collectors: %s", ",".join(sorted(enabled_collectors)) or "<none>")

    # registry with selected collectors
    registry: CollectorRegistry = build_registry_with_collectors(
        enabled_collectors=enabled_collectors,
        scrape_timeout=args.scrape_timeout or rc.scrape_timeout,
        cache_ttl=args.cache_ttl if args.cache_ttl is not None else (rc.cache_ttl or 0.0),
    )

    # listen address parsing (:9898 or addr:port)
    listen = args.listen_address
    if listen.startswith(":"):
        host, port = "0.0.0.0", int(listen[1:])
    elif ":" in listen:
        host, port_str = listen.rsplit(":", 1)
        port = int(port_str)
    else:
        host, port = listen, 9898

    # Start server and expose path
    log.info("ePO exporter %s listening on %s:%d path=%s", __version__, host, port, args.telemetry_path)
    serve_http(host, port, args.telemetry_path, registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


