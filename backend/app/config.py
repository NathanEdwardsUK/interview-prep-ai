from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/interview_prep"
    
    # Clerk Authentication
    CLERK_SECRET_KEY: str = ""
    
    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"
    USE_STUB_LLM: bool = False  # Use stub client for testing
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # OpenAI specific
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Anthropic specific
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Application
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS if isinstance(self.CORS_ORIGINS, list) else ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
