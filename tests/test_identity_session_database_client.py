import importlib

from app.clients.database import identity_session_database_client as database_client


def test_identity_database_access_uses_explicit_read_and_write_urls(monkeypatch) -> None:
	monkeypatch.setenv("APP_ENV", "local")
	monkeypatch.setenv(
		"IDENTITY_READ_DATABASE_URL",
		"postgresql://manifeed:manifeed@localhost:5432/manifeed_identity_read",
	)
	monkeypatch.setenv(
		"IDENTITY_WRITE_DATABASE_URL",
		"postgresql://manifeed:manifeed@localhost:5432/manifeed_identity_write",
	)

	module = importlib.reload(database_client)

	assert module.IDENTITY_READ_DATABASE_URL.endswith("/manifeed_identity_read")
	assert module.IDENTITY_WRITE_DATABASE_URL.endswith("/manifeed_identity_write")


def test_identity_database_access_falls_back_to_legacy_url(monkeypatch) -> None:
	monkeypatch.setenv("APP_ENV", "local")
	monkeypatch.setenv(
		"IDENTITY_DATABASE_URL",
		"postgresql://manifeed:manifeed@localhost:5432/manifeed_identity_legacy",
	)
	monkeypatch.delenv("IDENTITY_READ_DATABASE_URL", raising=False)
	monkeypatch.delenv("IDENTITY_WRITE_DATABASE_URL", raising=False)

	module = importlib.reload(database_client)

	assert module.IDENTITY_READ_DATABASE_URL.endswith("/manifeed_identity_legacy")
	assert module.IDENTITY_WRITE_DATABASE_URL.endswith("/manifeed_identity_legacy")
