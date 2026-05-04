import logging
import os

class Settings:
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://ai-service:8004")
    use_mock: bool = os.getenv("USE_MOCK", "false").lower() == "true"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

settings = Settings()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
