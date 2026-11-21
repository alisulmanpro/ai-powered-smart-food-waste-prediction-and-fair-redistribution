from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_SECRET = "change-me-in-dot-env-use-a-long-random-secret-key"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Smart Food Waste Redistribution API"
    API_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://foodwaste:foodwaste@localhost:5432/foodwaste"
    TEST_DATABASE_URL: str | None = None  # defaults to "<DATABASE_URL db>_test"

    # Auth
    JWT_SECRET: str = INSECURE_DEFAULT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS: comma separated list of allowed origins (admin panel, Expo web, ...)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8081"

    # First admin, created by scripts/seed.py (admins cannot self-register, FR-UM-07)
    FIRST_ADMIN_NAME: str = "Admin"
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "admin12345"

    # Domain settings
    ALLOCATION_RESPONSE_MINUTES: int = 60
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    MODEL_DIR: str = "models_store"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def validate_for_production(self) -> None:
        if self.ENVIRONMENT == "production" and self.JWT_SECRET == INSECURE_DEFAULT_SECRET:
            raise RuntimeError("Set a strong JWT_SECRET before running in production.")


settings = Settings()
