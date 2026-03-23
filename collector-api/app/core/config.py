import os


class Settings:
    APP_NAME: str = "trapnet collector"

    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "trapnet")
    DB_USER: str = os.getenv("DB_USER", "trapnet")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "trapnet")

    COLLECTOR_API_KEY_FILE: str = os.getenv(
        "COLLECTOR_API_KEY_FILE",
        "/run/secrets/collector_api_key",
    )


settings = Settings()