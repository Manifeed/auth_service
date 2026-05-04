# API Reference

## General Contract

- `GET /internal/health` and `GET /internal/ready` are probe endpoints and do not require the internal auth header
- All `/internal/auth/*` routes require `x-manifeed-internal-token`
- All `POST /internal/auth/*` request bodies are wrapped under `payload`
- Validation failures return HTTP `422` with shared `validation_error` payloads
- Domain errors return shared JSON payloads with stable `code` and `message` fields

## Health Endpoints

### `GET /internal/health`

Liveness endpoint.

Response:

```json
{
	"service": "auth-service",
	"status": "ok"
}
```

### `GET /internal/ready`

Readiness endpoint.

Validates:

- internal token configuration
- identity database connectivity (`SELECT 1`)

Response:

```json
{
	"service": "auth-service",
	"status": "ready"
}
```

This route does not authenticate the caller, but it fails if strict internal
token configuration is invalid.

## Auth Endpoints

All auth endpoints are under `/internal/auth` and require internal token
authorization.

### `POST /internal/auth/register`

Creates a new active user with role `user`.

Request:

```json
{
	"payload": {
		"email": "user@example.com",
		"pseudo": "user",
		"password": "correct horse battery"
	}
}
```

Behavior:

- normalizes email and pseudo
- validates password policy
- rejects duplicate users
- stores password hash only
- returns HTTP `200`
- common error codes: `duplicate_user_registration`, `invalid_pseudo`, `weak_password`

### `POST /internal/auth/login`

Authenticates user and creates a session.

Request:

```json
{
	"payload": {
		"email": "user@example.com",
		"password": "correct horse battery"
	}
}
```

Behavior:

- verifies normalized credentials
- rejects inactive users
- creates session row with expiration
- revokes older active sessions beyond configured per-user cap
- returns clear session token
- returns HTTP `200`
- common error codes: `invalid_credentials`, `inactive_user`

### `POST /internal/auth/session`

Resolves token and returns session + user projection.

Request:

```json
{
	"payload": {
		"session_token": "msess_example"
	}
}
```

Common error codes: `missing_session_token`, `invalid_session_token`,
`expired_session_token`, `inactive_user`, `user_not_found`.

### `POST /internal/auth/resolve-session`

Resolves token and returns internal session context:

- `user_id`
- `email`
- `role`
- `is_active`
- `api_access_enabled`
- `session_expires_at`

Request:

```json
{
	"payload": {
		"session_token": "msess_example"
	}
}
```

### `POST /internal/auth/logout`

Revokes session by token hash.

Request:

```json
{
	"payload": {
		"session_token": "msess_example"
	}
}
```

Response:

```json
{
	"ok": true
}
```

Logout is idempotent.

## Runtime Flows

### Registration Flow

1. validate internal token
2. normalize and validate input
3. create user
4. return user projection

### Login Flow

1. validate internal token
2. verify credentials
3. generate session token
4. store token hash + expiration
5. revoke older active sessions beyond configured cap
6. return token and user payload

### Session Resolution Flow

1. verify token presence
2. hash token
3. read active non-revoked session
4. validate expiry and user state
5. optionally touch `last_seen_at`
6. return authenticated context

## Current Assumptions

- Upstream layers own rate limiting for login and registration
- Session cleanup runs in-process on a background cadence
