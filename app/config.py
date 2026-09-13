"""
Application configuration.
Uses pydantic-settings so every tunable is overridable via env vars
(this is what Render injects at deploy time).
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # pydantic-settings v2 style
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core ---
    app_name: str = "Nigeria Timezone API"
    app_version: str = "1.0.0"
    debug: bool = False                 # NEVER enable in production
    environment: str = "production"     # development | staging | production

    # --- CORS ---
    # Comma-separated origins. Use "*" only for dev.
    cors_origins: str = "*"

    # --- Rate limit (simple in-memory, per-process) ---
    rate_limit_per_minute: int = 120

    # --- Logging ---
    log_level: str = "INFO"

    # --- Source timezone (Nigeria) ---
    # Locked to Africa/Lagos; exposed as a setting so tests can override.
    source_timezone: str = "Africa/Lagos"


# Single global instance — imported everywhere else.
settings = Settings()
