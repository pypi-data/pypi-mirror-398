from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict




class GluonConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    provider: str = Field(default="openai", description="AI provider to use")
    model: str = Field(default="gpt-5-mini", description="AI model to use")
    temperature: float = Field(default=0.3, ge=0.0, le=0.5, description="AI model temperature")
    max_tokens: int = Field(default=4000, ge=0, le=8000, description="Maximum tokens for AI response")


