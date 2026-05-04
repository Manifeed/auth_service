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
- wrapped `payload` route contract
- DB pool configuration fallback
- corrupted password hash rejection at login
- session touch interval logic
- active session cap enforcement
- session maintenance entrypoint behavior

Recommended next tests:

- DB integration tests for register/login/session/logout flows

## Runtime Base

The container build now targets `python:3.13-slim`.
