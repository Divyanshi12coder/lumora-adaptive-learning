#!/bin/sh
# Container entrypoint: migrate -> seed -> serve.
set -e
echo "Running database migrations..."
alembic upgrade head
if [ "${SEED_DEMO_USER:-false}" = "true" ]; then
  echo "Seeding curriculum + demo learner (simulated history)..."
  python -m app.seed.run --demo-user
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
