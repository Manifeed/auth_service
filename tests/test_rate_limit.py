from types import SimpleNamespace

import pytest

from app.errors.custom_exceptions import RateLimitExceededError
from app.middleware import rate_limit


def _request(host: str = "127.0.0.1"):
	return SimpleNamespace(headers={}, client=SimpleNamespace(host=host))


def test_rate_limit_raises_when_redis_required_and_unavailable(monkeypatch) -> None:
	monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
	monkeypatch.setenv("RATE_LIMIT_REDIS_REQUIRED", "true")
	monkeypatch.setattr(rate_limit, "_increment_redis_bucket", lambda key, ttl: None)

	with pytest.raises(RateLimitExceededError):
		rate_limit.enforce_rate_limit(
			_request(),
			namespace="auth-login-ip",
			limit=1,
			window_seconds=60,
		)


def test_rate_limit_uses_memory_fallback_when_redis_optional(monkeypatch) -> None:
	monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
	monkeypatch.setenv("RATE_LIMIT_REDIS_REQUIRED", "false")
	monkeypatch.setattr(rate_limit, "_increment_redis_bucket", lambda key, ttl: None)
	rate_limit._memory_buckets.clear()

	rate_limit.enforce_rate_limit(
		_request(),
		namespace="auth-login-email",
		identifier="User@Example.com",
		limit=1,
		window_seconds=60,
	)

	with pytest.raises(RateLimitExceededError):
		rate_limit.enforce_rate_limit(
			_request(),
			namespace="auth-login-email",
			identifier="user@example.com",
			limit=1,
			window_seconds=60,
		)
