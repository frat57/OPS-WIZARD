from __future__ import with_statement
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# set sqlalchemy.url from env if present (ci or runtime)
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Normalize common URL forms for SQLAlchemy 2.0 / Alembic
    # docker-compose often uses `postgres://...` but SQLAlchemy prefers a driver scheme
    if database_url.startswith('postgres://'):
        normalized = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        database_url = normalized
    # If user provided plain postgresql:// encourage using the psycopg driver
    if database_url.startswith('postgresql://') and 'psycopg' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

    # For debugging during migration/CI, make it visible which URL Alembic will use.
    # Keep secret values out of logs in production — this is development-friendly only.
    try:
        # write to alembic config (used by engine_from_config)
        config.set_main_option('sqlalchemy.url', database_url)
    except Exception as e:
        # bubble up but include helpful context
        raise RuntimeError(f"Failed to set sqlalchemy.url from DATABASE_URL (value starts with: {database_url[:40]}): {e}")

target_metadata = None


def run_migrations_offline():
    url = config.get_main_option('sqlalchemy.url')
    context.configure(url=url, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
