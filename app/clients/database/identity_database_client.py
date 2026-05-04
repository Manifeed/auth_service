from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.user_context import UserRecord, UserSessionContextRecord

from shared_backend.utils.datetime_utils import normalize_datetime_to_utc


def create_user(
	db: Session,
	*,
	email: str,
	pseudo: str,
	pp_id: int,
	password_hash: str,
	role: str,
	is_active: bool,
	api_access_enabled: bool,
) -> UserRecord:
	row = (
		db.execute(
			text(
				"""
				INSERT INTO users (
					email,
					pseudo,
					pp_id,
					password_hash,
					role,
					is_active,
					api_access_enabled
				) VALUES (
					:email,
					:pseudo,
					:pp_id,
					:password_hash,
					:role,
					:is_active,
					:api_access_enabled
				)
				RETURNING
					id,
					email,
					pseudo,
					pp_id,
					password_hash,
					role,
					is_active,
					api_access_enabled,
					created_at,
					updated_at
				"""
			),
			{
				"email": email,
				"pseudo": pseudo,
				"pp_id": pp_id,
				"password_hash": password_hash,
				"role": role,
				"is_active": is_active,
				"api_access_enabled": api_access_enabled,
			},
		)
		.mappings()
		.one()
	)
	return _map_user(row)


def get_user_by_email(db: Session, *, email: str) -> UserRecord | None:
	row = (
		db.execute(
			text(
				"""
				SELECT
					id,
					email,
					pseudo,
					pp_id,
					password_hash,
					role,
					is_active,
					api_access_enabled,
					created_at,
					updated_at
				FROM users
				WHERE email = :email
				"""
			),
			{"email": email},
		)
		.mappings()
		.one_or_none()
	)
	if row is None:
		return None
	return _map_user(row)


def get_user_by_id(db: Session, *, user_id: int) -> UserRecord | None:
	row = (
		db.execute(
			text(
				"""
				SELECT
					id,
					email,
					pseudo,
					pp_id,
					password_hash,
					role,
					is_active,
					api_access_enabled,
					created_at,
					updated_at
				FROM users
				WHERE id = :user_id
				"""
			),
			{"user_id": user_id},
		)
		.mappings()
		.one_or_none()
	)
	if row is None:
		return None
	return _map_user(row)


def create_user_session(
	db: Session,
	*,
	user_id: int,
	token_hash: str,
	expires_at: datetime,
) -> datetime:
	return db.execute(
		text(
			"""
			INSERT INTO user_sessions (
				user_id,
				token_hash,
				expires_at
			) VALUES (
				:user_id,
				:token_hash,
				:expires_at
			)
			RETURNING expires_at
			"""
		),
		{
			"user_id": user_id,
			"token_hash": token_hash,
			"expires_at": normalize_datetime_to_utc(expires_at),
		},
	).scalar_one()


def get_user_session_context_by_token_hash(
	db: Session,
	*,
	token_hash: str,
) -> UserSessionContextRecord | None:
	row = (
		db.execute(
			text(
				"""
				SELECT
					users.id,
					users.email,
					users.pseudo,
					users.pp_id,
					users.password_hash,
					users.role,
					users.is_active,
					users.api_access_enabled,
					users.created_at,
					users.updated_at,
					sessions.expires_at,
					sessions.last_seen_at
				FROM user_sessions AS sessions
				JOIN users
					ON users.id = sessions.user_id
				WHERE sessions.token_hash = :token_hash
					AND sessions.revoked_at IS NULL
				"""
			),
			{"token_hash": token_hash},
		)
		.mappings()
		.one_or_none()
	)
	if row is None:
		return None
	return UserSessionContextRecord(
		user=_map_user(row),
		expires_at=normalize_datetime_to_utc(row["expires_at"]) or datetime.now(timezone.utc),
		last_seen_at=normalize_datetime_to_utc(row["last_seen_at"]),
	)


def touch_user_session(db: Session, *, token_hash: str) -> None:
	db.execute(
		text(
			"""
			UPDATE user_sessions
			SET last_seen_at = now()
			WHERE token_hash = :token_hash
				AND revoked_at IS NULL
			"""
		),
		{"token_hash": token_hash},
	)


def revoke_user_session_by_token_hash(db: Session, *, token_hash: str) -> None:
	db.execute(
		text(
			"""
			UPDATE user_sessions
			SET revoked_at = now()
			WHERE token_hash = :token_hash
				AND revoked_at IS NULL
			"""
		),
		{"token_hash": token_hash},
	)


def revoke_excess_active_user_sessions(
	db: Session,
	*,
	user_id: int,
	keep_limit: int,
	now: datetime | None = None,
) -> int:
	rows = db.execute(
		text(
			"""
			WITH ranked_sessions AS (
				SELECT id
				FROM user_sessions
				WHERE user_id = :user_id
					AND revoked_at IS NULL
					AND expires_at > :now
				ORDER BY
					COALESCE(last_seen_at, created_at) DESC,
					created_at DESC,
					id DESC
				OFFSET :keep_limit
			)
			UPDATE user_sessions
			SET revoked_at = now()
			WHERE id IN (SELECT id FROM ranked_sessions)
				AND revoked_at IS NULL
			RETURNING id
			"""
		),
		{
			"user_id": user_id,
			"keep_limit": keep_limit,
			"now": normalize_datetime_to_utc(now) or datetime.now(timezone.utc),
		},
	).all()
	return len(rows)


def purge_retired_user_sessions(
	db: Session,
	*,
	expired_before: datetime,
	revoked_before: datetime,
) -> int:
	rows = db.execute(
		text(
			"""
			DELETE FROM user_sessions
			WHERE expires_at <= :expired_before
				OR (
					revoked_at IS NOT NULL
					AND revoked_at <= :revoked_before
				)
			RETURNING id
			"""
		),
		{
			"expired_before": normalize_datetime_to_utc(expired_before) or datetime.now(timezone.utc),
			"revoked_before": normalize_datetime_to_utc(revoked_before) or datetime.now(timezone.utc),
		},
	).all()
	return len(rows)


def _map_user(row: Mapping[str, Any]) -> UserRecord:
	return UserRecord(
		id=int(row["id"]),
		email=str(row["email"]),
		pseudo=str(row["pseudo"]),
		pp_id=int(row["pp_id"]),
		password_hash=str(row["password_hash"]),
		role=str(row["role"]),
		is_active=bool(row["is_active"]),
		api_access_enabled=bool(row["api_access_enabled"]),
		created_at=normalize_datetime_to_utc(row["created_at"]) or datetime.now(timezone.utc),
		updated_at=normalize_datetime_to_utc(row["updated_at"]) or datetime.now(timezone.utc),
	)
