# Operations

## Production Recommendations

- set `APP_ENV=production` (or explicit staging value)
- configure strong `INTERNAL_SERVICE_TOKEN` (min 32 chars)
- keep `RATE_LIMIT_REDIS_REQUIRED=true` in production
- set explicit `IDENTITY_DATABASE_URL` for all deployments
- monitor DB pool usage and rate limit rejection rates

## Known Constraints

- Redis rate limit increment and TTL are sent as separate commands
- no built-in scheduled purge for expired/revoked sessions
- session resolution reads from Postgres directly
- inter-service auth currently relies on a shared secret token

## Documentation Maintenance

Update docs in this folder whenever behavior changes in:

- `app/main.py`
- `app/routers/internal_auth_router.py`
- `app/services/*`
- `shared_backend/security/internal_service_auth.py`
- `app/middleware/rate_limit.py`
- `app/clients/database/*`
