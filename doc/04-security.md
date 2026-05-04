# Security

## Internal Service Authentication

Header used for internal authorization:

- `x-manifeed-internal-token`

Policy:

- local/test-like environments may allow missing token when not configured
- `REQUIRE_INTERNAL_SERVICE_TOKEN=true` forces strict mode even in local-like environments
- strict environments require configured token
- strict environments accept either one `INTERNAL_SERVICE_TOKEN` or a comma-separated `INTERNAL_SERVICE_TOKENS` set
- weak tokens are rejected in strict mode
- token comparison uses constant-time `secrets.compare_digest`
- `/internal/health` and `/internal/ready` stay unauthenticated for orchestration probes

## Password Security

- password policy validated before registration
- password hash/verify delegated to shared backend auth utilities
- login rejects invalid credentials with generic failure behavior

## Session Security

- token format: `msess_<random-secret>`
- token entropy generated from 32 random bytes
- only token hash is stored in database
- expired tokens are revoked during resolution
- `last_seen_at` updates are throttled by touch interval
- active sessions are capped per user at login time
- a background maintenance loop purges expired sessions and aged revoked sessions

## Edge And Gateway Controls

`auth_service` no longer applies local rate limiting.

Expected deployment model:

- edge/Nginx owns coarse IP-based throttling
- `public_api` owns identifier-based throttling such as email and pseudo
- `auth_service` assumes trusted internal callers and should not be exposed directly

## Current Security Gaps

- inter-service auth still uses header-borne shared secrets rather than mTLS or JWT
- session token hashing uses plain SHA-256 without an extra server-side pepper
