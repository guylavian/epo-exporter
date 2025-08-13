import json
import logging
from typing import Any, Dict, Optional

import requests

from ..config import EPO_HOST, EPO_PASSWORD, EPO_USERNAME, IGNORE_SSL, TIMEOUT
from ..telemetry import api_latency_agg

log = logging.getLogger("epo_exporter")

_session = requests.Session()
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    _session.mount("https://", HTTPAdapter(max_retries=retries))
    _session.mount("http://", HTTPAdapter(max_retries=retries))
except Exception:
    pass


def call_onprem_api(command: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    params = dict(params or {})
    params[":output"] = "json"
    url = f"{EPO_HOST}/remote/{command}"
    try:
        import time as _time
        t0 = _time.time()
        resp = _session.get(
            url,
            params=params,
            auth=(EPO_USERNAME, EPO_PASSWORD),
            verify=not IGNORE_SSL,
            timeout=TIMEOUT,
        )
        api_latency_agg.observe(command, _time.time() - t0)
        if not resp.ok:
            log.warning("API call to %s failed: status=%s reason=%s", command, resp.status_code, getattr(resp, "reason", ""))
            return None
        text = resp.text.lstrip()
        if text.startswith("OK:"):
            text = text[3:].lstrip()
        return json.loads(text)
    except Exception as e:
        log.error("API error %s: %s", command, e)
        return None


