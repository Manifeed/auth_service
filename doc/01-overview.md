# Overview

## Service Purpose

`auth_service` is the internal authentication and session service for Manifeed.
It provides backend-only endpoints for identity lifecycle and session handling.

This service is designed for trusted internal consumers, not public/browser
clients.

## Responsibilities

- Register users with validation and normalization
- Authenticate users and issue session tokens
- Resolve session tokens into authenticated user context
- Revoke sessions through logout
- Cap concurrent active sessions per user
- Purge expired/revoked sessions on a background cadence
- Enforce internal service token authorization
- Expose health/readiness probes for orchestrators
- Emit shared request logs and shared JSON error payloads
- Stay focused on identity/session rules while edge and gateway layers own rate limiting

## Technical Stack

- FastAPI
- SQLAlchemy + psycopg + PostgreSQL
- `manifeed-shared-backend` for shared schemas/domain/errors
