from __future__ import annotations

from typing import Iterable, List, Optional
import time
import logging


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
        now = time.time()
        start = now
        if self.cache_ttl_seconds and now < self._cache_until and self._cached is not None:
            for m in self._cached:
                yield m
            return
        if self._timed_out(start):
            if self._cached is not None:
                for m in self._cached:
                    yield m
            return
        try:
            metrics = self._collect_now()
        except Exception as e:
            self._log.warning("collector error: %s", e)
            metrics = self._cached or []
        self._cached = metrics
        self._cache_until = now + self.cache_ttl_seconds
        for m in metrics:
            yield m


