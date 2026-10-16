from app.core.config import settings
from app.core.logging_config import request_id_var

ACCESS_LOGGER = "app.access"
_enabled = False

# Nothing from the request is attached to events: bodies, cookies and headers carry
# passwords and tokens, and local variables of auth frames hold plaintext credentials.
DATA_COLLECTION = {
    "user_info": False,
    "cookies": {"mode": "off"},
    "http_headers": {"request": {"mode": "off"}},
    "http_bodies": [],
    "url_query_params": {"mode": "off"},
    "stack_frame_variables": False,
}


def init_sentry() -> bool:
    """Start Sentry error reporting when SENTRY_DSN is set. Returns whether it started.

    sentry-sdk is imported lazily so deployments without a DSN pay nothing.
    """
    global _enabled
    if not settings.SENTRY_DSN:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.logging import ignore_logger

    # The access log writes 5xx lines at ERROR, which would add a second, empty event
    # next to the real exception report.
    ignore_logger(ACCESS_LOGGER)
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        release=settings.APP_VERSION,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        data_collection=DATA_COLLECTION,
    )
    _enabled = True
    return True


def capture_exception(exc: BaseException) -> None:
    """Report an exception the app handled itself, tagged with the request id.

    Call it before logging the same exception: Sentry's logging integration would
    report it again, and drops that second report as a duplicate of this one.
    """
    if not _enabled:
        return
    import sentry_sdk

    with sentry_sdk.new_scope() as scope:
        scope.set_tag("request_id", request_id_var.get())
        sentry_sdk.capture_exception(exc)
