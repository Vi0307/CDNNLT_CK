import uuid
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

SUPPORTED_LANGUAGES = {"vi", "en"}

class ProcessRequest(BaseModel):
    text: str
    request_id: Optional[str] = None
    language: str = "vi"

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        """Bắt buộc 'text' không được rỗng."""
        if not v or not v.strip():
            raise ValueError("text field is required")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Nếu language không hợp lệ → mặc định về 'vi'."""
        return v if v in SUPPORTED_LANGUAGES else "vi"

    @model_validator(mode="after")
    def auto_generate_request_id(self) -> "ProcessRequest":
        """Tự sinh UUID nếu request_id không được cung cấp."""
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
        return self

class ProcessResponse(BaseModel):
    request_id: str
    summary: str
    script: str
    status: str
    language: str
    source: str  # "claude" | "mock"
