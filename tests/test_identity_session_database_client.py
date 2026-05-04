import importlib

from app.clients.database import identity_session_database_client as database_client


def test_invalid_db_pool_values_fallback_to_defaults(monkeypatch) -> None:
	monkeypatch.setenv("APP_ENV", "local")
	monkeypatch.delenv("REQUIRE_EXPLICIT_DATABASE_URLS", raising=False)
	monkeypatch.delenv("IDENTITY_DATABASE_URL", raising=False)
	monkeypatch.setenv("DB_POOL_SIZE", "not-a-number")
	monkeypatch.setenv("DB_MAX_OVERFLOW", "-1")
	monkeypatch.setenv("DB_POOL_TIMEOUT_SECONDS", "0")
	monkeypatch.setenv("DB_POOL_RECYCLE_SECONDS", "")

	module = importlib.reload(database_client)

	assert module.DB_POOL_SIZE == module.DEFAULT_DB_POOL_SIZE
	assert module.DB_MAX_OVERFLOW == module.DEFAULT_DB_MAX_OVERFLOW
	assert module.DB_POOL_TIMEOUT_SECONDS == module.DEFAULT_DB_POOL_TIMEOUT_SECONDS
	assert module.DB_POOL_RECYCLE_SECONDS == module.DEFAULT_DB_POOL_RECYCLE_SECONDS


def test_valid_db_pool_values_are_preserved(monkeypatch) -> None:
	monkeypatch.setenv("APP_ENV", "local")
	monkeypatch.delenv("REQUIRE_EXPLICIT_DATABASE_URLS", raising=False)
	monkeypatch.delenv("IDENTITY_DATABASE_URL", raising=False)
	monkeypatch.setenv("DB_POOL_SIZE", "8")
	monkeypatch.setenv("DB_MAX_OVERFLOW", "12")
	monkeypatch.setenv("DB_POOL_TIMEOUT_SECONDS", "45")
	monkeypatch.setenv("DB_POOL_RECYCLE_SECONDS", "900")

	module = importlib.reload(database_client)

	assert module.DB_POOL_SIZE == 8
	assert module.DB_MAX_OVERFLOW == 12
	assert module.DB_POOL_TIMEOUT_SECONDS == 45
	assert module.DB_POOL_RECYCLE_SECONDS == 900
