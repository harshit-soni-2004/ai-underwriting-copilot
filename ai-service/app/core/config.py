from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "ai-service"
    service_port: int = 8000
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    embedding_provider: str = "gemini"
    embedding_model: str = "text-embedding-004"
    core_service_url: str = "http://localhost:8080"
    extraction_confidence_threshold: float = 0.85
    retrieval_mode: str = "hybrid_rrf"
    chunking_strategy: str = "heading_aware"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
