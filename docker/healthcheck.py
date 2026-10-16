"""Container HEALTHCHECK: GET /health/live on the local server (exit 1 on failure).

Sends a Host header the app accepts: with ALLOWED_HOSTS restricted, the default
"127.0.0.1" would be rejected by TrustedHostMiddleware and the container would be
reported unhealthy.
"""

import json
import os
import sys
import urllib.request


def allowed_hosts() -> list[str]:
    raw = os.environ.get("ALLOWED_HOSTS", "*").strip()
    if raw.startswith("["):
        return [str(host) for host in json.loads(raw)]
    return [host.strip() for host in raw.split(",") if host.strip()]


def probe_host() -> str:
    for host in allowed_hosts():
        if host == "*":
            break
        if host.startswith("*."):  # wildcard subdomain: any label matches
            return "healthcheck" + host[1:]
        if "*" not in host:
            return host
    return "localhost"


def main() -> int:
    port = os.environ.get("PORT", "8000")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/health/live", headers={"Host": probe_host()}
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:  # nosec B310
            return 0 if response.status == 200 else 1
    except Exception as exc:
        print(f"healthcheck failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
