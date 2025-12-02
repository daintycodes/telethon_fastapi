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
try:
    if config.config_file_name and os.path.exists(config.config_file_name):
        fileConfig(config.config_file_name)
    else:
        # No config file present; skip logging configuration
        pass
except Exception:
    # If any logging config issue occurs, continue without failing migrations
    pass

# Add your model's MetaData object here for 'autogenerate' support
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.models import Base

target_metadata = Base.metadata


def get_url():
    return os.getenv("DATABASE_URL", "sqlite:///./telethon.db")


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
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
