from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Prodigy Workspace API"
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/prodigy"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    redis_url: str = "redis://localhost:6379/0"
    comp_cache_ttl_seconds: int = 21600
    comp_old_days_threshold: int = 180
    enabled_connectors: str = ""
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
