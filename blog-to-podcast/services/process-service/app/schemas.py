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
    source: str  # "gemini" | "mock"


class AskRequest(BaseModel):
    question: str
    context: str
    language: str = "vi"

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("question field is required")
        return v

    @field_validator("context")
    @classmethod
    def context_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("context field is required")
        return v

    @field_validator("language")
    @classmethod
    def validate_ask_language(cls, v: str) -> str:
        return v if v in SUPPORTED_LANGUAGES else "vi"


class AskResponse(BaseModel):
    answer: str
    language: str
    source: str


class ExplainRequest(BaseModel):
    term: str
    context: str
    language: str = "vi"

    @field_validator("term")
    @classmethod
    def term_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("term field is required")
        return v

    @field_validator("context")
    @classmethod
    def explain_context_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("context field is required")
        return v

    @field_validator("language")
    @classmethod
    def validate_explain_language(cls, v: str) -> str:
        return v if v in SUPPORTED_LANGUAGES else "vi"


class ExplainResponse(BaseModel):
    explanation: str
    language: str
    source: str
