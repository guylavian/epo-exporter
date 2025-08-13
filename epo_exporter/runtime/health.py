from __future__ import annotations

import threading
import time
from typing import Optional

from ..api.client import call_onprem_api

_lock = threading.Lock()
_last_ok_ts: float = 0.0


def refresh_readiness() -> bool:
    """Try ePO heartbeat without crashing the server; returns whether ready."""
    global _last_ok_ts
    try:
        res = call_onprem_api("core.getVersion")  # Should have internal timeout if supported
        ok = isinstance(res, (dict, list)) or res is not None
    except Exception:
        ok = False
    if ok:
        with _lock:
            _last_ok_ts = time.time()
    return ok


def is_ready(ttl_seconds: float = 60.0) -> bool:
    now = time.time()
    with _lock:
        if _last_ok_ts and (now - _last_ok_ts) <= ttl_seconds:
            return True
    # No fresh state; probe once
    return refresh_readiness()


