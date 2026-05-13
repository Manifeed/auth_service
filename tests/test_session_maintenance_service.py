from app.services import session_maintenance_service


class _FakeSession:
	pass


class _FakeSessionContext:
	def __init__(self, db) -> None:
		self._db = db

	def __enter__(self):
		return self._db

	def __exit__(self, exc_type, exc, tb) -> None:
		return None


def test_run_session_maintenance_cycle_uses_session_factory(monkeypatch) -> None:
	db = _FakeSession()
	calls = []
	monkeypatch.setattr(
		session_maintenance_service,
		"purge_retired_sessions",
		lambda received_db: calls.append(received_db) or 4,
	)

	purged_count = session_maintenance_service.run_session_maintenance_cycle(
		session_factory=lambda: _FakeSessionContext(db),
	)

	assert purged_count == 4
	assert calls == [db]
