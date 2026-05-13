from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AuthenticatedUserContext:
	user_id: int
	email: str
	role: str
	is_active: bool
	api_access_enabled: bool
	session_expires_at: datetime


@dataclass(frozen=True)
class UserRecord:
	id: int
	email: str
	pseudo: str
	pp_id: int
	password_hash: str
	role: str
	is_active: bool
	api_access_enabled: bool
	created_at: datetime
	updated_at: datetime


@dataclass(frozen=True)
class UserSessionContextRecord:
	user: UserRecord
	expires_at: datetime
	last_seen_at: datetime | None
