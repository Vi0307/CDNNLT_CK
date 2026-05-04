from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.config import AUDIO_DIR
from app.schemas import TTSRequest, TTSResponse
from app.service import generate_audio_file

@app.post("/tts", response_model=TTSResponse)
async def create_tts(request: TTSRequest):
    try:
        print(f"DEBUG: Processing TTS for text length: {len(request.text)}")
        filename, _ = await generate_audio_file(text=request.text, language=request.language, voice=request.voice)
        return TTSResponse(
            status="success",
            audio_url=f"/download/{filename}",
            message="Thành công"
        )
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_audio(filename: str):
    filepath = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(path=filepath, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/")
async def root():
    return {"message": "TTS Service is running"}
