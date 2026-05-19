from __future__ import annotations

import os

# Bootstrap env before app modules configure database access at import time.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
	"IDENTITY_DATABASE_URL",
	"postgresql://manifeed:manifeed@localhost:5432/manifeed_identity_test",
)
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "x" * 32)
