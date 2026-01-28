from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/interview_prep"
    
    # Clerk Authentication
    CLERK_SECRET_KEY: str
    
    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # OpenAI specific
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Anthropic specific
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Application
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
