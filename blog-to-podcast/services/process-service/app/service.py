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
            f"Bạn là một biên tập viên podcast chuyên nghiệp. Ngôn ngữ: {request.language}. "
            "Chỉ trả về JSON hợp lệ, không markdown, không giải thích thêm. "
            "JSON bắt buộc có đúng 2 trường: "
            "'summary' là chuỗi tóm tắt ngắn gọn và 'script' là chuỗi kịch bản podcast hoàn chỉnh."
        )

        prompt = f"""
HÃY XỬ LÝ NỘI DUNG BÀI VIẾT SAU:
{request.text[:15000]}

YÊU CẦU:
1. summary: Tóm tắt nội dung chính, ngắn gọn, dễ hiểu.
2. script: Viết lại thành kịch bản podcast lôi cuốn, tự nhiên, phù hợp để đọc thành audio.
3. Không thêm markdown/code fence.
4. Chỉ trả về JSON hợp lệ dạng: {{"summary":"...","script":"..."}}
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

        if not script_val.strip():
            raise ValueError("Claude response did not contain a usable script")

        return ProcessResponse(
            request_id=request.request_id,
            summary=summary_val,
            script=script_val,
            status="done",
            language=request.language,
            source="claude",
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"AI Service request failed: {e}")
        raise HTTPException(status_code=502, detail=f"Claude AI service request failed: {e}")
    except Exception as e:
        logger.error(f"Claude processing failed: {e}")
        raise HTTPException(status_code=502, detail=f"Claude processing failed: {e}")


def _parse_ai_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end <= start:
            raise ValueError("Could not find JSON object in Claude response")
        return json.loads(content[start:end])


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
        script="[MOCK] Xin chào, đây là kịch bản podcast giả lập.",
        status="done",
        language=request.language,
        source="mock",
    )
