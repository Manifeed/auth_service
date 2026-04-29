# Development and Testing

## Local Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Minimum local environment:

```bash
export APP_ENV=local
export IDENTITY_DATABASE_URL=postgresql://manifeed:manifeed@localhost:5432/manifeed_identity
```

Optional Redis:

```bash
export REDIS_URL=redis://localhost:6379/0
```

Run service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

Build from monorepo root:

```bash
docker build -t manifeed-auth-service -f auth_service/Dockerfile .
```

Run:

```bash
docker run --rm -p 8000:8000 \
	-e APP_ENV=production \
	-e IDENTITY_DATABASE_URL='postgresql://user:pass@host:5432/db' \
	-e INTERNAL_SERVICE_TOKEN='replace-with-strong-secret-min-32-chars' \
	-e RATE_LIMIT_REDIS_REQUIRED=true \
	-e REDIS_URL='redis://redis:6379/0' \
	manifeed-auth-service
```

## Tests

Run all tests:

```bash
pytest -q
```

Current test coverage:

- source syntax validation
- internal token behavior
- rate limit fallback/strict behavior
- session touch interval logic

Recommended next tests:

- DB integration tests for register/login/session/logout flows
- Redis integration tests for TTL and counter behavior
- route-level contract tests per endpoint
