import logging
import requests
import json
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
        
        # Thử cả 2 loại header phổ biến cho Proxy
        headers = {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}", # Một số proxy yêu cầu Bearer
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

        # Log kiểm tra (che bớt key)
        masked_key = f"{self.api_key[:6]}...{self.api_key[-4:]}" if len(self.api_key) > 10 else "INVALID_KEY"
        logger.info(f"Calling Proxy: {url}")
        logger.info(f"Model: {self.model} | Key: {masked_key}")

        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Claude raw response keys: {list(data.keys())}, content type: {type(data.get('content'))}")
            
            # Extract content from Claude's response format
            content = data.get("content", [])
            # Proxy có thể trả về string trực tiếp thay vì array
            if isinstance(content, str):
                if content:
                    logger.info("Claude API call successful (string content)")
                    return content
                else:
                    logger.error(f"Claude returned empty string content. Full response: {data}")
                    raise Exception(f"Claude returned empty content. Response: {data}")
            if content and len(content) > 0:
                # Claude có thể trả về nhiều blocks: thinking, text, ...
                # Cần lấy đúng block có type == "text"
                text_content = ""
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_content = block.get("text", "")
                        break
                if not text_content:
                    # Fallback: lấy block đầu tiên có key "text"
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            text_content = block["text"]
                            break
                logger.info(f"Claude API call successful, text length={len(text_content)}")
                return text_content
            
            logger.error(f"Unexpected Claude response format: {data}")
            raise Exception(f"Invalid response format from Claude: {data}")
            
        except requests.exceptions.Timeout:
            logger.error(f"Claude API timeout after {self.timeout}s")
            raise Exception("AI Provider Timeout")
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
