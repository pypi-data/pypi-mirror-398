"""
FastDjango database backends.
Configuration for different database engines.
"""

from typing import Any


def get_database_url(config: dict[str, Any]) -> str:
    """
    Build a database URL from configuration dictionary.

    Args:
        config: Database configuration dictionary with keys:
            - ENGINE: Database engine (aiosqlite, asyncpg, asyncmy)
            - NAME: Database name
            - USER: Username (optional)
            - PASSWORD: Password (optional)
            - HOST: Host (optional, default: localhost)
            - PORT: Port (optional)

    Returns:
        Database URL string
    """
    engine = config.get("ENGINE", "aiosqlite")
    name = config.get("NAME", "db.sqlite3")
    user = config.get("USER", "")
    password = config.get("PASSWORD", "")
    host = config.get("HOST", "localhost")
    port = config.get("PORT")

    if engine == "aiosqlite":
        return f"sqlite://{name}"

    elif engine == "asyncpg":
        port = port or 5432
        if user and password:
            return f"postgres://{user}:{password}@{host}:{port}/{name}"
        elif user:
            return f"postgres://{user}@{host}:{port}/{name}"
        else:
            return f"postgres://{host}:{port}/{name}"

    elif engine == "asyncmy":
        port = port or 3306
        if user and password:
            return f"mysql://{user}:{password}@{host}:{port}/{name}"
        elif user:
            return f"mysql://{user}@{host}:{port}/{name}"
        else:
            return f"mysql://{host}:{port}/{name}"

    else:
        # Assume it's already a URL
        return engine


# Supported database backends
SUPPORTED_BACKENDS = {
    "aiosqlite": {
        "name": "SQLite (async)",
        "driver": "aiosqlite",
        "default_port": None,
    },
    "asyncpg": {
        "name": "PostgreSQL (async)",
        "driver": "asyncpg",
        "default_port": 5432,
    },
    "asyncmy": {
        "name": "MySQL (async)",
        "driver": "asyncmy",
        "default_port": 3306,
    },
}


__all__ = [
    "get_database_url",
    "SUPPORTED_BACKENDS",
]
