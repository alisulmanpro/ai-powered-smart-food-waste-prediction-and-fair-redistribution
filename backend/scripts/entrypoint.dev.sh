#!/bin/sh
# Dev container entrypoint: wait for DB -> migrate -> seed -> run with auto-reload.
set -e

python -m scripts.wait_for_db
alembic upgrade head
python -m scripts.seed

exec uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 \
  --reload --reload-dir app
