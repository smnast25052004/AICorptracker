from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "corptracker"
    postgres_user: str = "corptracker"
    postgres_password: str = "corptracker_secret"

    kafka_bootstrap_servers: str = "localhost:29092"

    openai_api_key: str = ""
    llm_provider: str = "local"

    app_env: str = "development"
    api_port: int = 8000
    dashboard_port: int = 8501

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
