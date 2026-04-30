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
- Internal token gate (`x-manifeed-internal-token`) on all auth routes
- Per-IP and per-email rate limiting for registration and login
- Health and readiness probes for orchestration

## Architecture Overview

- `app/routers`: HTTP route layer (`/internal/auth/*`)
- `app/services`: auth business use cases
- `app/clients/database`: SQLAlchemy session and SQL access layer
- `app/clients/networking`: Redis networking client for rate limiting
- `shared_backend.security.internal_service_auth`: shared inter-service token validation helpers
- `app/middleware/rate_limit.py`: reusable rate limiting enforcement

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

Optional Redis for distributed rate limiting:

```bash
export REDIS_URL=redis://localhost:6379/0
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

## Security Model

- All `/internal/auth/*` routes require `x-manifeed-internal-token`
  except in explicit local/test environments without configured token.
- Session tokens are generated as random secrets and only their SHA-256 hash
  is persisted in `user_sessions`.
- Password hashing and verification are delegated to shared backend auth
  utilities (Argon2-based).
- Login and registration are protected by rate limiting (IP + email buckets).

## Configuration

### Core runtime

- `APP_ENV` / `ENVIRONMENT`: environment mode resolver
- `IDENTITY_DATABASE_URL`: identity Postgres DSN
- `REQUIRE_EXPLICIT_DATABASE_URLS`: requires explicit DB URL in strict envs
- `INTERNAL_SERVICE_TOKEN`: shared secret for internal route protection
- `REQUIRE_INTERNAL_SERVICE_TOKEN`: force strict internal token mode

### Session behavior

- `AUTH_SESSION_TTL_SECONDS`: default session lifetime (`604800`)
- `AUTH_SESSION_TOUCH_INTERVAL_SECONDS`: minimum interval between
  `last_seen_at` updates (`300`)

### Rate limiting

- `RATE_LIMIT_ENABLED`: global rate limiting switch
- `RATE_LIMIT_REDIS_REQUIRED`: fail-closed when Redis is unavailable
- `REDIS_URL`: Redis connection URL
- `REDIS_SOCKET_TIMEOUT_SECONDS`: Redis socket timeout (`0.2`)

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
- Internal token behavior (local vs strict environments)
- Rate limit Redis-required and memory fallback behavior
- Session touch strategy (`last_seen_at` update policy)

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
`shared_backend` from a wheel built locally from the monorepo.

## Detailed Documentation

Documentation is available in:

- `doc/README.md`
