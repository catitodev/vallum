"""
VALLUM — Secure Configuration Module
Fail-safe: missing required secrets = crash on startup
"""

import os
from functools import lru_cache


class Settings:
    """All configuration from environment variables. NEVER hardcode secrets."""

    def __init__(self):
        self.env = os.getenv("ENV", "development").lower()
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

        self.lobster_trap_url = os.getenv("LOBSTER_TRAP_URL", "http://localhost:8080")
        self.lobster_trap_policy = os.getenv("LOBSTER_TRAP_POLICY", "configs/default_policy.yaml")

        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./vallum.db")

        self.audit_chain_secret = os.getenv("AUDIT_CHAIN_SECRET")
        self.audit_chain_algorithm = os.getenv("AUDIT_CHAIN_ALGORITHM", "sha256")

        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_secret_manager_enabled = os.getenv("GCP_SECRET_MANAGER_ENABLED", "false").lower() == "true"

        if self.is_production and not self.gemini_api_key and not self.gcp_secret_manager_enabled:
            raise RuntimeError("GEMINI_API_KEY or GCP Secret Manager required in production")

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
