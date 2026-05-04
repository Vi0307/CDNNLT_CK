import logging
import os
from typing import Annotated, Optional
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from app.config import setup_logging
from app.schemas import ProcessRequest, ProcessResponse
from app.service import process_text

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Process Service",
    description="Microservice xử lý văn bản Blog thành nội dung Podcast (via AI Gateway)",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "process-service",
        "ai_gateway_url": os.getenv("AI_SERVICE_URL", "http://ai-service:8004")
    }

@app.post("/process", response_model=ProcessResponse, tags=["Process"])
def process_endpoint(request: ProcessRequest):
    """Xử lý văn bản thông qua AI Service."""
    response = process_text(request)
    logger.info(f"AI Service response: {response}")
    return response

@app.post("/process/form", response_model=ProcessResponse, tags=["Process"])
def process_text_form(
    text: Annotated[str, Form(description="Dán nội dung bài báo")],
    language: Annotated[str, Form()] = "vi",
    request_id: Annotated[Optional[str], Form()] = None,
):
    """Hỗ trợ gửi form thay vì JSON."""
    request = ProcessRequest(text=text, language=language, request_id=request_id)
    return process_text(request)
