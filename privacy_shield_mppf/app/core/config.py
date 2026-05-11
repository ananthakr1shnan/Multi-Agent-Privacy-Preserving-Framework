"""
Configuration management for the MPPF application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""

    # API Keys
    groq_api_key: str

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # ── Per-Agent Model Configuration ─────────────────────────────────────────
    # Creativity Agent — largest model, high temperature for divergent thinking
    creativity_model: str = "llama-3.3-70b-versatile"

    # Productivity Agent — fast & focused, receives creative brief
    productivity_model: str = "llama-3.1-8b-instant"

    # Ethics Agent — Llama 4 Scout, strong instruction following for structured JSON verdicts
    ethics_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Aggregator / Judge — llama-3.3-70b (official replacement for deepseek-r1 per Groq docs)
    aggregator_model: str = "llama-3.3-70b-versatile"

    # ── Pipeline Configuration ─────────────────────────────────────────────────
    # Maximum number of Productivity→Ethics retries before force-accept
    max_ethics_retries: int = 2

    # Web search results per query
    web_search_max_results: int = 5

    # ── Legacy / Shared Config ─────────────────────────────────────────────────
    groq_model: str = "llama-3.3-70b-versatile"
    groq_api_base: str = "https://api.groq.com/openai/v1"
    max_tokens: int = 1024
    temperature: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
