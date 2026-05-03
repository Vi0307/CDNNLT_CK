import os
import uuid
import base64
import httpx
from app.config import AUDIO_DIR, GOOGLE_API_KEY

async def generate_audio_file(text: str, language: str, voice: str = None) -> tuple[str, str]:
    if not voice:
        # Mặc định sử dụng giọng cao cấp Neural2 của Google
        if language == "vi":
            voice = "vi-VN-Neural2-A"
        elif language == "en":
            voice = "en-US-Neural2-F"
        else:
            voice = "vi-VN-Neural2-A"

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    if not GOOGLE_API_KEY:
        try:
            from gtts import gTTS
            # Determine language code for gTTS
            lang_code = "vi" if language == "vi" else "en"
            tts = gTTS(text=text, lang=lang_code)
            tts.save(filepath)
            print(f"Mocking TTS with gTTS (No API Key). Saved to {filepath}")
            return filename, filepath
        except ImportError:
            print("gTTS not installed. Creating empty dummy file.")
            # Create a dummy silent/empty mp3 file for mock testing
            with open(filepath, 'wb') as f:
                pass
            return filename, filepath

    # Gọi Google Cloud TTS REST API
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}"

    # Xác định language code từ tên voice (ví dụ: vi-VN-Neural2-A -> vi-VN)
    language_code = "-".join(voice.split("-")[:2]) if "-" in voice else "vi-VN"

    payload = {
        "input": {
            "text": text
        },
        "voice": {
            "languageCode": language_code,
            "name": voice
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60.0)
        if response.status_code != 200:
            error_details = response.text
            raise Exception(f"Google TTS API Error (Status {response.status_code}): {error_details}")

        data = response.json()
        audio_content = data.get("audioContent")
        if not audio_content:
            raise Exception("Google TTS API returned success but no audioContent.")

        # audioContent là chuỗi base64
        audio_bytes = base64.b64decode(audio_content)
        # Ghi file
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
    return filename, filepath

async def generate_tts(text: str, language: str):
    """
    Sử dụng Edge-TTS để chuyển văn bản thành giọng nói thật.
    """
    if settings.use_mock:
        return generate_mock_tts()

    # Chọn giọng đọc dựa trên ngôn ngữ
    voice = "vi-VN-HoaiMyNeural" if language.lower() == "vietnamese" else "en-US-GuyNeural"
    
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    if not GOOGLE_API_KEY:
        try:
            from gtts import gTTS
            # Determine language code for gTTS
            lang_code = "vi" if language.lower() == "vietnamese" else "en"
            tts = gTTS(text=text, lang=lang_code)
            tts.save(filepath)
            print(f"Mocking TTS with gTTS (No API Key). Saved to {filepath}")
            return filename, filepath
        except ImportError:
            print("gTTS not installed. Creating empty dummy file.")
            # Create a dummy silent/empty mp3 file for mock testing
            with open(filepath, 'wb') as f:
                pass
            return filename, filepath

    # Gọi Google Cloud TTS REST API
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}"
    
    # Xác định language code từ tên voice (ví dụ: vi-VN-Neural2-A -> vi-VN)
    language_code = "-".join(voice.split("-")[:2]) if "-" in voice else "vi-VN"

    payload = {
        "input": {
            "text": text
        },
        "voice": {
            "languageCode": language_code,
            "name": voice
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60.0)
        
        if response.status_code != 200:
            error_details = response.text
            raise Exception(f"Google TTS API Error (Status {response.status_code}): {error_details}")

        data = response.json()
        audio_content = data.get("audioContent")
        
        if not audio_content:
            raise Exception("Google TTS API returned success but no audioContent.")

        # audioContent là chuỗi base64
        audio_bytes = base64.b64decode(audio_content)
        
        # Ghi file
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
    return filename, filepath
