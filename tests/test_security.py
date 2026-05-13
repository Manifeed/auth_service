from types import SimpleNamespace

import pytest

from shared_backend.errors.custom_exceptions import InternalServiceAuthError
from shared_backend.security.internal_service_auth import INTERNAL_SERVICE_TOKEN_HEADER, require_internal_service_token


def _request(token: str | None = None):
	headers = {}
	if token is not None:
		headers[INTERNAL_SERVICE_TOKEN_HEADER] = token
	return SimpleNamespace(headers=headers)


def test_internal_token_is_required_in_all_environments(monkeypatch) -> None:
	for app_env in ("local", "production"):
		monkeypatch.setenv("APP_ENV", app_env)
		monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)
		monkeypatch.delenv("INTERNAL_SERVICE_TOKENS", raising=False)

		with pytest.raises(InternalServiceAuthError):
			require_internal_service_token(_request())


def test_internal_token_matches_constant_time_secret(monkeypatch) -> None:
	token = "a" * 32
	monkeypatch.setenv("APP_ENV", "production")
	monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", token)

	require_internal_service_token(_request(token))


def test_internal_token_matches_any_configured_secret(monkeypatch) -> None:
	monkeypatch.setenv("APP_ENV", "production")
	monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)
	monkeypatch.setenv("INTERNAL_SERVICE_TOKENS", f"{'a' * 32},{'b' * 32}")

	require_internal_service_token(_request("b" * 32))
