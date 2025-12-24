import logging
from importlib.metadata import version

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from lecrapaud.config import (
    LOGGING_LEVEL,
    PYTHON_ENV,
    SENTRY_DSN,
    SENTRY_PROFILES_SAMPLE_RATE,
    SENTRY_TRACES_SAMPLE_RATE,
)


def _release_version():
    try:
        return f"lecrapaud@{version('lecrapaud')}"
    except Exception:
        return None


def init_sentry():
    """
    Initialize Sentry if a DSN is configured.
    Returns True when enabled, False otherwise.
    """
    if not SENTRY_DSN:
        return False

    sentry_logging = LoggingIntegration(
        level=getattr(logging, LOGGING_LEVEL.upper(), logging.INFO),
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=PYTHON_ENV,
        release=_release_version(),
        integrations=[sentry_logging],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
    )

    return True
