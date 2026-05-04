# Operations

## Production Recommendations

- set `APP_ENV=production` (or explicit staging value)
- configure strong `INTERNAL_SERVICE_TOKEN` (min 32 chars)
- prefer distinct caller tokens and configure accepted ingress tokens through `INTERNAL_SERVICE_TOKENS` when rotating away from a single shared secret
- set explicit `IDENTITY_DATABASE_URL` for all deployments
- monitor DB pool usage, login failures, and session churn
- keep `/internal/auth/*` behind trusted internal networking only
- ensure edge and `public_api` rate limiting stay enabled, because this service does not throttle locally
- standardize client payloads on the wrapped `{"payload": ...}` contract
- tune session retention with `AUTH_MAX_ACTIVE_SESSIONS_PER_USER`, `AUTH_SESSION_PURGE_INTERVAL_SECONDS`, and `AUTH_SESSION_REVOKED_RETENTION_SECONDS`

## Known Constraints

- session resolution reads from Postgres directly
- inter-service auth still relies on shared-secret headers rather than mTLS/JWT

## Documentation Maintenance

Update docs in this folder whenever behavior changes in:

- `app/main.py`
- `app/services/routers/internal_auth_router.py`
- `app/services/*`
- `shared_backend/security/internal_service_auth.py`
- `app/clients/database/*`
