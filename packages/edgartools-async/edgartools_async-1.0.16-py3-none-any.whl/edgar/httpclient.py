import logging
import os
from contextlib import asynccontextmanager, contextmanager
import time
import asyncio
from collections import deque
import threading
from pathlib import Path
from typing import AsyncGenerator, Generator, Optional

import httpx

from edgar.core import get_identity, strtobool, log

from .core import edgar_data_dir

MAX_SUBMISSIONS_AGE_SECONDS = 10 * 60  # Check for submissions every 10 minutes
MAX_INDEX_AGE_SECONDS = 30 * 60  # Check for updates to index (ie: daily-index) every 30 minutes

# rules are regular expressions matching the request url path: 
# The value determines whether it is cached or not:
# - int > 0: how many seconds it'll be considered valid. During this time, the cached object will not be revalidated.
# - False or 0: Do not cache
# - True: Cache forever, never revalidate
# - None: Determine cachability using response cache headers only. 
#
# Note that: revalidation consumes rate limit "hit", but will be served from cache if the data hasn't changed.


CACHE_RULES = {
    r".*\.sec\.gov": {
        "/submissions.*": MAX_SUBMISSIONS_AGE_SECONDS,
        r"/include/ticker\.txt.*": MAX_SUBMISSIONS_AGE_SECONDS,
        r"/files/company_tickers\.json.*": MAX_SUBMISSIONS_AGE_SECONDS,
        ".*index/.*": MAX_INDEX_AGE_SECONDS,
        "/Archives/edgar/data": True,  # cache forever
    }
}

def get_cache_directory() -> str:
    cachedir = Path(edgar_data_dir) / "_tcache"
    cachedir.mkdir(parents=True, exist_ok=True)

    return str(cachedir)


def get_edgar_verify_ssl():
    """
    Returns True if using SSL verification on http requests
    """

    if "EDGAR_VERIFY_SSL" in os.environ:
        return strtobool(os.environ["EDGAR_VERIFY_SSL"])
    else:
        return True


_REQUESTS_PER_SEC = 9


class AsyncRateLimiter:
    """Simple, process-wide async sliding-window rate limiter.

    Guarantees at most `rate` requests per second across all async callers.
    """

    def __init__(self, rate: int):
        self.rate = max(1, int(rate))
        self._timestamps = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        window = 1.0
        while True:
            async with self._lock:
                now = time.monotonic()
                while self._timestamps and (now - self._timestamps[0]) > window:
                    self._timestamps.popleft()
                if len(self._timestamps) < self.rate:
                    self._timestamps.append(now)
                    log.debug(f"Rate limiter: acquired slot ({len(self._timestamps)}/{self.rate})")
                    return
                # Need to wait until the oldest slot expires
                sleep_for = max(0.0, window - (now - self._timestamps[0]))
            # Sleep outside the lock
            log.debug(f"Rate limiter: sleeping {sleep_for:.3f}s (bucket full)")
            await asyncio.sleep(sleep_for if sleep_for > 0 else 0)


_ASYNC_GLOBAL_LIMITER: Optional[AsyncRateLimiter] = None


def _get_async_limiter(rate: int) -> AsyncRateLimiter:
    global _ASYNC_GLOBAL_LIMITER
    if _ASYNC_GLOBAL_LIMITER is None or _ASYNC_GLOBAL_LIMITER.rate != max(1, int(rate)):
        _ASYNC_GLOBAL_LIMITER = AsyncRateLimiter(rate)
    return _ASYNC_GLOBAL_LIMITER


def get_http_mgr(cache_enabled: bool = True, request_per_sec_limit: int = 9):
    global _REQUESTS_PER_SEC
    _REQUESTS_PER_SEC = int(request_per_sec_limit)
    if cache_enabled:
        cache_dir = get_cache_directory()
        cache_mode = "Hishel-File"
    else:
        cache_dir = None
        cache_mode = "Disabled"

    # Try throttle/cache manager lazily; fall back to simple manager on failure
    try:
        from httpxthrottlecache import HttpxThrottleCache  # lazy import
        http_mgr = HttpxThrottleCache(
            user_agent_factory=get_identity,
            cache_dir=cache_dir,
            cache_mode=cache_mode,
            request_per_sec_limit=request_per_sec_limit,
            cache_rules=CACHE_RULES,
            rate_limiter_enabled=False,  # Use our own async rate limiter instead
        )
        http_mgr.httpx_params["verify"] = get_edgar_verify_ssl()
        return http_mgr
    except Exception as e:
        log.warning("Failed to initialize httpxthrottlecache (%s). Falling back to SimpleHTTPManager.", e)

        class SimpleHTTPManager:
            """
            Lightweight HTTP manager used when httpxthrottlecache is not available.
            Adds a simple global rate limiter to both sync and async clients via httpx event hooks
            so that SEC rate limits are still respected.
            """

            _lock = None           # asyncio lock for async limiter
            _timestamps = None     # shared timestamps deque
            _tlock = None          # threading lock for sync limiter

            def __init__(self):
                self.httpx_params = {"verify": get_edgar_verify_ssl()}
                # Shared limiter state (process-wide) for both sync/async
                if SimpleHTTPManager._lock is None:
                    SimpleHTTPManager._lock = asyncio.Lock()
                if SimpleHTTPManager._timestamps is None:
                    SimpleHTTPManager._timestamps = deque()
                if SimpleHTTPManager._tlock is None:
                    SimpleHTTPManager._tlock = threading.Lock()
                self._rate = max(1, int(request_per_sec_limit))

            # ---- Simple sliding window limiter (shared for sync/async) ----
            def _acquire_sync(self):
                window = 1.0
                while True:
                    with SimpleHTTPManager._tlock:
                        now = time.monotonic()
                        while SimpleHTTPManager._timestamps and (now - SimpleHTTPManager._timestamps[0]) > window:
                            SimpleHTTPManager._timestamps.popleft()
                        if len(SimpleHTTPManager._timestamps) < self._rate:
                            SimpleHTTPManager._timestamps.append(now)
                            return
                        sleep_for = max(0.0, window - (now - SimpleHTTPManager._timestamps[0]))
                    time.sleep(sleep_for if sleep_for > 0 else 0)

            async def _acquire_async(self):
                window = 1.0
                while True:
                    async with SimpleHTTPManager._lock:
                        now = time.monotonic()
                        while SimpleHTTPManager._timestamps and (now - SimpleHTTPManager._timestamps[0]) > window:
                            SimpleHTTPManager._timestamps.popleft()
                        if len(SimpleHTTPManager._timestamps) < self._rate:
                            SimpleHTTPManager._timestamps.append(now)
                            return
                        sleep_for = max(0.0, window - (now - SimpleHTTPManager._timestamps[0]))
                    await asyncio.sleep(sleep_for if sleep_for > 0 else 0)

            def _populate_user_agent(self, params: dict) -> dict:
                headers = params.get("headers", {}) or {}
                try:
                    ua = get_identity()
                except Exception:
                    ua = None
                if ua:
                    headers["User-Agent"] = ua
                params["headers"] = headers
                return params

            @asynccontextmanager
            async def async_http_client(self, client: Optional[httpx.AsyncClient] = None, **kwargs):
                params = self._populate_user_agent(self.httpx_params.copy())
                params.update(kwargs)
                if client is None:
                    # Attach async hook to enforce rate limiting per request
                    async def _hook(request):
                        await self._acquire_async()
                    hooks = params.get("event_hooks", {}) or {}
                    hooks.setdefault("request", []).append(_hook)
                    params["event_hooks"] = hooks
                    async with httpx.AsyncClient(**params) as c:
                        yield c
                else:
                    yield client

            @contextmanager
            def http_client(self, **kwargs):
                params = self._populate_user_agent(self.httpx_params.copy())
                params.update(kwargs)
                # Attach sync hook to enforce rate limiting per request
                def _hook(request):
                    self._acquire_sync()
                hooks = params.get("event_hooks", {}) or {}
                hooks.setdefault("request", []).append(_hook)
                params["event_hooks"] = hooks
                with httpx.Client(**params) as c:
                    yield c

            def close(self):
                pass

        return SimpleHTTPManager()


@asynccontextmanager
async def async_http_client(client: Optional[httpx.AsyncClient] = None, **kwargs) -> AsyncGenerator[httpx.AsyncClient, None]:
    # Optional escape hatch to avoid double limiting when relying solely on httpxthrottlecache
    disable_wrapper = str(os.getenv("EDGAR_DISABLE_ASYNC_WRAPPER_LIMITER", "0")).lower() in {"1", "true", "yes", "on"}

    if not disable_wrapper:
        async def _rl_hook(request):
            limiter = _get_async_limiter(_REQUESTS_PER_SEC)
            log.debug(f"Async rate limiter hook called for {request.url.host}")
            await limiter.acquire()

        if client is None:
            # Attach hook via constructor kwargs
            hooks = kwargs.get("event_hooks", {}) or {}
            hooks.setdefault("request", []).append(_rl_hook)
            kwargs["event_hooks"] = hooks
        else:
            # Attach idempotently to a provided client
            if not getattr(client, "_edgar_async_rl_hook_attached", False):
                hooks = getattr(client, "event_hooks", None)
                if hooks is not None:
                    hooks.setdefault("request", []).append(_rl_hook)
                    setattr(client, "_edgar_async_rl_hook_attached", True)

    async with HTTP_MGR.async_http_client(client=client, **kwargs) as client:
        yield client


@contextmanager
def http_client(**kwargs) -> Generator[httpx.Client, None, None]:
    with HTTP_MGR.http_client(**kwargs) as client:
        yield client


def get_http_params():
    return HTTP_MGR._populate_user_agent(HTTP_MGR.httpx_params.copy())


def close_clients():
    HTTP_MGR.close()


HTTP_MGR = get_http_mgr()
