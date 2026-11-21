# syntax=docker/dockerfile:1

# ---------- base: system libs + python deps ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# libgomp1: needed by scikit-learn / OR-Tools wheels. curl: container healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---------- dev: hot reload, test + lint tools ----------
# docker-compose bind-mounts ./backend into /app, so code edits reload instantly.
FROM base AS dev

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY . .

EXPOSE 8000
CMD ["sh", "scripts/entrypoint.dev.sh"]


# ---------- prod: no reload, non-root user ----------
FROM base AS prod

RUN useradd --create-home --uid 1000 app
COPY --chown=app:app . .
USER app

EXPOSE 8000
CMD ["sh", "scripts/entrypoint.prod.sh"]
