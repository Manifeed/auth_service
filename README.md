# Manifeed Auth Service

`auth_service` is the internal identity and session service for Manifeed.
It exposes internal FastAPI endpoints for user registration, login, session
resolution, and logout. It is designed to be consumed by trusted backend
services, not by browsers or public clients directly.

## What This Service Provides

- User registration with password policy validation
- User login with secure password verification
- Session token issuance and hashed session storage
- Session resolution for inter-service authentication flows
- Idempotent logout (session revocation)
- Active session cap and periodic session cleanup
- Internal token gate (`x-manifeed-internal-token`) on all auth routes
- Health and readiness probes for orchestration

## Architecture Overview

- `app/services/routers`: HTTP route layer (`/internal/auth/*`)
- `app/services`: auth business use cases
- `app/clients/database`: SQLAlchemy session and SQL access layer
- `shared_backend.security.internal_service_auth`: shared inter-service token validation helpers
- `shared_backend.errors.exception_handlers`: shared JSON error mapping
- `shared_backend.utils.logging_utils`: shared request logging middleware

## Quick Start (Local Development)

### 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) Set minimal local environment

```bash
export APP_ENV=local
export IDENTITY_DATABASE_URL=postgresql://manifeed:manifeed@localhost:5432/manifeed_identity
```

### 3) Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Service endpoints:

- `GET /internal/health`
- `GET /internal/ready`
- `POST /internal/auth/register`
- `POST /internal/auth/login`
- `POST /internal/auth/session`
- `POST /internal/auth/resolve-session`
- `POST /internal/auth/logout`

All `POST /internal/auth/*` endpoints expect a JSON body wrapped under
`payload`, for example:

```json
{
  "payload": {
    "session_token": "msess_example"
  }
}
```

## Security Model

- All `/internal/auth/*` routes require `x-manifeed-internal-token`.
- Startup fails if no strong internal token is configured.
- Incoming auth can validate either one `INTERNAL_SERVICE_TOKEN` or multiple
  accepted secrets via `INTERNAL_SERVICE_TOKENS`.
- `/internal/health` and `/internal/ready` stay unauthenticated for probes;
  `/internal/ready` still validates token configuration.
- Session tokens are generated as random secrets and only their SHA-256 hash
  is persisted in `user_sessions`.
- Active sessions are capped per user and older sessions are revoked on login.
- Expired sessions are purged periodically; revoked sessions are retained for
  a bounded window before deletion.
- Password hashing and verification are delegated to shared backend auth
  utilities (Argon2-based).
- Login and registration rely on edge/gateway rate limiting; `auth_service`
  itself stays focused on identity and session rules.

## Configuration

### Core runtime

- `APP_ENV` / `ENVIRONMENT`: environment mode resolver
- `IDENTITY_DATABASE_URL`: identity Postgres DSN
- `REQUIRE_EXPLICIT_DATABASE_URLS`: requires explicit DB URL in strict envs
- `INTERNAL_SERVICE_TOKEN`: shared secret for internal route protection
- `INTERNAL_SERVICE_TOKENS`: optional comma-separated accepted ingress tokens

### Session behavior

- `AUTH_SESSION_TTL_SECONDS`: default session lifetime (`604800`)
- `AUTH_SESSION_TOUCH_INTERVAL_SECONDS`: minimum interval between
  `last_seen_at` updates (`300`)
- `AUTH_MAX_ACTIVE_SESSIONS_PER_USER`: active session cap per user (`5`)
- `AUTH_SESSION_PURGE_INTERVAL_SECONDS`: background purge cadence (`900`)
- `AUTH_SESSION_REVOKED_RETENTION_SECONDS`: retention for revoked sessions
  before deletion (`86400`)

### DB pool tuning

- `DB_POOL_SIZE`: SQLAlchemy pool size (`5`)
- `DB_MAX_OVERFLOW`: SQLAlchemy max overflow (`10`)
- `DB_POOL_TIMEOUT_SECONDS`: pool checkout timeout (`30`)
- `DB_POOL_RECYCLE_SECONDS`: pool recycle interval (`1800`)

## Tests

Run the test suite:

```bash
pytest -q
```

Current tests cover:

- Source syntax validity
- Internal token behavior and strong-token requirements
- Wrapped `payload` request contract on internal auth routes
- Invalid DB pool configuration fallback behavior
- Corrupted password hash rejection during login
- Session touch strategy (`last_seen_at` update policy)
- Active session cap enforcement on login
- Periodic session maintenance entrypoint

Current gaps before strong production confidence:

- No DB integration tests for `register -> login -> resolve -> logout`

## Docker

Build:

```bash
docker build -t manifeed-auth-service -f auth_service/Dockerfile ..
```

Run:

```bash
docker run --rm -p 8000:8000 \
	-e APP_ENV=production \
	-e IDENTITY_DATABASE_URL='postgresql://user:pass@host:5432/db' \
	-e INTERNAL_SERVICE_TOKEN='replace-with-strong-secret-min-32-chars' \
	manifeed-auth-service
```

The image is multi-stage, runs as a non-root user, and installs
`shared_backend` from a wheel built locally from the monorepo. The runtime
base image is `python:3.13-slim`.

## Detailed Documentation

Documentation is available in:

- `doc/README.md`
