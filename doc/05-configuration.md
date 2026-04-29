# Configuration

## Core Runtime

- `APP_ENV`: primary environment selector
- `ENVIRONMENT`: fallback environment selector
- `IDENTITY_DATABASE_URL`: PostgreSQL DSN for identity database
- `REQUIRE_EXPLICIT_DATABASE_URLS`: forces explicit DB URL in strict envs
- `INTERNAL_SERVICE_TOKEN`: shared internal secret
- `REQUIRE_INTERNAL_SERVICE_TOKEN`: strict token requirement toggle

## Session Variables

- `AUTH_SESSION_TTL_SECONDS`
	- default: `604800` (7 days)
	- invalid/non-positive values fallback to default

- `AUTH_SESSION_TOUCH_INTERVAL_SECONDS`
	- default: `300` (5 minutes)
	- invalid/negative values fallback to default

## Rate Limiting Variables

- `RATE_LIMIT_ENABLED`
	- enabled by default
	- disable with `0`, `false`, `no`, `off`

- `RATE_LIMIT_REDIS_REQUIRED`
	- explicit strict/optional behavior when set
	- if unset, strict behavior is applied in production-like envs

- `REDIS_URL`
	- default: `redis://redis:6379/0`

- `REDIS_SOCKET_TIMEOUT_SECONDS`
	- default: `0.2`
	- invalid/non-positive values fallback to default

## Database Pool Variables

- `DB_POOL_SIZE` (default: `5`)
- `DB_MAX_OVERFLOW` (default: `10`)
- `DB_POOL_TIMEOUT_SECONDS` (default: `30`)
- `DB_POOL_RECYCLE_SECONDS` (default: `1800`)
