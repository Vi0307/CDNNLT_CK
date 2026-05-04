import logging
import os

class Settings:
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://ai-service:8004")
    use_mock: bool = os.getenv("USE_MOCK", "false").lower() == "true"
    ai_timeout: int = int(os.getenv("AI_TIMEOUT", "180"))

settings = Settings()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
