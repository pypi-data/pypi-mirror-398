from __future__ import annotations

from typing import Optional

import sys
from pathlib import Path

from alembic import context
from sqlmodel import SQLModel


# Ensure package importability in dev (when running from repo root)
try:
    import pushikoo  # noqa: F401
except Exception:  # pragma: no cover - dev convenience
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# Alembic Context
config = context.config

# Your models' metadata for autogenerate
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL. Prefer a URL passed via
    Config (sqlalchemy.url); otherwise attempt to infer from app engine.
    """
    url: Optional[str] = config.get_main_option("sqlalchemy.url")
    if not url:
        try:
            from pushikoo.db import engine as app_engine

            url = str(app_engine.url)
        except Exception:  # pragma: no cover - best-effort fallback
            url = None

    if not url:
        raise RuntimeError("No database URL available for offline migrations")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Prefer a connection injected via Config attributes["connection"].
    If absent, fall back to the application's engine.
    """
    connection = config.attributes.get("connection")
    close_conn = False

    if connection is None:
        from pushikoo.db import engine as app_engine

        connection = app_engine.connect()
        close_conn = True

    try:
        is_sqlite = getattr(connection.dialect, "name", "") == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()
    finally:
        if close_conn:
            connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
