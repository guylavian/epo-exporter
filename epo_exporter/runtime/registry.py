from typing import Iterable, Set

from prometheus_client.core import CollectorRegistry

from ..collectors.core.exporter_self import ExporterSelfCollector
from ..collectors.core.inventory import InventoryCollector
from ..collectors.compliance.policy_coverage import PolicyCoverageCollector
from ..collectors.compliance.policy_mismatch import PolicyMismatchCollector
from ..collectors.threat.events_total import ProductEventsCollector
from ..collectors.compliance.policy_gap import ProductGapCollector
from ..collectors.compliance.policy_not_applied import PolicyNotAppliedCollector
from ..collectors.compliance.dat_outdated import DatOutdatedCollector
from ..collectors.infra.agent_handler import AgentHandlerCollector
from ..collectors.threat.tie_metrics import TIECollector
from ..collectors.threat.atp_metrics import ATPCollector
from ..collectors.inventory_plus.version_distribution import VersionDistributionCollector
from ..collectors.compliance.tags_usage import TagsUsageCollector
from ..collectors.compliance.client_tasks import ClientTasksCollector
from ..collectors.infra.repository_status import RepositoryStatusCollector
from ..collectors.threat.events_severity import EventsSeverityCollector
from ..collectors.threat.quarantine import QuarantineCollector
from ..collectors.inventory_plus.dat_info import DatInfoCollector
from ..collectors.inventory_plus.policy_last_modified import PolicyLastModifiedCollector
from ..collectors.compliance.asci_config import ASCIConfigCollector


def build_registry_with_collectors(
    enabled_collectors: Set[str], scrape_timeout: float | None, cache_ttl: float
) -> CollectorRegistry:
    registry = CollectorRegistry()

    def maybe_add(name: str, collector):
        if name in enabled_collectors:
            registry.register(collector)

    maybe_add("exporter_self", ExporterSelfCollector(scrape_timeout=scrape_timeout))
    maybe_add("inventory", InventoryCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("product_events", ProductEventsCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("product_gap", ProductGapCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("policy_coverage", PolicyCoverageCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("policy_mismatch", PolicyMismatchCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("policy_not_applied", PolicyNotAppliedCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("dat_outdated", DatOutdatedCollector(cache_ttl_seconds=cache_ttl, scrape_timeout=scrape_timeout))
    maybe_add("agent_handler", AgentHandlerCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("tie", TIECollector(cache_ttl_seconds=cache_ttl))
    maybe_add("atp", ATPCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("version_distribution", VersionDistributionCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("tags_usage", TagsUsageCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("client_tasks", ClientTasksCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("repository_status", RepositoryStatusCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("events_severity", EventsSeverityCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("quarantine", QuarantineCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("dat_info", DatInfoCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("policy_last_modified", PolicyLastModifiedCollector(cache_ttl_seconds=cache_ttl))
    maybe_add("asci_config", ASCIConfigCollector())

    return registry


