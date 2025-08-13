#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refactor project layout to:
epo-exporter/
├─ cmd/epo_exporter/
├─ epo_exporter/
│  ├─ api/{client.py,endpoints.py,schemas.py}
│  ├─ collectors/{core,compliance,threat,infra,inventory_plus}/...
│  ├─ config/{env.py,file.py,model.py}
│  ├─ runtime/{registry.py,server.py,telemetry.py,base.py,utils.py}
│  └─ __init__.py
├─ docs/{collectors/,operations.md}
├─ examples/config.yaml
├─ tests/{unit/{api,collectors/core,collectors/compliance,collectors/threat,runtime},integration/}
└─ pyproject.toml
"""
import os, re, shutil, sys, json
from pathlib import Path

ROOT = Path.cwd()
PKG  = ROOT / "epo_exporter"
CMD  = ROOT / "cmd" / "epo_exporter"

def ensure(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def write_if_missing(p: Path, content: str):
    if not p.exists():
        p.write_text(content, encoding="utf-8")

def move_with_shim(src_rel: str, dst_rel: str):
    src = PKG / src_rel
    if not src.exists(): return
    dst = PKG / dst_rel
    ensure(dst.parent)
    shutil.move(str(src), str(dst))
    # shim לשמירת תאימות
    shim = PKG / src_rel
    shim.write_text(f"from .{dst_rel.replace('/', '.')} import *\n", encoding="utf-8")

def rewrite_imports(path: Path, depth_add: int = 1):
    """
    collectors הועמקו בעוד חבילה (למשל מ- epo_exporter/collectors/*.py ל- epo_exporter/collectors/<domain>/*.py)
    לכן צריך להחליף '..' ב-'...' בכמה imports נפוצים.
    """
    txt = path.read_text(encoding="utf-8", errors="ignore")
    original = txt
    if depth_add > 0:
        txt = re.sub(r"from\s+\.\.\s*api\.client\s+import", "from " + "."*(2+depth_add) + "api.client import", txt)
        txt = re.sub(r"from\s+\.\.\s*config\s+import",      "from " + "."*(2+depth_add) + "config import", txt)
        txt = re.sub(r"from\s+\.\.\s*metrics\s+import",     "from " + "."*(2+depth_add) + "metrics import", txt)
        txt = re.sub(r"from\s+\.\.\s*telemetry\s+import",   "from " + "."*(2+depth_add) + "runtime.telemetry import", txt)
        txt = txt.replace("from ..telemetry import",        "from " + "."*(2+depth_add) + "runtime.telemetry import")
        txt = txt.replace("from ..server import",           "from " + "."*(2+depth_add) + "runtime.server import")
    if txt != original:
        path.write_text(txt, encoding="utf-8")

def main():
    if not PKG.exists() or not CMD.exists():
        print("Run from the repo root (must contain 'epo_exporter/' and 'cmd/epo_exporter/').", file=sys.stderr)
        sys.exit(1)

    # יצירת עץ חדש
    ensure(PKG / "api")
    ensure(PKG / "collectors")
    ensure(PKG / "collectors" / "core")
    ensure(PKG / "collectors" / "compliance")
    ensure(PKG / "collectors" / "threat")
    ensure(PKG / "collectors" / "infra")
    ensure(PKG / "collectors" / "inventory_plus")
    ensure(PKG / "runtime")
    ensure(PKG / "config")
    ensure(ROOT / "docs" / "collectors")
    write_if_missing(ROOT / "docs" / "operations.md", "# Operations\n\nFlags, sizing, alerts.\n")

    # api: endpoints+schemas (אם חסרים)
    write_if_missing(PKG / "api" / "endpoints.py",
"""from .client import call_onprem_api

def q(query_id: str, params: dict | None = None):
    p = {"queryId": query_id}
    if params: p.update(params)
    return call_onprem_api("core.executeQuery", p)

def list_agent_handlers():
    return call_onprem_api("agentmgmt.listAgentHandlers")
""")
    write_if_missing(PKG / "api" / "schemas.py", "# optional: pydantic/dataclasses for API responses\n")

    # runtime: base+utils (אם חסרים)
    write_if_missing(PKG / "runtime" / "base.py",
"""from typing import Iterable, List, Optional
import time, logging

class CachingCollectorBase:
    def __init__(self, cache_ttl_seconds: float = 0.0, scrape_timeout: Optional[float] = None) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self.scrape_timeout = scrape_timeout
        self._cache_until = 0.0
        self._cached: Optional[List] = None
        self._log = logging.getLogger(self.__class__.__name__)

    def describe(self) -> Iterable:
        return []

    def _timed_out(self, start: float) -> bool:
        return self.scrape_timeout is not None and (time.time() - start) >= self.scrape_timeout

    def _collect_now(self) -> List:
        raise NotImplementedError

    def collect(self) -> Iterable:
        start = time.time()
        now = start
        if self.cache_ttl_seconds and now < self._cache_until and self._cached is not None:
            for m in self._cached: yield m
            return
        if self._timed_out(start):
            if self._cached is not None:
                for m in self._cached: yield m
            return
        try:
            metrics = self._collect_now()
        except Exception as e:
            self._log.warning("collector error: %s", e)
            metrics = self._cached or []
        self._cached = metrics
        self._cache_until = now + self.cache_ttl_seconds
        for m in metrics: yield m
""")
    write_if_missing(PKG / "runtime" / "utils.py",
"""from typing import Callable, List, Tuple
from ..metrics import get_int, get_str, parse_epoch_or_iso

def sanitize_label(s: str) -> str:
    s = (s or "").strip()
    return s if s else "unknown"

def topn_with_other(rows: List[dict], key: Callable[[dict], int], n: int) -> Tuple[List[dict], int]:
    rows = [r for r in rows if r is not None]
    rows.sort(key=key, reverse=True)
    head, tail = rows[:n], rows[n:]
    other = sum(key(r) for r in tail)
    return head, other
""")

    # telemetry/server/registry -> runtime, עם shim
    move_with_shim("telemetry.py", "runtime/telemetry.py")
    move_with_shim("server.py",    "runtime/server.py")
    move_with_shim("registry.py",  "runtime/registry.py")

    # config שלדים (אם חסר)
    write_if_missing(PKG / "config" / "env.py",
"""import os
# expose env in one place
EPO_HOST = os.environ.get("EPO_HOST", "https://localhost:8443")
# ... add your env bindings ...
""")
    write_if_missing(PKG / "config" / "file.py",
"""# YAML loader/merge (optional). Put your file config logic here.
""")
    write_if_missing(PKG / "config" / "model.py",
"""# dataclass/pydantic model for merged config (optional).
""")

    # מיפוי קבצי קולקטור -> דומיין ותיקיית יעד (כולל שינוי שם חלקי)
    mapping = {
        # core
        "exporter_self.py": ("collectors/core/exporter_self.py", None),
        "inventory.py":     ("collectors/core/inventory.py", None),

        # compliance
        "product_gap.py":         ("collectors/compliance/policy_gap.py", "rename"),  # שינוי שם
        "policy_mismatch.py":     ("collectors/compliance/policy_mismatch.py", None),
        "policy_coverage.py":     ("collectors/compliance/policy_coverage.py", None),
        "policy_not_applied.py":  ("collectors/compliance/policy_not_applied.py", None),
        "dat_outdated.py":        ("collectors/compliance/dat_outdated.py", None),
        "tags_usage.py":          ("collectors/compliance/tags_usage.py", None),
        "client_tasks.py":        ("collectors/compliance/client_tasks.py", None),

        # threat
        "product_events.py":      ("collectors/threat/events_total.py", "rename"),    # שינוי שם
        "events_severity.py":     ("collectors/threat/events_severity.py", None),
        "atp_metrics.py":         ("collectors/threat/atp_metrics.py", None),
        "tie_metrics.py":         ("collectors/threat/tie_metrics.py", None),
        "quarantine.py":          ("collectors/threat/quarantine.py", None),

        # infra
        "agent_handler.py":       ("collectors/infra/agent_handler.py", None),
        "repository_status.py":   ("collectors/infra/repository_status.py", None),

        # inventory_plus
        "version_distribution.py":("collectors/inventory_plus/version_distribution.py", None),
        "dat_info.py":            ("collectors/inventory_plus/dat_info.py", None),
        "policy_last_modified.py":("collectors/inventory_plus/policy_last_modified.py", None),
    }

    # אסוף כל קבצי collectors/ (רק ישירים)
    old_col = list((PKG / "collectors").glob("*.py"))
    moved = []

    for p in old_col:
        if p.name == "__init__.py": continue
        if p.name not in mapping:
            # נשאיר קבצים לא מזוהים במיקום הישן (או הדפס אזהרה)
            print(f"[warn] unknown collector stays put: {p.name}")
            continue
        dst_rel, action = mapping[p.name]
        dst = PKG / dst_rel
        ensure(dst.parent)
        shutil.move(str(p), str(dst))
        moved.append((p, dst))
        # עדכון imports לקובץ שהועבר (העמקה בעוד חבילה → ... במקום ..)
        rewrite_imports(dst, depth_add=1)

    # הוספת __init__.py בכל תיקיות חדשות
    for d in [
        PKG / "collectors",
        PKG / "collectors" / "core",
        PKG / "collectors" / "compliance",
        PKG / "collectors" / "threat",
        PKG / "collectors" / "infra",
        PKG / "collectors" / "inventory_plus",
        PKG / "runtime",
        PKG / "api",
        PKG / "config",
    ]:
        (d / "__init__.py").write_text("", encoding="utf-8")

    # עדכון registry imports לנתיבים החדשים
    reg_path = PKG / "runtime" / "registry.py"
    if reg_path.exists():
        reg = reg_path.read_text(encoding="utf-8", errors="ignore")
        repl = {
            # core
            r"from \.collectors\.exporter_self import ExporterSelfCollector":
                "from ..collectors.core.exporter_self import ExporterSelfCollector",
            r"from \.collectors\.inventory import InventoryCollector":
                "from ..collectors.core.inventory import InventoryCollector",

            # compliance
            r"from \.collectors\.product_gap import ProductGapCollector":
                "from ..collectors.compliance.policy_gap import ProductGapCollector",
            r"from \.collectors\.policy_mismatch import PolicyMismatchCollector":
                "from ..collectors.compliance.policy_mismatch import PolicyMismatchCollector",
            r"from \.collectors\.policy_coverage import PolicyCoverageCollector":
                "from ..collectors.compliance.policy_coverage import PolicyCoverageCollector",
            r"from \.collectors\.policy_not_applied import PolicyNotAppliedCollector":
                "from ..collectors.compliance.policy_not_applied import PolicyNotAppliedCollector",
            r"from \.collectors\.dat_outdated import DatOutdatedCollector":
                "from ..collectors.compliance.dat_outdated import DatOutdatedCollector",
            r"from \.collectors\.tags_usage import TagsUsageCollector":
                "from ..collectors.compliance.tags_usage import TagsUsageCollector",
            r"from \.collectors\.client_tasks import ClientTasksCollector":
                "from ..collectors.compliance.client_tasks import ClientTasksCollector",

            # threat
            r"from \.collectors\.product_events import ProductEventsCollector":
                "from ..collectors.threat.events_total import ProductEventsCollector",
            r"from \.collectors\.events_severity import EventsSeverityCollector":
                "from ..collectors.threat.events_severity import EventsSeverityCollector",
            r"from \.collectors\.atp_metrics import ATPCollector":
                "from ..collectors.threat.atp_metrics import ATPCollector",
            r"from \.collectors\.tie_metrics import TIECollector":
                "from ..collectors.threat.tie_metrics import TIECollector",
            r"from \.collectors\.quarantine import QuarantineCollector":
                "from ..collectors.threat.quarantine import QuarantineCollector",

            # infra
            r"from \.collectors\.agent_handler import AgentHandlerCollector":
                "from ..collectors.infra.agent_handler import AgentHandlerCollector",
            r"from \.collectors\.repository_status import RepositoryStatusCollector":
                "from ..collectors.infra.repository_status import RepositoryStatusCollector",

            # inventory_plus
            r"from \.collectors\.version_distribution import VersionDistributionCollector":
                "from ..collectors.inventory_plus.version_distribution import VersionDistributionCollector",
            r"from \.collectors\.dat_info import DatInfoCollector":
                "from ..collectors.inventory_plus.dat_info import DatInfoCollector",
            r"from \.collectors\.policy_last_modified import PolicyLastModifiedCollector":
                "from ..collectors.inventory_plus.policy_last_modified import PolicyLastModifiedCollector",
        }
        for pat, rep in repl.items():
            reg = re.sub(pat, rep, reg)
        reg_path.write_text(reg, encoding="utf-8")

    # תיקון imports בקבצי collectors שנשארו בשורש (אם יש) – לא מעמיקים
    for p in (PKG / "collectors").glob("*.py"):
        if p.name == "__init__.py": continue
        rewrite_imports(p, depth_add=0)

    # הדפס סיכום
    summary = {
        "moved": [(str(a.relative_to(ROOT)), str(b.relative_to(ROOT))) for a,b in moved],
        "created_dirs": [
            str((PKG/"collectors/core").relative_to(ROOT)),
            str((PKG/"collectors/compliance").relative_to(ROOT)),
            str((PKG/"collectors/threat").relative_to(ROOT)),
            str((PKG/"collectors/infra").relative_to(ROOT)),
            str((PKG/"collectors/inventory_plus").relative_to(ROOT)),
            str((PKG/"runtime").relative_to(ROOT)),
            str((PKG/"config").relative_to(ROOT)),
            "docs/collectors",
        ],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()


