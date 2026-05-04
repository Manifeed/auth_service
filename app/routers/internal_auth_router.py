from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.services.login_user_service import login_user
from app.services.register_user_service import register_user
from app.clients.database.identity_session_database_client import get_identity_db_session
from app.services.session_service import (
	logout_session_token,
	read_current_session_by_token,
	resolve_session_token,
)

from shared_backend.security.internal_service_auth import require_internal_service_token
from shared_backend.schemas.internal.service_schema import InternalResolvedSessionRead
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


internal_auth_router = APIRouter(
	prefix="/internal/auth",
	tags=["internal-auth"],
	dependencies=[Depends(require_internal_service_token)],
)


@internal_auth_router.post("/register", response_model=AuthRegisterRead)
def register_internal_auth_user(
	payload: Annotated[AuthRegisterRequestSchema, Body(embed=True)],
	db: Session = Depends(get_identity_db_session),
) -> AuthRegisterRead:
	return register_user(db, payload)


@internal_auth_router.post("/login", response_model=InternalAuthLoginRead)
def login_internal_auth_user(
	payload: Annotated[AuthLoginRequestSchema, Body(embed=True)],
	db: Session = Depends(get_identity_db_session),
) -> InternalAuthLoginRead:
	result = login_user(db, payload)
	return InternalAuthLoginRead(
		session_token=result.session_token,
		expires_at=result.expires_at,
		user=result.user,
	)


@internal_auth_router.post("/session", response_model=AuthSessionRead)
def read_internal_auth_session(
	payload: Annotated[InternalSessionTokenRequest, Body(embed=True)],
	db: Session = Depends(get_identity_db_session),
) -> AuthSessionRead:
	return read_current_session_by_token(db, session_token=payload.session_token)


@internal_auth_router.post("/resolve-session", response_model=InternalResolvedSessionRead)
def resolve_internal_auth_session(
	payload: Annotated[InternalSessionTokenRequest, Body(embed=True)],
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
	payload: Annotated[InternalSessionTokenRequest, Body(embed=True)],
	db: Session = Depends(get_identity_db_session),
) -> AuthLogoutRead:
	return logout_session_token(db, session_token=payload.session_token)
