from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from shared_backend.database import (
	check_database_ready,
	configure_database_access,
	get_db_session as shared_get_db_session,
)

_IDENTITY_DATABASE = configure_database_access(
	write_env="IDENTITY_WRITE_DATABASE_URL",
	read_env="IDENTITY_READ_DATABASE_URL",
	write_fallback_env_names=("IDENTITY_DATABASE_URL",),
	read_fallback_env_names=("IDENTITY_DATABASE_URL",),
)

IDENTITY_READ_DATABASE_URL = _IDENTITY_DATABASE.read_url
IDENTITY_WRITE_DATABASE_URL = _IDENTITY_DATABASE.write_url
IDENTITY_DATABASE_URL = IDENTITY_READ_DATABASE_URL

identity_read_engine = _IDENTITY_DATABASE.read_engine
IdentityReadSessionLocal = _IDENTITY_DATABASE.read_session_factory
IdentityWriteSessionLocal = _IDENTITY_DATABASE.write_session_factory
IdentitySessionLocal = IdentityWriteSessionLocal


def get_identity_read_db_session() -> Generator[Session, None, None]:
	yield from shared_get_db_session(IdentityReadSessionLocal)


def get_identity_write_db_session() -> Generator[Session, None, None]:
	yield from shared_get_db_session(IdentityWriteSessionLocal)


def check_identity_read_database_ready() -> None:
	check_database_ready(identity_read_engine)


def check_identity_database_ready() -> None:
	check_identity_read_database_ready()
