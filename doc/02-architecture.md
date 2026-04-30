# Architecture

## High-Level Layers

- `app/routers`: HTTP route definitions and request entry points
- `app/services`: core authentication business logic
- `app/clients/database`: DB session and SQL access
- `app/clients/networking`: Redis communication for rate limiting
- `shared_backend.security.internal_service_auth`: inter-service token validation
- `app/middleware/rate_limit.py`: reusable rate limiting policy

## Route Layer

Main router:

- `app/routers/internal_auth_router.py`
- Prefix: `/internal/auth`
- Protected by `require_internal_service_token`

## Business Layer

Core services:

- `register_user_service.py`
- `login_user_service.py`
- `session_service.py`

These services normalize inputs, validate constraints, execute domain rules,
and return response schemas.

## Persistence Layer

Database session and readiness:

- `identity_session_database_client.py`

Identity and session SQL operations:

- `identity_database_client.py`

## Error and Schema Strategy

- Exceptions and handlers come from shared backend modules
- API contracts use shared backend schema definitions
- This keeps cross-service behavior and payloads consistent
