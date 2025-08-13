from __future__ import annotations

import threading
from typing import Dict, List, Tuple


API_HISTOGRAM_BUCKETS: Tuple[float, ...] = (0.1, 0.5, 1.0, 2.0, 5.0, 10.0)


class _ApiLatencyAgg:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # command -> {"buckets": [counts per bucket incl +Inf], "sum": float, "count": int}
        self._state: Dict[str, Dict[str, object]] = {}

    def observe(self, command: str, seconds: float) -> None:
        with self._lock:
            st = self._state.get(command)
            if st is None:
                st = {"buckets": [0] * (len(API_HISTOGRAM_BUCKETS) + 1), "sum": 0.0, "count": 0}
                self._state[command] = st
            buckets: List[int] = st["buckets"]  # type: ignore[assignment]
            st["sum"] = float(st["sum"]) + float(seconds)  # type: ignore[index]
            st["count"] = int(st["count"]) + 1  # type: ignore[index]
            # increment buckets up to threshold and +Inf
            for i, le in enumerate(API_HISTOGRAM_BUCKETS):
                if seconds <= le:
                    buckets[i] += 1
            # +Inf bucket always increments once
            buckets[-1] += 1

    def snapshot(self) -> Dict[str, Dict[str, object]]:
        with self._lock:
            # return a shallow copy safe for reading
            out: Dict[str, Dict[str, object]] = {}
            for cmd, st in self._state.items():
                out[cmd] = {
                    "buckets": list(st["buckets"]),  # type: ignore[index]
                    "sum": float(st["sum"]),  # type: ignore[index]
                    "count": int(st["count"])  # type: ignore[index]
                }
            return out


api_latency_agg = _ApiLatencyAgg()


