import os
import logging
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_base_url: str = os.getenv("ANTHROPIC_BASE_URL", "https://1gw.gwai.cloud")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    ai_timeout: int = int(os.getenv("AI_TIMEOUT", "60"))
    ai_provider: str = os.getenv("AI_PROVIDER", "claude")

    class Config:
        env_file = ".env"

settings = Settings()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
