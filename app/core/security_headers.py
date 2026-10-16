from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

API_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}
# This service only serves JSON; Swagger UI (dev only) needs scripts, so no CSP there.
API_CSP = "default-src 'none'; frame-ancestors 'none'"
HSTS = "max-age=63072000; includeSubDomains"


class SecurityHeadersMiddleware:
    """Add baseline security headers to every HTTP response."""

    def __init__(self, app: ASGIApp, *, strict: bool):
        self.app = app
        self.headers = dict(API_HEADERS)
        if strict:
            self.headers["Content-Security-Policy"] = API_CSP
            self.headers["Strict-Transport-Security"] = HSTS

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in self.headers.items():
                    headers.setdefault(name, value)
                if scope["path"].startswith("/auth"):
                    headers.setdefault("Cache-Control", "no-store")
            await send(message)

        await self.app(scope, receive, send_with_headers)
