import json
import logging
from typing import Any

import requests
from fastapi import HTTPException

from app.config import settings
from app.schemas import ProcessRequest, ProcessResponse

logger = logging.getLogger(__name__)


def process_text(request: ProcessRequest) -> ProcessResponse:
    if settings.use_mock:
        return process_text_mock(request)
    return process_text_with_ai_service(request)


def process_text_with_ai_service(request: ProcessRequest) -> ProcessResponse:
    try:
        system_instruction = (
            "Bạn là một biên tập viên podcast chuyên nghiệp. "
            "Nhiệm vụ của bạn là đọc một bài viết, sau đó tạo ra một kịch bản podcast. "
            "Yêu cầu TRẢ VỀ DUY NHẤT một đối tượng JSON hợp lệ với 3 trường:\n"
            "1. 'original_script': Kịch bản podcast viết bằng CHÍNH NGÔN NGỮ GỐC CỦA BÀI BÁO.\n"
            "2. 'script': Kịch bản podcast ĐÃ ĐƯỢC DỊCH SANG NGÔN NGỮ ĐÍCH do người dùng yêu cầu.\n"
            "3. 'summary': Tóm tắt bài báo bằng NGÔN NGỮ ĐÍCH."
        )

        prompt = f"""
NGÔN NGỮ ĐÍCH NGƯỜI DÙNG YÊU CẦU: {request.language}

NỘI DUNG BÀI VIẾT:
{request.text[:15000]}

CÁC BƯỚC THỰC HIỆN:
Bước 1: Xác định ngôn ngữ gốc của bài viết trên.
Bước 2: Dựa trên bài viết, hãy soạn một kịch bản podcast sinh động bằng CHÍNH NGÔN NGỮ GỐC ĐÓ. Lưu vào trường "original_script".
Bước 3: Dịch kịch bản podcast ở Bước 2 sang ngôn ngữ đích ({request.language}). Lưu vào trường "script". Nếu ngôn ngữ đích đã trùng với ngôn ngữ gốc, hãy copy y nguyên.
Bước 4: Viết một đoạn tóm tắt bài báo bằng ngôn ngữ đích ({request.language}). Lưu vào trường "summary".

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (Chỉ chứa JSON, không chứa dấu ```):
{{
  "original_script": "...",
  "script": "...",
  "summary": "..."
}}
""".strip()

        logger.info("Sending request to AI Service (Claude)")
        response = requests.post(
            f"{settings.ai_service_url}/generate",
            json={
                "prompt": prompt,
                "system_instruction": system_instruction,
                "provider": "claude",
            },
            timeout=settings.ai_timeout,
        )
        response.raise_for_status()
        ai_data = response.json()
        content = ai_data.get("content", "")
        data = _parse_ai_json(content)

        script_val = _stringify_ai_field(data.get("script", ""))
        summary_val = _stringify_ai_field(data.get("summary", ""))
        original_script_val = _stringify_ai_field(data.get("original_script", ""))

        if not script_val.strip():
            raise ValueError("Claude response did not contain a usable script")

        return ProcessResponse(
            request_id=request.request_id,
            summary=summary_val,
            original_script=original_script_val,
            script=script_val,
            status="done",
            language=request.language,
            source="claude",
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"AI Service request failed: {e}")
        raise HTTPException(status_code=502, detail=f"Claude AI service request failed: {e}")
    except ValueError as e:
        logger.error(f"Validation/Parsing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Claude processing failed: {e}")
        raise HTTPException(status_code=502, detail=f"Claude processing failed: {e}")


def _parse_ai_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse inner JSON: {e2}. Snippet: {content[start:start+200]}")
                raise ValueError(f"JSON parsing error: {e2}")
        
        logger.error(f"Failed to parse JSON: {e}. Snippet: {content[:200]}")
        
        # Check if content has safety block or generic/refusal response
        refusal_keywords = [
            "can't discuss", "cannot discuss", "can't help", "cannot help", "sorry, i",
            "từ chối", "không thể hỗ trợ", "không thể thảo luận", "an toàn", "nhạy cảm",
            "I'm Claude", "I am Claude", "Hi there!"
        ]
        if any(kw.lower() in content.lower() for kw in refusal_keywords):
            raise ValueError(f"AI từ chối xử lý nội dung nhạy cảm hoặc phản hồi không phù hợp: \"{content[:100]}...\"")
            
        raise ValueError("Could not find valid JSON object in Claude response")


def _stringify_ai_field(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(
            item.get("content", str(item)) if isinstance(item, dict) else str(item)
            for item in value
        ).strip()
    if value is None:
        return ""
    return str(value).strip()


def process_text_mock(request: ProcessRequest) -> ProcessResponse:
    return ProcessResponse(
        request_id=request.request_id,
        summary="[MOCK] Đây là tóm tắt giả lập cho mục đích kiểm thử.",
        original_script="[MOCK] Hello, this is a mock podcast script for testing.",
        script="[MOCK] Xin chào, đây là kịch bản podcast giả lập cho mục đích kiểm thử.",
        status="done",
        language=request.language,
        source="mock",
    )
