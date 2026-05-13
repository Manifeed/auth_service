from __future__ import annotations

import asyncio
import logging

from app.clients.database.identity_session_database_client import IdentitySessionLocal
from app.services.session_service import (
	purge_retired_sessions,
	resolve_session_purge_interval_seconds,
)


logger = logging.getLogger(__name__)


def run_session_maintenance_cycle(session_factory=IdentitySessionLocal) -> int:
	with session_factory() as db:
		return purge_retired_sessions(db)


async def run_session_maintenance_loop() -> None:
	while True:
		try:
			purged_count = run_session_maintenance_cycle()
			if purged_count:
				logger.info(
					"Session maintenance purged %s retired sessions",
					purged_count,
				)
		except asyncio.CancelledError:
			raise
		except Exception:
			logger.exception("Session maintenance cycle failed")
		await asyncio.sleep(resolve_session_purge_interval_seconds())


def start_session_maintenance_task() -> asyncio.Task[None]:
	return asyncio.create_task(
		run_session_maintenance_loop(),
		name="auth-service-session-maintenance",
	)
