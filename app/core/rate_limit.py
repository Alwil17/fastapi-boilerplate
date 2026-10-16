import math
import time

from fastapi import HTTPException, Request, status
from limits import parse
from limits.storage import storage_from_string
from limits.strategies import MovingWindowRateLimiter

from app.core.config import settings

_limiter = MovingWindowRateLimiter(storage_from_string(settings.RATE_LIMIT_STORAGE_URI))


def reset_rate_limits() -> None:
    """Forget every counter (used by tests)."""
    _limiter.storage.reset()


def rate_limit(limit: str, scope: str):
    """Dependency factory: allow `limit` (e.g. "5/minute") per client IP and `scope`.

    The memory:// storage is per process; behind several workers/replicas point
    RATE_LIMIT_STORAGE_URI at Redis (redis://host:6379) so counters are shared.
    """
    item = parse(limit)

    def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        client = request.client.host if request.client else "unknown"
        if not _limiter.hit(item, scope, client):
            reset_at = _limiter.get_window_stats(item, scope, client).reset_time
            retry_after = max(1, math.ceil(reset_at - time.time()))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
