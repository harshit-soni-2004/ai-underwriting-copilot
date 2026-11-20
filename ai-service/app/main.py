from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title="MSME Underwriting AI Service",
    description="FastAPI service powering document extraction, policy RAG, and credit memo drafting",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {
        "status": "OK",
        "service": settings.service_name,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model
    }
