#!/bin/sh
# Prod container entrypoint: wait for DB -> migrate -> seed -> run (no reload).
set -e

python -m scripts.wait_for_db
alembic upgrade head
python -m scripts.seed

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
