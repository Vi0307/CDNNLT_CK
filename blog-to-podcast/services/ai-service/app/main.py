from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Service Mock")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    text: str
    language: str

class ProcessResponse(BaseModel):
    request_id: str
    summary: str
    script: str
    status: str
    language: str

@app.post("/process", response_model=ProcessResponse)
def process_text(req: ProcessRequest):
    return ProcessResponse(
        request_id="mock-123",
        summary=f"Đây là tóm tắt giả định của bài viết bằng tiếng {req.language}. Nó cho bạn cái nhìn tổng quan về nội dung.",
        script=f"Chào mừng bạn đến với podcast! Hôm nay chúng ta sẽ thảo luận về một bài viết thú vị. Đây là nội dung kịch bản đã được chuyển đổi. Ngôn ngữ: {req.language}",
        status="success",
        language=req.language
    )
