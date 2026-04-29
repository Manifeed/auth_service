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
- Enforce internal service token authorization
- Apply rate limiting on login and registration

## Technical Stack

- FastAPI
- SQLAlchemy + psycopg + PostgreSQL
- Redis (rate limiting counters)
- `manifeed-shared-backend` for shared schemas/domain/errors
