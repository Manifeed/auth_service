from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.schemas.user_context import AuthenticatedUserContext
from app.services.user_read_service import build_authenticated_user_read

from shared_backend.utils.auth_utils import hash_secret_token
from shared_backend.errors.custom_exceptions import (
	ExpiredSessionTokenError,
	InactiveUserError,
	InvalidSessionTokenError,
	MissingSessionTokenError,
	UserNotFoundError,
)
from shared_backend.schemas.auth.auth_schema import (
	AuthLogoutRead,
	AuthSessionRead,
)

DEFAULT_SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
DEFAULT_SESSION_TOUCH_INTERVAL_SECONDS = 5 * 60
DEFAULT_SESSION_PURGE_INTERVAL_SECONDS = 15 * 60
DEFAULT_SESSION_REVOKED_RETENTION_SECONDS = 24 * 60 * 60
DEFAULT_MAX_ACTIVE_SESSIONS_PER_USER = 5


def read_current_session(
	db: Session,
	current_user: AuthenticatedUserContext,
) -> AuthSessionRead:
	user = identity_database_client.get_user_by_id(db, user_id=current_user.user_id)
	if user is None:
		raise UserNotFoundError()
	return AuthSessionRead(
		expires_at=current_user.session_expires_at,
		user=build_authenticated_user_read(user),
	)


def read_current_session_by_token(
	db: Session,
	*,
	session_token: str,
	commit: bool = True,
) -> AuthSessionRead:
	current_user = resolve_session_token(db, session_token=session_token, commit=commit)
	return read_current_session(db, current_user)


def logout_session_token(
	db: Session,
	*,
	session_token: str,
	commit: bool = True,
) -> AuthLogoutRead:
	try:
		identity_database_client.revoke_user_session_by_token_hash(
			db,
			token_hash=hash_secret_token(session_token),
		)
		if commit:
			db.commit()
	except Exception:
		if commit:
			db.rollback()
		raise

	return AuthLogoutRead(ok=True)


def enforce_user_session_limit(db: Session, *, user_id: int) -> int:
	return identity_database_client.revoke_excess_active_user_sessions(
		db,
		user_id=user_id,
		keep_limit=resolve_max_active_sessions_per_user(),
	)


def purge_retired_sessions(
	db: Session,
	*,
	commit: bool = True,
) -> int:
	now = datetime.now(timezone.utc)
	try:
		purged_count = identity_database_client.purge_retired_user_sessions(
			db,
			expired_before=now,
			revoked_before=now - timedelta(seconds=resolve_session_revoked_retention_seconds()),
		)
		if commit:
			db.commit()
	except Exception:
		if commit:
			db.rollback()
		raise
	return purged_count


def resolve_session_token(
	db: Session,
	*,
	session_token: str,
	commit: bool = True,
) -> AuthenticatedUserContext:
	if not session_token:
		raise MissingSessionTokenError()

	token_hash = hash_secret_token(session_token)
	session_context = identity_database_client.get_user_session_context_by_token_hash(
		db,
		token_hash=token_hash,
	)
	if session_context is None:
		raise InvalidSessionTokenError()
	if session_context.expires_at <= datetime.now(timezone.utc):
		identity_database_client.revoke_user_session_by_token_hash(
			db,
			token_hash=token_hash,
		)
		if commit:
			db.commit()
		raise ExpiredSessionTokenError()
	if not session_context.user.is_active:
		raise InactiveUserError()

	if _should_touch_session(session_context.last_seen_at):
		identity_database_client.touch_user_session(db, token_hash=token_hash)
		if commit:
			db.commit()
	return AuthenticatedUserContext(
		user_id=session_context.user.id,
		email=session_context.user.email,
		role=session_context.user.role,
		is_active=session_context.user.is_active,
		api_access_enabled=session_context.user.api_access_enabled,
		session_expires_at=session_context.expires_at,
	)


def _should_touch_session(last_seen_at: datetime | None) -> bool:
	if last_seen_at is None:
		return True
	return last_seen_at <= datetime.now(timezone.utc) - timedelta(
		seconds=resolve_session_touch_interval_seconds()
	)


def resolve_session_touch_interval_seconds() -> int:
	raw_value = os.getenv(
		"AUTH_SESSION_TOUCH_INTERVAL_SECONDS",
		str(DEFAULT_SESSION_TOUCH_INTERVAL_SECONDS),
	).strip()
	try:
		parsed = int(raw_value)
	except ValueError:
		return DEFAULT_SESSION_TOUCH_INTERVAL_SECONDS
	if parsed < 0:
		return DEFAULT_SESSION_TOUCH_INTERVAL_SECONDS
	return parsed


def resolve_session_purge_interval_seconds() -> int:
	return _read_positive_int_env(
		"AUTH_SESSION_PURGE_INTERVAL_SECONDS",
		DEFAULT_SESSION_PURGE_INTERVAL_SECONDS,
	)


def resolve_session_revoked_retention_seconds() -> int:
	return _read_positive_int_env(
		"AUTH_SESSION_REVOKED_RETENTION_SECONDS",
		DEFAULT_SESSION_REVOKED_RETENTION_SECONDS,
	)


def resolve_max_active_sessions_per_user() -> int:
	return _read_positive_int_env(
		"AUTH_MAX_ACTIVE_SESSIONS_PER_USER",
		DEFAULT_MAX_ACTIVE_SESSIONS_PER_USER,
	)


def _read_positive_int_env(name: str, default: int) -> int:
	raw_value = os.getenv(name, str(default)).strip()
	try:
		parsed = int(raw_value)
	except ValueError:
		return default
	if parsed <= 0:
		return default
	return parsed


def resolve_session_ttl_seconds() -> int:
	raw_value = os.getenv(
		"AUTH_SESSION_TTL_SECONDS",
		str(DEFAULT_SESSION_TTL_SECONDS),
	).strip()
	try:
		parsed = int(raw_value)
	except ValueError:
		return DEFAULT_SESSION_TTL_SECONDS
	if parsed <= 0:
		return DEFAULT_SESSION_TTL_SECONDS
	return parsed
