from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.errors.custom_exceptions import (
	DuplicateUserRegistrationError,
	InvalidPseudoError,
)
from shared_backend.domain.password_policy import validate_password_policy
from shared_backend.domain.user_identity import normalize_user_pseudo
from shared_backend.schemas.auth.auth_schema import AuthRegisterRead, AuthRegisterRequestSchema
from app.utils.auth_utils import hash_password

from .user_read_service import build_authenticated_user_read


def register_user(
	db: Session,
	payload: AuthRegisterRequestSchema,
	*,
	commit: bool = True,
) -> AuthRegisterRead:
	normalized_email = _normalize_email(payload.email)
	normalized_pseudo = _normalize_pseudo(payload.pseudo)
	validate_password_policy(payload.password)
	if identity_database_client.get_user_by_email(db, email=normalized_email) is not None:
		raise DuplicateUserRegistrationError()

	try:
		user = identity_database_client.create_user(
			db,
			email=normalized_email,
			pseudo=normalized_pseudo,
			pp_id=1,
			password_hash=hash_password(payload.password),
			role="user",
			is_active=True,
			api_access_enabled=False,
		)
		if commit:
			db.commit()
	except IntegrityError as exception:
		if commit:
			db.rollback()
		raise DuplicateUserRegistrationError() from exception
	except Exception:
		if commit:
			db.rollback()
		raise

	return AuthRegisterRead(user=build_authenticated_user_read(user))


def _normalize_email(email: str) -> str:
	return email.strip().lower()


def _normalize_pseudo(pseudo: str) -> str:
	normalized = normalize_user_pseudo(pseudo)
	if not normalized:
		raise InvalidPseudoError()
	return normalized
