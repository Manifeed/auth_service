from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.middleware.rate_limit import enforce_rate_limit
from app.services.login_user_service import login_user
from app.services.register_user_service import register_user
from app.services.session_service import (
	logout_session_token,
	read_current_session_by_token,
	resolve_session_token,
)
from app.security import require_internal_service_token
from app.clients.database.identity_session_database_client import get_identity_db_session


from shared_backend.schemas.auth.auth_schema import (
	AuthLoginRequestSchema,
	AuthLogoutRead,
	AuthRegisterRead,
	AuthRegisterRequestSchema,
	AuthSessionRead,
)
from shared_backend.schemas.internal.auth_service_schema import (
	InternalAuthLoginRead,
	InternalSessionTokenRequest,
)
from shared_backend.schemas.internal.service_schema import InternalResolvedSessionRead


internal_auth_router = APIRouter(
	prefix="/internal/auth",
	tags=["internal-auth"],
	dependencies=[Depends(require_internal_service_token)],
)


@internal_auth_router.post("/register", response_model=AuthRegisterRead)
def register_internal_auth_user(
	request: Request,
	payload: AuthRegisterRequestSchema,
	db: Session = Depends(get_identity_db_session),
) -> AuthRegisterRead:
	enforce_rate_limit(
		request,
		namespace="auth-register-ip",
		limit=10,
		window_seconds=3600,
	)
	enforce_rate_limit(
		request,
		namespace="auth-register-email",
		identifier=payload.email.strip().lower(),
		limit=5,
		window_seconds=3600,
	)
	return register_user(db, payload)


@internal_auth_router.post("/login", response_model=InternalAuthLoginRead)
def login_internal_auth_user(
	request: Request,
	payload: AuthLoginRequestSchema,
	db: Session = Depends(get_identity_db_session),
) -> InternalAuthLoginRead:
	enforce_rate_limit(
		request,
		namespace="auth-login-ip",
		limit=30,
		window_seconds=300,
	)
	enforce_rate_limit(
		request,
		namespace="auth-login-email",
		identifier=payload.email.strip().lower(),
		limit=10,
		window_seconds=300,
	)
	result = login_user(db, payload)
	return InternalAuthLoginRead(
		session_token=result.session_token,
		expires_at=result.expires_at,
		user=result.user,
	)


@internal_auth_router.post("/session", response_model=AuthSessionRead)
def read_internal_auth_session(
	payload: InternalSessionTokenRequest,
	db: Session = Depends(get_identity_db_session),
) -> AuthSessionRead:
	return read_current_session_by_token(db, session_token=payload.session_token)


@internal_auth_router.post("/resolve-session", response_model=InternalResolvedSessionRead)
def resolve_internal_auth_session(
	payload: InternalSessionTokenRequest,
	db: Session = Depends(get_identity_db_session),
) -> InternalResolvedSessionRead:
	current_user = resolve_session_token(db, session_token=payload.session_token)
	return InternalResolvedSessionRead(
		user_id=current_user.user_id,
		email=current_user.email,
		role=current_user.role,
		is_active=current_user.is_active,
		api_access_enabled=current_user.api_access_enabled,
		session_expires_at=current_user.session_expires_at,
	)


@internal_auth_router.post("/logout", response_model=AuthLogoutRead)
def logout_internal_auth_user(
	payload: InternalSessionTokenRequest,
	db: Session = Depends(get_identity_db_session),
) -> AuthLogoutRead:
	return logout_session_token(db, session_token=payload.session_token)
