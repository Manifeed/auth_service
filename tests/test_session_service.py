from datetime import datetime, timedelta, timezone

from app.schemas.user_context import (
	UserRecord,
	UserSessionContextRecord,
)
from app.services import session_service


class _FakeDb:
	def __init__(self) -> None:
		self.commits = 0
		self.rollbacks = 0

	def commit(self) -> None:
		self.commits += 1

	def rollback(self) -> None:
		self.rollbacks += 1


def _user() -> UserRecord:
	now = datetime.now(timezone.utc)
	return UserRecord(
		id=1,
		email="user@example.com",
		pseudo="user",
		pp_id=1,
		password_hash="hash",
		role="user",
		is_active=True,
		api_access_enabled=False,
		created_at=now,
		updated_at=now,
	)


def _session_context(last_seen_at: datetime | None) -> UserSessionContextRecord:
	return UserSessionContextRecord(
		user=_user(),
		expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
		last_seen_at=last_seen_at,
	)


def test_resolve_session_skips_recent_last_seen_touch(monkeypatch) -> None:
	db = _FakeDb()
	touched = []
	monkeypatch.setattr(session_service, "hash_secret_token", lambda token: "hash")
	monkeypatch.setattr(
		session_service.identity_database_client,
		"get_user_session_context_by_token_hash",
		lambda db, token_hash: _session_context(datetime.now(timezone.utc)),
	)
	monkeypatch.setattr(
		session_service.identity_database_client,
		"touch_user_session",
		lambda db, token_hash: touched.append(token_hash),
	)

	result = session_service.resolve_session_token(db, session_token="token")

	assert result.user_id == 1
	assert touched == []
	assert db.commits == 0
	assert db.rollbacks == 0


def test_resolve_session_touches_stale_last_seen(monkeypatch) -> None:
	db = _FakeDb()
	touched = []
	monkeypatch.setattr(session_service, "hash_secret_token", lambda token: "hash")
	monkeypatch.setattr(
		session_service.identity_database_client,
		"get_user_session_context_by_token_hash",
		lambda db, token_hash: _session_context(
			datetime.now(timezone.utc) - timedelta(minutes=10)
		),
	)
	monkeypatch.setattr(
		session_service.identity_database_client,
		"touch_user_session",
		lambda db, token_hash: touched.append(token_hash),
	)

	result = session_service.resolve_session_token(db, session_token="token")

	assert result.user_id == 1
	assert touched == ["hash"]
	assert db.commits == 1
	assert db.rollbacks == 0


def test_session_settings_fallback_to_defaults_for_invalid_values(monkeypatch) -> None:
	monkeypatch.setenv("AUTH_SESSION_PURGE_INTERVAL_SECONDS", "0")
	monkeypatch.setenv("AUTH_SESSION_REVOKED_RETENTION_SECONDS", "invalid")
	monkeypatch.setenv("AUTH_MAX_ACTIVE_SESSIONS_PER_USER", "-3")

	assert (
		session_service.resolve_session_purge_interval_seconds()
		== session_service.DEFAULT_SESSION_PURGE_INTERVAL_SECONDS
	)
	assert (
		session_service.resolve_session_revoked_retention_seconds()
		== session_service.DEFAULT_SESSION_REVOKED_RETENTION_SECONDS
	)
	assert (
		session_service.resolve_max_active_sessions_per_user()
		== session_service.DEFAULT_MAX_ACTIVE_SESSIONS_PER_USER
	)


def test_purge_retired_sessions_uses_retention_window(monkeypatch) -> None:
	db = _FakeDb()
	calls: list[tuple[datetime, datetime]] = []
	now = datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)

	class _FrozenDatetime(datetime):
		@classmethod
		def now(cls, tz=None):
			return now

	monkeypatch.setattr(session_service, "datetime", _FrozenDatetime)
	monkeypatch.setattr(
		session_service,
		"resolve_session_revoked_retention_seconds",
		lambda: 3600,
	)
	monkeypatch.setattr(
		session_service.identity_database_client,
		"purge_retired_user_sessions",
		lambda db, expired_before, revoked_before: calls.append((expired_before, revoked_before)) or 3,
	)

	purged_count = session_service.purge_retired_sessions(db)

	assert purged_count == 3
	assert calls == [(now, now - timedelta(seconds=3600))]
	assert db.commits == 1
	assert db.rollbacks == 0
