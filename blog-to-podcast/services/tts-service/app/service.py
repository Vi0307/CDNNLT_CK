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
            import edge_tts
            print(f"DEBUG: Using edge-tts fallback. Voice: {voice}")
            # Nếu Frontend truyền tên giọng Edge-TTS (kết thúc bằng Neural), ta sẽ dùng luôn giọng đó.
            # Nếu không (hoặc truyền giọng của Google như Neural2), ta dùng giọng mặc định.
            if voice and voice.endswith("Neural") and "Neural2" not in voice:
                edge_voice = voice
            else:
                edge_voice = "vi-VN-HoaiMyNeural" if language == "vi" else "en-US-AriaNeural"
                
            communicate = edge_tts.Communicate(text, edge_voice)
            print(f"DEBUG: Starting edge-tts save (Background Task - 60s timeout)...")
            import asyncio
            try:
                # Đợi tối đa 60 giây vì đây là chạy ngầm
                await asyncio.wait_for(communicate.save(filepath), timeout=60.0)
                print(f"DEBUG: edge-tts save complete. Saved to {filepath}")
            except Exception as e:
                print(f"DEBUG: edge-tts SKIPPED (Timeout or Error): {str(e)}")
                # Tạo file trắng ngay lập tức để không bị treo fetch
                with open(filepath, 'wb') as f:
                    f.write(b'\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                return filename, filepath
            return filename, filepath
        except Exception as e:
            print(f"DEBUG: CRITICAL ERROR in service.py: {str(e)}")
            raise e

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

