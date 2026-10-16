"""Gunicorn settings for the container: gunicorn -c gunicorn.conf.py app.main:app

Tuned through environment variables so one image fits every environment:
WEB_CONCURRENCY (workers), GUNICORN_TIMEOUT, GUNICORN_GRACEFUL_TIMEOUT,
GUNICORN_MAX_REQUESTS and FORWARDED_ALLOW_IPS (see README, "Deployment").
"""

import os
import shutil
from pathlib import Path

from app.core.config import settings

bind = f"{settings.HOST}:{settings.PORT}"
worker_class = "uvicorn_worker.UvicornWorker"
# Each worker has its own DB pool (DB_POOL_SIZE + DB_MAX_OVERFLOW connections).
workers = int(os.getenv("WEB_CONCURRENCY", "2"))

# A worker silent for `timeout` seconds is killed; on SIGTERM, in-flight requests get
# `graceful_timeout` seconds to finish. Keep both below the orchestrator's kill delay.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = 5
# Recycle workers after N requests (0 = never); jitter avoids restarting them all at once.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "0"))
max_requests_jitter = max_requests // 10

# Heartbeat file on tmpfs: a slow disk would otherwise get workers killed by the arbiter.
worker_tmp_dir = "/dev/shm" if os.path.isdir("/dev/shm") else None

# X-Forwarded-For / -Proto are only trusted from these peers. Behind a reverse proxy
# or load balancer set it to that proxy's address(es), otherwise every client shares
# the proxy's IP (and one rate-limit bucket).
forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1,::1")

# Requests are logged by RequestContextMiddleware (JSON, with request id).
accesslog = None
errorlog = "-"
loglevel = settings.LOG_LEVEL.lower()
# Gunicorn's own messages (master and worker lifecycle) use the application format.
# The root logger is configured by the app itself inside each worker.
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "app.core.logging_config.RequestIdFilter"}},
    "formatters": {"app": {"()": "app.core.logging_config.build_formatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "app",
            "filters": ["request_id"],
        }
    },
    "root": {"level": "WARNING", "handlers": []},
    "loggers": {
        "gunicorn.error": {
            "level": loglevel.upper(),
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

if settings.PROMETHEUS_ENABLED:
    # Must be set before any worker imports the app (metrics are created at import).
    # The directory is emptied on every start: stale files would resurrect old counters.
    _metrics_dir = Path(
        os.environ.setdefault(
            "PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus"
        )  # nosec B108
    )

    def on_starting(server):
        shutil.rmtree(_metrics_dir, ignore_errors=True)
        _metrics_dir.mkdir(parents=True, exist_ok=True)

    def child_exit(server, worker):
        # Stop reporting the live gauges of a dead worker (counters are kept).
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(worker.pid)
