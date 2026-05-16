import logging
import requests
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_content(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        pass

class ClaudeProvider(BaseAIProvider):
    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 60):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        url = f"{self.base_url}/v1/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        if system_instruction:
            payload["system"] = system_instruction

        masked_key = f"{self.api_key[:6]}...{self.api_key[-4:]}" if len(self.api_key) > 10 else "INVALID_KEY"
        logger.info(f"Calling Proxy: {url}")
        logger.info(f"Model: {self.model} | Key: {masked_key}")

        # Retry tối đa 3 lần với delay tăng dần khi gặp 503/rate limit
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, 
                    headers=headers, 
                    json=payload, 
                    timeout=self.timeout
                )
                
                # Nếu 503 (rate limit/auth lỗi tạm thời) → retry sau delay
                if response.status_code == 503:
                    wait = (attempt + 1) * 3  # 3s, 6s, 9s
                    logger.warning(f"503 from proxy (attempt {attempt+1}/{max_retries}), retrying in {wait}s...")
                    if attempt < max_retries - 1:
                        time.sleep(wait)
                        continue
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"Claude raw response keys: {list(data.keys())}, content type: {type(data.get('content'))}")
                
                content = data.get("content", [])
                if isinstance(content, str):
                    if content:
                        logger.info("Claude API call successful (string content)")
                        return content
                    else:
                        raise Exception(f"Claude returned empty content. Response: {data}")
                if content and len(content) > 0:
                    text_content = ""
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_content = block.get("text", "")
                            break
                    if not text_content:
                        for block in content:
                            if isinstance(block, dict) and "text" in block:
                                text_content = block["text"]
                                break
                    logger.info(f"Claude API call successful, text length={len(text_content)}")
                    return text_content
                
                raise Exception(f"Invalid response format from Claude: {data}")
                
            except requests.exceptions.Timeout:
                logger.error(f"Claude API timeout after {self.timeout}s")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise Exception("AI Provider Timeout")
            except requests.exceptions.HTTPError as e:
                if response.status_code == 503 and attempt < max_retries - 1:
                    continue  # đã xử lý ở trên
                logger.error(f"Claude API Error: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response details: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Claude API Error: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response details: {e.response.text}")
                raise

class AIFactory:
    @staticmethod
    def get_provider(provider_type: str, config: Dict[str, Any]) -> BaseAIProvider:
        if provider_type.lower() == "claude":
            return ClaudeProvider(
                api_key=config.get("api_key"),
                base_url=config.get("base_url"),
                model=config.get("model"),
                timeout=config.get("timeout", 60)
            )
        raise ValueError(f"Unsupported AI Provider: {provider_type}")
