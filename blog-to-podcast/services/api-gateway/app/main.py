from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="API Gateway", description="Cổng giao tiếp duy nhất cho Blog2Cast")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConvertRequest(BaseModel):
    url: str
    language: str = "vi"
    voice: str = "vi-VN-Neural2-A"

class ConvertResponse(BaseModel):
    status: str
    audio_url: str
    summary: str

CONTENT_SERVICE_URL = "http://content-service:8001"
PROCESS_SERVICE_URL = "http://process-service:8002"
TTS_SERVICE_URL = "http://tts-service:8003"

@app.post("/convert", response_model=ConvertResponse)
async def convert_blog_to_podcast(request: ConvertRequest):
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Bước 1: Crawl nội dung
        try:
            content_res = await client.post(f"{CONTENT_SERVICE_URL}/crawl", json={"url": request.url})
            content_res.raise_for_status()
            content_data = content_res.json()
            article_text = content_data.get("text")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi Crawl: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối Content Service: {str(e)}")

        if not article_text:
             raise HTTPException(status_code=400, detail="Không thể lấy nội dung từ URL này.")

        # Bước 2: AI Tóm tắt và biên tập
        try:
            process_res = await client.post(f"{PROCESS_SERVICE_URL}/process", json={"text": article_text, "language": request.language})
            process_res.raise_for_status()
            process_data = process_res.json()
            summary_text = process_data.get("summary")
            script_text = process_data.get("script")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi AI Process: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối Process Service: {str(e)}")

        # Bước 3: Text-to-Speech
        try:
            tts_res = await client.post(f"{TTS_SERVICE_URL}/tts", json={
                "text": script_text,
                "language": request.language,
                "voice": request.voice
            })
            tts_res.raise_for_status()
            tts_data = tts_res.json()
            audio_url_raw = tts_data.get("audio_url") # /download/<filename>
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi TTS: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối TTS Service: {str(e)}")

        return ConvertResponse(
            status="success",
            audio_url=audio_url_raw,
            summary=summary_text
        )

@app.get("/download/{filename}")
async def download_audio(filename: str):
    # Proxy or stream from TTS service
    async def iterfile():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", f"{TTS_SERVICE_URL}/download/{filename}") as response:
                if response.status_code != 200:
                    yield b""
                    return
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(iterfile(), media_type="audio/mpeg")

@app.get("/")
def read_root():
    return {"message": "API Gateway is running"}
