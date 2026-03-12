"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Supabase ---
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous/public key")
    supabase_service_role_key: str = Field(..., description="Supabase service role key")

    # --- OpenAI ---
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")

    # --- Slack (Optional) ---
    slack_webhook_url: str = Field(default="", description="Slack incoming webhook URL")

    # --- Email / SMTP (Optional) ---
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="", description="SMTP username/email")
    smtp_password: str = Field(default="", description="SMTP password/app password")

    # --- App Settings ---
    app_env: str = Field(default="development", description="Application environment")
    app_debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
