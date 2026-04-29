from datetime import datetime, timedelta, timezone

from app.clients.database.identity_database_client import (
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
	assert db.rollbacks == 1


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
