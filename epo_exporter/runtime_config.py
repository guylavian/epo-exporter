from __future__ import annotations

import dataclasses
import os
from typing import List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclasses.dataclass
class RuntimeConfig:
    enabled_collectors: Optional[List[str]] = None
    scrape_timeout: Optional[float] = None
    cache_ttl: Optional[float] = None
    log_level: Optional[str] = None

    @staticmethod
    def load_from_file(path: Optional[str]) -> "RuntimeConfig":
        if not path:
            return RuntimeConfig()
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if yaml is None:
            raise RuntimeError("PyYAML is required to load config file. Install pyyaml.")
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        rc = RuntimeConfig()
        ec = data.get("enabled_collectors")
        if isinstance(ec, list):
            rc.enabled_collectors = [str(x) for x in ec]
        rc.scrape_timeout = _get_float(data.get("scrape_timeout"))
        rc.cache_ttl = _get_float(data.get("cache_ttl"))
        if isinstance(data.get("log_level"), str):
            rc.log_level = data.get("log_level")
        return rc


def _get_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


