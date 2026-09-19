from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_port: int = 8000
    log_level: str = "info"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    hf_token: str = ""
    tavily_api_key: str = ""

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""


settings = Settings()
