from __future__ import annotations

from asyncio import CancelledError
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI

from app.routers.internal_auth_router import internal_auth_router
from app.services.session_maintenance_service import start_session_maintenance_task
from app.clients.database.identity_session_database_client import check_identity_database_ready

from shared_backend.errors.exception_handlers import register_exception_handlers
from shared_backend.security.internal_service_auth import validate_internal_service_token_configuration
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead
from shared_backend.utils.logging_utils import (
	configure_service_logging,
	create_request_logging_middleware,
)


@asynccontextmanager
async def _app_lifespan(_: FastAPI):
	validate_internal_service_token_configuration()
	maintenance_task = start_session_maintenance_task()
	try:
		yield
	finally:
		maintenance_task.cancel()
		with suppress(CancelledError):
			await maintenance_task


def create_app() -> FastAPI:
	configure_service_logging("auth-service")
	app = FastAPI(
		title="Manifeed Auth Service",
		lifespan=_app_lifespan,
	)
	app.middleware("http")(
		create_request_logging_middleware(
			service_name="auth-service",
			route_class="internal-auth",
		)
	)
	app.include_router(internal_auth_router)
	register_exception_handlers(app)

	@app.get("/internal/health", response_model=InternalServiceHealthRead)
	def read_internal_health() -> InternalServiceHealthRead:
		return InternalServiceHealthRead(service="auth-service", status="ok")

	@app.get("/internal/ready", response_model=InternalServiceHealthRead)
	def read_internal_ready() -> InternalServiceHealthRead:
		validate_internal_service_token_configuration()
		check_identity_database_ready()
		return InternalServiceHealthRead(service="auth-service", status="ready")

	return app


app = create_app()
