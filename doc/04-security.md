# Security

## Internal Service Authentication

Header used for internal authorization:

- `x-manifeed-internal-token`

Policy:

- local/test-like environments may allow missing token when not configured
- strict environments require configured token
- weak tokens are rejected in strict mode
- token comparison uses constant-time `secrets.compare_digest`

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

## Rate Limiting Security

Login and register endpoints are protected with namespace-based buckets:

- IP-based buckets
- email-based buckets

Redis availability policy:

- strict mode blocks when Redis is unavailable
- optional mode uses in-memory fallback
