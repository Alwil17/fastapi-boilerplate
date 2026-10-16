import hmac
import time

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests handled",
    ["method", "path", "status"],
)
DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
IN_PROGRESS = Gauge("http_requests_in_progress", "HTTP requests being handled")

UNMATCHED = "unmatched"


class MetricsMiddleware:
    """Count requests and time them, labelled by route *template*.

    Labelling with the raw URL would create one time series per id (or per scanner
    probe) and exhaust the metrics backend; unmatched URLs share one label.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] == "/metrics":
            await self.app(scope, receive, send)
            return

        status_code = 500
        started_at = time.perf_counter()

        async def send_capturing_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        IN_PROGRESS.inc()
        try:
            await self.app(scope, receive, send_capturing_status)
        finally:
            IN_PROGRESS.dec()
            # The router stores the matched route in the (shared) scope.
            route = scope.get("route")
            path = getattr(route, "path", UNMATCHED)
            method = scope["method"]
            REQUESTS.labels(method, path, str(status_code)).inc()
            DURATION.labels(method, path).observe(time.perf_counter() - started_at)


def _authorize(request: Request) -> None:
    token = settings.METRICS_TOKEN
    if not token:
        return
    supplied = request.headers.get("Authorization", "")
    if not hmac.compare_digest(supplied.encode(), f"Bearer {token}".encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid metrics token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def install_metrics(app: FastAPI) -> None:
    """Add the metrics middleware and a GET /metrics endpoint (Prometheus format)."""

    def metrics(request: Request) -> Response:
        _authorize(request)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.add_middleware(MetricsMiddleware)
    app.add_api_route("/metrics", metrics, include_in_schema=False)
