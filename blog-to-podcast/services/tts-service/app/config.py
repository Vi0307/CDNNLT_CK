import os

# Thư mục lưu trữ file mp3 sinh ra
AUDIO_DIR = os.getenv("AUDIO_DIR", "audio_output")

# Đảm bảo thư mục tồn tại khi import config
os.makedirs(AUDIO_DIR, exist_ok=True)
