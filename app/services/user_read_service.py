from __future__ import annotations

from app.schemas.user_context import UserRecord

from shared_backend.schemas.auth.auth_schema import AuthenticatedUserRead


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
