from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB_POOL_SIZE = 5
DEFAULT_DB_MAX_OVERFLOW = 10
DEFAULT_DB_POOL_TIMEOUT_SECONDS = 30
DEFAULT_DB_POOL_RECYCLE_SECONDS = 1800


def _read_int_env(name: str, default: int, *, minimum: int | None = None) -> int:
	raw_value = os.getenv(name, str(default)).strip()
	try:
		parsed = int(raw_value)
	except ValueError:
		return default
	if minimum is not None and parsed < minimum:
		return default
	return parsed


DB_POOL_SIZE = _read_int_env("DB_POOL_SIZE", DEFAULT_DB_POOL_SIZE, minimum=1)
DB_MAX_OVERFLOW = _read_int_env("DB_MAX_OVERFLOW", DEFAULT_DB_MAX_OVERFLOW, minimum=0)
DB_POOL_TIMEOUT_SECONDS = _read_int_env(
	"DB_POOL_TIMEOUT_SECONDS",
	DEFAULT_DB_POOL_TIMEOUT_SECONDS,
	minimum=1,
)
DB_POOL_RECYCLE_SECONDS = _read_int_env(
	"DB_POOL_RECYCLE_SECONDS",
	DEFAULT_DB_POOL_RECYCLE_SECONDS,
	minimum=1,
)

def _resolve_database_url() -> str:
	database_url = os.getenv("IDENTITY_DATABASE_URL")
	if not database_url or not database_url.strip():
		raise RuntimeError("IDENTITY_DATABASE_URL must be configured")
	database_url = database_url.strip()
	if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
		return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
	return database_url


def _create_engine(database_url: str) -> Engine:
	return create_engine(
		database_url,
		pool_pre_ping=True,
		pool_size=DB_POOL_SIZE,
		max_overflow=DB_MAX_OVERFLOW,
		pool_timeout=DB_POOL_TIMEOUT_SECONDS,
		pool_recycle=DB_POOL_RECYCLE_SECONDS,
	)


identity_engine = _create_engine(_resolve_database_url())
IdentitySessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=identity_engine,
)


def get_identity_db_session() -> Generator[Session, None, None]:
	db = IdentitySessionLocal()
	try:
		yield db
	finally:
		db.close()


def check_identity_database_ready() -> None:
	with IdentitySessionLocal() as db:
		db.execute(text("SELECT 1")).scalar_one()
