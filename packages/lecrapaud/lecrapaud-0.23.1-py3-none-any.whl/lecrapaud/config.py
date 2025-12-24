import os
from dotenv import load_dotenv

load_dotenv(override=False)

PYTHON_ENV = os.getenv("PYTHON_ENV")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

DB_USER = (
    os.getenv("TEST_DB_USER") if PYTHON_ENV == "Test" else os.getenv("DB_USER", None)
)
DB_PASSWORD = (
    os.getenv("TEST_DB_PASSWORD", "")
    if PYTHON_ENV == "Test"
    else os.getenv("DB_PASSWORD", "")
)
DB_HOST = (
    os.getenv("TEST_DB_HOST") if PYTHON_ENV == "Test" else os.getenv("DB_HOST", None)
)
DB_PORT = (
    os.getenv("TEST_DB_PORT") if PYTHON_ENV == "Test" else os.getenv("DB_PORT", None)
)
DB_NAME = (
    os.getenv("TEST_DB_NAME") if PYTHON_ENV == "Test" else os.getenv("DB_NAME", None)
)
DB_URI: str = (
    os.getenv("TEST_DB_URI", None)
    if PYTHON_ENV == "Test"
    else os.getenv("DB_URI", None)
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LECRAPAUD_LOGFILE = os.getenv("LECRAPAUD_LOGFILE")
LECRAPAUD_TABLE_PREFIX = os.getenv("LECRAPAUD_TABLE_PREFIX", "lecrapaud")
LECRAPAUD_OPTIMIZATION_BACKEND = os.getenv(
    "LECRAPAUD_OPTIMIZATION_BACKEND", "hyperopt"
).lower()

SENTRY_DSN = os.getenv("SENTRY_DSN")

try:
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0"))
except ValueError:
    SENTRY_TRACES_SAMPLE_RATE = 0.0

try:
    SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0"))
except ValueError:
    SENTRY_PROFILES_SAMPLE_RATE = 0.0

LECRAPAUD_SAVE_FULL_TRAIN_DATA = (
    os.getenv("LECRAPAUD_SAVE_FULL_TRAIN_DATA", "False").lower() == "true"
)
