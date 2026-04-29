from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.clients.database.identity_database_client import UserRecord
from shared_backend.schemas.auth.auth_schema import AuthenticatedUserRead


@dataclass(frozen=True)
class AuthenticatedUserContext:
	user_id: int
	email: str
	role: str
	is_active: bool
	api_access_enabled: bool
	session_expires_at: datetime


def build_authenticated_user_read(user: UserRecord) -> AuthenticatedUserRead:
	return AuthenticatedUserRead(
		id=user.id,
		email=user.email,
		pseudo=user.pseudo,
		pp_id=user.pp_id,
		role=user.role,
		is_active=user.is_active,
		api_access_enabled=user.api_access_enabled,
		created_at=user.created_at,
		updated_at=user.updated_at,
	)
