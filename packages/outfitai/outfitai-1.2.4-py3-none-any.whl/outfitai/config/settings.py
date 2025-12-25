from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, FieldValidationInfo


class Settings(BaseSettings):
    # API Configuration
    OUTFITAI_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # OpenAI specific settings
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 300

    # Gemini specific settings
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Common settings
    BATCH_SIZE: int = 10
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator('OUTFITAI_PROVIDER')
    @classmethod
    def validate_provider(cls, v: str, info: FieldValidationInfo) -> str:
        if v == '':
            return 'openai'
        if v not in ['openai', 'gemini']:
            raise ValueError(
                'OUTFITAI_PROVIDER must be either "openai" or "gemini"')
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_api_keys()

    def _validate_api_keys(self):
        """Validate that the appropriate API key is available."""
        if self.OUTFITAI_PROVIDER == 'openai' and not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY must be provided when using OpenAI provider"
            )
        elif self.OUTFITAI_PROVIDER == 'gemini' and not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY must be provided when using Gemini provider"
            )

    @classmethod
    def from_dict(cls, settings_dict: dict) -> 'Settings':
        """Create Settings instance from dictionary."""
        return cls(**settings_dict)
