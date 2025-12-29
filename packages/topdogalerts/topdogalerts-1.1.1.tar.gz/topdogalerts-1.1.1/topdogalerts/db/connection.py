# topdogalerts/db/connection.py
"""
Database connection helpers for topdogalerts.

Provides functions for creating database connections using environment variables.
"""
import os
from typing import List
from urllib.parse import quote_plus

import psycopg2
from psycopg2.extensions import connection as PGConnection


def _get_missing_env_vars() -> List[str]:
    """
    Check for required database environment variables.

    Returns a list of missing variable names.
    """
    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_SSLMODE"]
    return [var for var in required_vars if not os.getenv(var)]


def get_connection() -> PGConnection:
    """
    Create a new psycopg2 connection using environment variables.

    Required environment variables:
        DB_HOST     - Database host
        DB_NAME     - Database name
        DB_USER     - Database user
        DB_PASSWORD - Database password

    Optional environment variables:
        DB_PORT     - Database port (defaults to PostgreSQL default)

    Returns:
        A new psycopg2 connection object.

    Raises:
        RuntimeError: If required environment variables are missing.

    Note:
        Caller is responsible for closing the connection.
    """
    missing = _get_missing_env_vars()
    if missing:
        raise RuntimeError(f"Missing required DB env vars: {', '.join(missing)}")

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE"),
    )

    return conn


def get_async_connection_string() -> str:
    """
    Build a PostgreSQL connection string for asyncpg.

    Required environment variables:
        DB_HOST     - Database host
        DB_NAME     - Database name
        DB_USER     - Database user
        DB_PASSWORD - Database password

    Optional environment variables:
        DB_PORT     - Database port (defaults to 5432)

    Returns:
        A PostgreSQL connection string in the format:
        postgresql://user:password@host:port/dbname

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    missing = _get_missing_env_vars()
    if missing:
        raise RuntimeError(f"Missing required DB env vars: {', '.join(missing)}")

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    sslmode = os.getenv("DB_SSLMODE")

    # URL-encode user and password to handle special characters
    user_encoded = quote_plus(user)
    password_encoded = quote_plus(password)

    # Handle IPv6 addresses (wrap in brackets)
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    return f"postgresql://{user_encoded}:{password_encoded}@{host}:{port}/{dbname}?sslmode={sslmode}"
