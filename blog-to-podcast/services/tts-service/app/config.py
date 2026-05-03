import os
from dotenv import load_dotenv

load_dotenv()


# API Key cho Google Cloud (dùng để gọi Text-to-Speech)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Đảm bảo thư mục tồn tại khi import config
os.makedirs(AUDIO_DIR, exist_ok=True)
