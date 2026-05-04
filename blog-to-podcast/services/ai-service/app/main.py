from fastapi import FastAPI, HTTPException
from app.ai_client import AIFactory
from app.config import settings, setup_logging
from app.schemas import AIRequest, AIResponse
import logging

setup_logging()
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Gateway Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/generate", response_model=AIResponse)
def generate_content(request: AIRequest):
    provider_type = request.provider or settings.ai_provider
    
    config = {
        "api_key": settings.anthropic_api_key,
        "base_url": settings.anthropic_base_url,
        "model": settings.anthropic_model,
        "timeout": settings.ai_timeout
    }
    
    try:
        provider = AIFactory.get_provider(provider_type, config)
        content = provider.generate_content(
            prompt=request.prompt,
            system_instruction=request.system_instruction
        )
        
        return AIResponse(
            content=content,
            provider=provider_type,
            model=settings.anthropic_model
        )
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
