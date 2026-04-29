from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.errors.custom_exceptions import InactiveUserError, InvalidCredentialsError
from shared_backend.schemas.auth.auth_schema import AuthLoginRequestSchema
from shared_backend.schemas.auth.session_schema import AuthLoginResult
from app.utils.auth_utils import (
	generate_session_token,
	hash_secret_token,
	verify_password,
)

from .session_service import resolve_session_ttl_seconds
from .user_read_service import build_authenticated_user_read


def login_user(
	db: Session,
	payload: AuthLoginRequestSchema,
	*,
	commit: bool = True,
) -> AuthLoginResult:
	normalized_email = payload.email.strip().lower()
	user = identity_database_client.get_user_by_email(db, email=normalized_email)
	if user is None or not verify_password(user.password_hash, payload.password):
		raise InvalidCredentialsError()
	if not user.is_active:
		raise InactiveUserError()

	session_token = generate_session_token()
	expires_at = datetime.now(timezone.utc) + timedelta(
		seconds=resolve_session_ttl_seconds()
	)

	try:
		identity_database_client.create_user_session(
			db,
			user_id=user.id,
			token_hash=hash_secret_token(session_token),
			expires_at=expires_at,
		)
		if commit:
			db.commit()
	except Exception:
		if commit:
			db.rollback()
		raise

	return AuthLoginResult(
		session_token=session_token,
		expires_at=expires_at,
		user=build_authenticated_user_read(user),
	)
