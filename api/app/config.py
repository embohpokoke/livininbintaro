from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://livin:L1v1n!B1nt4r0_2026@localhost:5432/livininbintaro"
    SECRET_KEY: str = "livininbintaro-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    APP_VERSION: str = "2.0.0"
    APP_NAME: str = "Livininbintaro V2 API"
    FRONTEND_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "https://livininbintaro.my.id",
            "https://www.livininbintaro.my.id",
            "https://dashboard.livininbintaro.my.id",
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )
    GOWA_LIVININ_SECRET: str = "liviningowaSecret2026"


settings = Settings()
