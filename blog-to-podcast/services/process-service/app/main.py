from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import setup_logging
from app.schemas import ProcessRequest, ProcessResponse
from app.service import process_text_mock

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(
    title="Process Service",
    description="Microservice xử lý văn bản Blog thành nội dung Podcast",
    version="1.0.0",
)

# --- CORS Middleware (cho phép mọi origin) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoint: GET /health ---
@app.get("/health", tags=["Health"])
def health_check():
    """Kiểm tra trạng thái hoạt động của service."""
    return {"status": "ok", "service": "process-service"}

# --- Endpoint: POST /process ---
@app.post("/process", response_model=ProcessResponse, tags=["Process"])
def process_text(request: ProcessRequest):
    """
    Nhận văn bản Blog và trả về tóm tắt + kịch bản Podcast.
    """
    try:
        return process_text_mock(request)
    except Exception as e:
        logger.error(f"[request_id={request.request_id}] Lỗi xử lý: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal error", "detail": str(e)},
        )
