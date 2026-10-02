from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_port: int = 8000
    log_level: str = "info"

    groq_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"
    llm_base_url: str = "https://api.groq.com/openai/v1"

    tavily_api_key: str = ""

    # retrieval depth. override to run an A/B against the same question set.
    sub_queries: int = 8
    # measured on the cached pool, n1+n2, 100% pool overlap:
    # 3/query -> 19.0 sources at 542 chars each, 25 claims, 92% usable quotes
    # 5/query -> 30.5 at 360 chars, 11 claims, one refusal, one token-cap cut
    # the writer budget is fixed, so more results/query just thins each source
    results_per_query: int = 3

    # groq caps input+output at 8k tokens/min. 12000 chars + 3500 out is about
    # 6.8k tokens and fits
    writer_input_chars: int = 12000
    writer_context_chars: int = 2500
    writer_max_tokens: int = 3500


settings = Settings()