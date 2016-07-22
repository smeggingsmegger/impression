from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

'''
WARNING: THIS IS AN UGLY HACK TO GET AUTO-GENERATION WORKING.
'''
import sys
import os
os.environ['RUNNING_ALEMBIC'] = '1'
SQLALCHEMY_DATABASE_URI = os.environ.get('IMPRESSION_DB_URI', 'sqlite:///../impression/impression.db')

alembic_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
impression_path = os.path.join(alembic_path, os.pardir)

sys.path.append(impression_path)

from impression import db
from impression.models import *
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # Override sqlalchemy.url value to application's value
    alembic_config = config.get_section(config.config_ini_section)
    alembic_config['sqlalchemy.url'] = SQLALCHEMY_DATABASE_URI

    engine = engine_from_config(
                alembic_config,
                prefix='sqlalchemy.',
                poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                render_as_batch=config.get_main_option('sqlalchemy.url').startswith('sqlite:///')
                )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
