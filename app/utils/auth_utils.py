from __future__ import annotations

import secrets

SESSION_TOKEN_BYTES = 32
SESSION_TOKEN_PREFIX = "msess"  # nosec


def generate_session_token() -> str:
	return f"{SESSION_TOKEN_PREFIX}_{secrets.token_urlsafe(SESSION_TOKEN_BYTES)}"
