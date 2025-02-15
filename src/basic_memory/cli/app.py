import asyncio

import typer

from basic_memory import db
from basic_memory.config import config
from basic_memory.utils import setup_logging

setup_logging(log_file=".basic-memory/basic-memory-cli.log")  # pragma: no cover

asyncio.run(db.run_migrations(config))

app = typer.Typer()
