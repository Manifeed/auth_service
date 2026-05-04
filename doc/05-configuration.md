# Configuration

## Core Runtime

- `APP_ENV`: primary environment selector
- `ENVIRONMENT`: fallback environment selector
- `IDENTITY_DATABASE_URL`: PostgreSQL DSN for identity database
- `REQUIRE_EXPLICIT_DATABASE_URLS`: forces explicit DB URL in strict envs
- `INTERNAL_SERVICE_TOKEN`: shared internal secret
- `INTERNAL_SERVICE_TOKENS`: optional comma-separated accepted ingress tokens
- `REQUIRE_INTERNAL_SERVICE_TOKEN`: strict token requirement toggle

## Session Variables

- `AUTH_SESSION_TTL_SECONDS`
	- default: `604800` (7 days)
	- invalid/non-positive values fallback to default

- `AUTH_SESSION_TOUCH_INTERVAL_SECONDS`
	- default: `300` (5 minutes)
	- invalid/negative values fallback to default

- `AUTH_MAX_ACTIVE_SESSIONS_PER_USER`
	- default: `5`
	- invalid/non-positive values fallback to default

- `AUTH_SESSION_PURGE_INTERVAL_SECONDS`
	- default: `900` (15 minutes)
	- invalid/non-positive values fallback to default

- `AUTH_SESSION_REVOKED_RETENTION_SECONDS`
	- default: `86400` (24 hours)
	- invalid/non-positive values fallback to default

## Database Pool Variables

- `DB_POOL_SIZE` (default: `5`)
- `DB_MAX_OVERFLOW` (default: `10`)
- `DB_POOL_TIMEOUT_SECONDS` (default: `30`)
- `DB_POOL_RECYCLE_SECONDS` (default: `1800`)

Current implementation note:

- invalid or too-small DB pool values fall back to safe defaults at import time
