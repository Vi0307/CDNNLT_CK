import os


class Settings:
    use_mock: bool = os.getenv("USE_MOCK", "true").lower() == "true"


settings = Settings()

# Thư mục lưu file mp3 (trong Docker volume thường mount ./audio_output → /app/audio_output)
AUDIO_DIR = os.getenv("AUDIO_DIR", "audio_output")
os.makedirs(AUDIO_DIR, exist_ok=True)
