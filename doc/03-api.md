# API Reference

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

## Auth Endpoints

All auth endpoints are under `/internal/auth` and require internal token
authorization.

### `POST /internal/auth/register`

Creates a new active user with role `user`.

Behavior:

- normalizes email and pseudo
- validates password policy
- rejects duplicate users
- stores password hash only

Rate limits:

- IP: 10 requests / 1 hour
- Email: 5 requests / 1 hour

### `POST /internal/auth/login`

Authenticates user and creates a session.

Behavior:

- verifies normalized credentials
- rejects inactive users
- creates session row with expiration
- returns clear session token

Rate limits:

- IP: 30 requests / 5 minutes
- Email: 10 requests / 5 minutes

### `POST /internal/auth/session`

Resolves token and returns session + user projection.

### `POST /internal/auth/resolve-session`

Resolves token and returns internal session context:

- `user_id`
- `email`
- `role`
- `is_active`
- `api_access_enabled`
- `session_expires_at`

### `POST /internal/auth/logout`

Revokes session by token hash.

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
2. enforce rate limits
3. normalize and validate input
4. create user
5. return user projection

### Login Flow

1. validate internal token
2. enforce rate limits
3. verify credentials
4. generate session token
5. store token hash + expiration
6. return token and user payload

### Session Resolution Flow

1. verify token presence
2. hash token
3. read active non-revoked session
4. validate expiry and user state
5. optionally touch `last_seen_at`
6. return authenticated context
