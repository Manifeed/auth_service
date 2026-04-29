from __future__ import annotations

from fastapi import FastAPI

from app.clients.database.identity_session_database_client import (
	check_identity_database_ready,
)
from app.errors.exception_handlers import register_exception_handlers
from app.routers.internal_auth_router import internal_auth_router
from app.security import validate_internal_service_token_configuration

from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead


app = FastAPI(title="Manifeed Auth Service")
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
