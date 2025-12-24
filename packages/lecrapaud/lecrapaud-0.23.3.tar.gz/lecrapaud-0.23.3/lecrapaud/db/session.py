"""Database session management and initialization module."""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse

from alembic.config import Config
from alembic import command
import os

from lecrapaud.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, DB_URI

_engine = None
_SessionLocal = None

if DB_URI:
    if "mysql://" in DB_URI and "pymysql://" not in DB_URI:
        DB_URI = DB_URI.replace("mysql://", "mysql+pymysql://")
    DATABASE_URL = DB_URI
elif DB_USER:
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    DATABASE_URL = None


def init_db(uri: str = None):
    global _engine, _SessionLocal, DATABASE_URL, DB_URI
    if _SessionLocal is not None:
        return

    # Step 0: Set database URI
    if uri:
        if "mysql://" in uri and "pymysql://" not in uri:
            uri = uri.replace("mysql://", "mysql+pymysql://")
        DATABASE_URL = uri
    elif DATABASE_URL:
        pass
    else:
        raise ValueError(
            "No database configuration found, please set env variables "
            "DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME or DB_URI, "
            "or provide a `uri` argument to LeCrapaud"
        )
    print(f"Initializing database with URI: {DATABASE_URL}")

    # Step 1: Create root engine without database
    parsed = urlparse(DATABASE_URL)
    db_name = parsed.path.lstrip("/")  # remove leading slash
    root_uri = f"{parsed.scheme}://{parsed.netloc}"
    root_engine = create_engine(root_uri)

    # Step 2: Create database if it doesn't exist
    with root_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
        conn.commit()

    # Step 3: Configure main engine with connection pooling and reconnection settings
    _engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Check connection health before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_timeout=30,  # Wait 30 seconds for a connection from the pool
        pool_size=10,  # Maintain up to 10 connections
        max_overflow=10,  # Allow up to 10 more connections during spikes
        connect_args={
            "connect_timeout": 10,  # 10 second connection timeout
        },
    )

    # Step 4: Configure session factory
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        expire_on_commit=False,  # Prevent detached instance errors
    )

    # Step 5: Apply Alembic migrations programmatically
    current_dir = os.path.dirname(__file__)  # → lecrapaud/db
    alembic_ini_path = os.path.join(current_dir, "alembic.ini")
    alembic_dir = os.path.join(
        current_dir, "alembic"
    )  # Use absolute path to alembic directory

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", alembic_dir)  # Use absolute path
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    command.upgrade(alembic_cfg, "head")


# Dependency to get a session instance
@contextmanager
def get_db():
    """Get a database session with automatic connection management.

    Yields:
        Session: A SQLAlchemy session instance

    The session is automatically committed if no exceptions occur, and rolled back otherwise.
    The connection is automatically returned to the pool when the session is closed.
    """
    if _SessionLocal is None:
        init_db()

    db = _SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise Exception(e) from e
    finally:
        db.close()
