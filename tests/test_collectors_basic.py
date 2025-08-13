from prometheus_client.core import CollectorRegistry

from epo_exporter.collectors.core.inventory import InventoryCollector
from epo_exporter.collectors.threat.events_total import ProductEventsCollector
from epo_exporter.collectors.compliance.policy_gap import ProductGapCollector
from epo_exporter.collectors.compliance.policy_coverage import PolicyCoverageCollector
from epo_exporter.collectors.compliance.policy_mismatch import PolicyMismatchCollector


def collect_all(collector):
    reg = CollectorRegistry()
    reg.register(collector)
    # iterate generator once to ensure no exceptions
    list(collector.collect())


def test_inventory_collects_without_crash(monkeypatch):
    from epo_exporter.api import client as api

    monkeypatch.setattr(api, "call_onprem_api", lambda *a, **k: [])
    collect_all(InventoryCollector())


def test_product_events_collects_without_crash(monkeypatch):
    from epo_exporter.api import client as api

    monkeypatch.setattr(api, "call_onprem_api", lambda *a, **k: [])
    collect_all(ProductEventsCollector())


def test_product_gap_collects_without_crash(monkeypatch):
    from epo_exporter.api import client as api

    monkeypatch.setattr(api, "call_onprem_api", lambda *a, **k: [])
    collect_all(ProductGapCollector())


def test_policy_coverage_collects_without_crash(monkeypatch):
    from epo_exporter.api import client as api

    monkeypatch.setattr(api, "call_onprem_api", lambda *a, **k: [])
    collect_all(PolicyCoverageCollector())


def test_policy_mismatch_collects_without_crash(monkeypatch):
    from epo_exporter.api import client as api

    monkeypatch.setattr(api, "call_onprem_api", lambda *a, **k: [])
    collect_all(PolicyMismatchCollector())


