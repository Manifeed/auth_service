# Architecture

## High-Level Layers

- `app/services/routers`: HTTP route definitions and request entry points
- `app/services`: core authentication business logic
- `app/clients/database`: DB session and SQL access
- `shared_backend.security.internal_service_auth`: inter-service token validation
- `shared_backend.errors.exception_handlers`: shared exception-to-JSON mapping
- `shared_backend.utils.logging_utils`: shared request logging middleware

## Route Layer

Main router:

- `app/services/routers/internal_auth_router.py`
- Prefix: `/internal/auth`
- Protected by `require_internal_service_token`
- All POST request bodies are embedded under `payload`

Application bootstrap:

- `app/main.py`
- configures request logging middleware
- starts a background session maintenance task
- registers shared exception handlers
- exposes `/internal/health` and `/internal/ready`

## Business Layer

Core services:

- `register_user_service.py`
- `login_user_service.py`
- `session_service.py`
- `session_maintenance_service.py`

These services normalize inputs, validate constraints, execute domain rules,
and return response schemas. Edge/gateway rate limiting is intentionally kept
out of this service.

## Persistence Layer

Database session and readiness:

- `identity_session_database_client.py`
- creates the SQLAlchemy engine and session factory at import time
- validates DB connectivity for readiness with `SELECT 1`

Identity and session SQL operations:

- `identity_database_client.py`
- keeps raw SQL queries and lightweight dataclass projections

## Error and Schema Strategy

- Exceptions and handlers come from shared backend modules
- API contracts use shared backend schema definitions
- This keeps cross-service behavior and payloads consistent
