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

    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    short_uuid = str(uuid.uuid4())[:6]
    filename = f"{now_str}_{short_uuid}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    if not GOOGLE_API_KEY:
        try:
            import edge_tts
            print(f"DEBUG: Using edge-tts fallback. Voice: {voice}")
            edge_voice_map = {
                "vi-VN-Neural2-A": "vi-VN-HoaiMyNeural",
                "vi-VN-Neural2-D": "vi-VN-NamMinhNeural",
                "en-US-Neural2-F": "en-US-AriaNeural",
                "en-US-Neural2-J": "en-US-ChristopherNeural",
                "fr-FR-Neural2-A": "fr-FR-DeniseNeural",
                "fr-FR-Neural2-B": "fr-FR-HenriNeural",
                "ja-JP-Neural2-A": "ja-JP-NanamiNeural",
                "ja-JP-Neural2-B": "ja-JP-KeitaNeural",
            }
            
            if voice in edge_voice_map:
                edge_voice = edge_voice_map[voice]
            elif voice and voice.endswith("Neural") and "Neural2" not in voice:
                edge_voice = voice
            else:
                if language == "vi":
                    edge_voice = "vi-VN-HoaiMyNeural"
                elif language == "en":
                    edge_voice = "en-US-AriaNeural"
                elif language == "fr":
                    edge_voice = "fr-FR-DeniseNeural"
                elif language == "ja":
                    edge_voice = "ja-JP-NanamiNeural"
                else:
                    edge_voice = "en-US-AriaNeural"
                
            import re
            def split_text(text, max_length=1500):
                sentences = re.split(r'(?<=[.!?\n])\s+', text)
                chunks = []
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= max_length:
                        current_chunk += " " + sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                if current_chunk:
                    chunks.append(current_chunk.strip())
                return chunks

            chunks = split_text(text, max_length=1500)
            print(f"DEBUG: Starting edge-tts save. Text split into {len(chunks)} chunks...")
            
            import asyncio
            try:
                # Mở file để ghi byte tuần tự
                with open(filepath, 'wb') as f:
                    for i, chunk_text in enumerate(chunks):
                        if not chunk_text.strip():
                            continue
                        print(f"DEBUG: Processing chunk {i+1}/{len(chunks)}...")
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                communicate = edge_tts.Communicate(chunk_text, edge_voice)
                                async def process_chunk():
                                    async for chunk in communicate.stream():
                                        if chunk["type"] == "audio":
                                            f.write(chunk["data"])
                                await asyncio.wait_for(process_chunk(), timeout=120.0)
                                break  # Success!
                            except asyncio.TimeoutError:
                                if attempt == max_retries - 1: raise
                                print(f"DEBUG: Chunk timeout, retrying {attempt+1}...")
                                await asyncio.sleep(1)
                            except Exception as e:
                                if "No audio" in str(e) or "NoAudioReceived" in str(type(e).__name__):
                                    if attempt == max_retries - 1: raise
                                    print(f"DEBUG: NoAudioReceived, retrying {attempt+1}...")
                                    await asyncio.sleep(1.5)
                                else:
                                    raise
                print(f"DEBUG: edge-tts save complete. Saved to {filepath}")
            except asyncio.TimeoutError:
                print("DEBUG: edge-tts SKIPPED (Timeout during chunking)")
                raise Exception("Tạo Audio thất bại: Quá thời gian xử lý (Timeout) khi tải một đoạn kịch bản.")
            except Exception as e:
                print(f"DEBUG: edge-tts SKIPPED (Error): {str(e)}")
                raise Exception(f"Lỗi tạo Audio từ Edge-TTS: {str(e)}")
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

