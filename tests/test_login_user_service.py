from datetime import datetime, timezone

import pytest

from app.schemas.user_context import UserRecord
from app.services import login_user_service

from shared_backend.errors.custom_exceptions import InvalidCredentialsError
from shared_backend.schemas.auth.auth_schema import AuthLoginRequestSchema


class _FakeDb:
	def __init__(self) -> None:
		self.commits = 0
		self.rollbacks = 0

	def commit(self) -> None:
		self.commits += 1

	def rollback(self) -> None:
		self.rollbacks += 1


def test_login_rejects_corrupted_password_hash(monkeypatch) -> None:
	now = datetime.now(timezone.utc)
	user = UserRecord(
		id=1,
		email="user@example.com",
		pseudo="user",
		pp_id=1,
		password_hash="argon2-invalid-hash",
		role="user",
		is_active=True,
		api_access_enabled=False,
		created_at=now,
		updated_at=now,
	)
	monkeypatch.setattr(
		login_user_service.identity_database_client,
		"get_user_by_email",
		lambda db, email: user,
	)

	with pytest.raises(InvalidCredentialsError):
		login_user_service.login_user(
			object(),
			AuthLoginRequestSchema(
				email="user@example.com",
				password="correct horse battery",
			),
		)


def test_login_enforces_active_session_limit(monkeypatch) -> None:
	now = datetime.now(timezone.utc)
	db = _FakeDb()
	user = UserRecord(
		id=1,
		email="user@example.com",
		pseudo="user",
		pp_id=1,
		password_hash="argon2-valid-hash",
		role="user",
		is_active=True,
		api_access_enabled=False,
		created_at=now,
		updated_at=now,
	)
	created_sessions: list[tuple[int, str]] = []
	enforced_limits: list[int] = []
	monkeypatch.setattr(
		login_user_service.identity_database_client,
		"get_user_by_email",
		lambda db, email: user,
	)
	monkeypatch.setattr(login_user_service, "verify_password", lambda password_hash, password: True)
	monkeypatch.setattr(login_user_service, "generate_session_token", lambda: "msess_example")
	monkeypatch.setattr(login_user_service, "resolve_session_ttl_seconds", lambda: 300)
	monkeypatch.setattr(login_user_service, "hash_secret_token", lambda token: "hashed-token")
	monkeypatch.setattr(
		login_user_service.identity_database_client,
		"create_user_session",
		lambda db, user_id, token_hash, expires_at: created_sessions.append((user_id, token_hash)),
	)
	monkeypatch.setattr(
		login_user_service,
		"enforce_user_session_limit",
		lambda db, user_id: enforced_limits.append(user_id),
	)

	result = login_user_service.login_user(
		db,
		AuthLoginRequestSchema(
			email="user@example.com",
			password="correct horse battery",
		),
	)

	assert result.session_token == "msess_example"
	assert created_sessions == [(1, "hashed-token")]
	assert enforced_limits == [1]
	assert db.commits == 1
	assert db.rollbacks == 0
