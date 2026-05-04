from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.internal_auth_router as router_module

from app.schemas.user_context import AuthenticatedUserContext
from shared_backend.schemas.auth.auth_schema import (
	AuthenticatedUserRead,
	AuthLogoutRead,
	AuthRegisterRead,
	AuthSessionRead,
)
from shared_backend.schemas.auth.session_schema import AuthLoginResult


def _user_read() -> AuthenticatedUserRead:
	now = datetime.now(timezone.utc)
	return AuthenticatedUserRead(
		id=1,
		email="user@example.com",
		pseudo="user",
		pp_id=1,
		role="user",
		is_active=True,
		api_access_enabled=False,
		created_at=now,
		updated_at=now,
	)


def _build_client(monkeypatch) -> TestClient:
	app = FastAPI()
	app.include_router(router_module.internal_auth_router)
	app.dependency_overrides[router_module.require_internal_service_token] = lambda: None
	app.dependency_overrides[router_module.get_identity_db_session] = lambda: object()

	user = _user_read()
	monkeypatch.setattr(
		router_module,
		"register_user",
		lambda db, payload: AuthRegisterRead(user=user),
	)
	monkeypatch.setattr(
		router_module,
		"login_user",
		lambda db, payload: AuthLoginResult(
			session_token="msess_example",
			expires_at=user.updated_at,
			user=user,
		),
	)
	monkeypatch.setattr(
		router_module,
		"read_current_session_by_token",
		lambda db, session_token: AuthSessionRead(
			expires_at=user.updated_at,
			user=user,
		),
	)
	monkeypatch.setattr(
		router_module,
		"resolve_session_token",
		lambda db, session_token: AuthenticatedUserContext(
			user_id=user.id,
			email=user.email,
			role=user.role,
			is_active=user.is_active,
			api_access_enabled=user.api_access_enabled,
			session_expires_at=user.updated_at,
		),
	)
	monkeypatch.setattr(
		router_module,
		"logout_session_token",
		lambda db, session_token: AuthLogoutRead(ok=True),
	)
	return TestClient(app)


def test_internal_auth_routes_reject_flat_json_bodies(monkeypatch) -> None:
	client = _build_client(monkeypatch)

	requests = [
		("/internal/auth/register", {"email": "user@example.com", "pseudo": "user", "password": "correct horse battery"}),
		("/internal/auth/login", {"email": "user@example.com", "password": "correct horse battery"}),
		("/internal/auth/session", {"session_token": "msess_example"}),
		("/internal/auth/resolve-session", {"session_token": "msess_example"}),
		("/internal/auth/logout", {"session_token": "msess_example"}),
	]

	for path, body in requests:
		response = client.post(path, json=body)
		assert response.status_code == 422, path


def test_internal_auth_routes_accept_wrapped_json_bodies(monkeypatch) -> None:
	client = _build_client(monkeypatch)

	requests = [
		("/internal/auth/register", {"payload": {"email": "user@example.com", "pseudo": "user", "password": "correct horse battery"}}),
		("/internal/auth/login", {"payload": {"email": "user@example.com", "password": "correct horse battery"}}),
		("/internal/auth/session", {"payload": {"session_token": "msess_example"}}),
		("/internal/auth/resolve-session", {"payload": {"session_token": "msess_example"}}),
		("/internal/auth/logout", {"payload": {"session_token": "msess_example"}}),
	]

	for path, body in requests:
		response = client.post(path, json=body)
		assert response.status_code == 200, path
