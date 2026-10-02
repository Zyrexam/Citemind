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
    # UNSETTLED: the old "measured: 3 beats 6" had nothing behind it -- the writer
    # emitted zero claims, so quote-pass rate was uncomputable. What is real: the
    # fixed 12000-char writer budget means more results/query = thinner slices
    # (5/query: 17.0 sources at 1277 chars; 3/query: 10.8 at 1517).
    results_per_query: int = 3

    # Groq's on-demand tier caps input+output at 8k tokens per minute. Measured at
    # ~3.6 chars/token, so 12000 + 3500 output fits. The previous 17000 + 4000
    # asked for 8713, so every request was rejected then retried at half budget.
    writer_input_chars: int = 12000
    writer_context_chars: int = 2500
    writer_max_tokens: int = 3500


settings = Settings()