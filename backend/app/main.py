from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

settings.validate_for_production()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "Decision-support API: predicts surplus food, filters and fairly ranks recipients, "
        "plans collection. Predictions are estimates only; food-safety rules always apply."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["health"])
def liveness() -> dict:
    """Cheap liveness probe (no DB). Used by the Docker healthcheck."""
    return {"status": "ok"}
