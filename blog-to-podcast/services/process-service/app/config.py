import logging
import os

class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "AIzaSyAZUclbJuGUsm5-eJ0S0roWVe0z10Z1xK0")
    use_mock: bool = os.getenv("USE_MOCK", "false").lower() == "true"

settings = Settings()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
