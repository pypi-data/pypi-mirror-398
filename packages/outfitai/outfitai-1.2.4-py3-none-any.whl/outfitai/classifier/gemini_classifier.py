from google import genai
import json
from typing import Dict, Any, Optional, Union
import re
from ..utils.image_processor import ImageSource
from ..error.exceptions import APIError
from .base import BaseClassifier
from ..config.settings import Settings


class GeminiClassifier(BaseClassifier):
    def __init__(self, settings: Optional[Union[Settings, dict]] = None):
        """
        Initialize Gemini classifier with optional settings.

        Args:
            settings: Optional Settings instance or dictionary of settings
        """
        try:
            if isinstance(settings, dict):
                settings = Settings.from_dict(settings)
            elif settings is None:
                settings = Settings()

            super().__init__(settings)
            self.client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            self.prompt_text = self._create_prompt()

        except ValueError as e:
            raise ValueError(str(e)) from e

    async def classify_single(self, image_source: Union[str, ImageSource]) -> Dict[str, Any]:
        """
        Classify a single clothing item using Gemini Vision API.

        Args:
            image_source: Path to the image file

        Returns:
            Dictionary containing classification results
        """
        try:
            image_part = await self.image_processor.process_image(image_source)

            response = self.client.models.generate_content(
                model=self.settings.GEMINI_MODEL,
                contents=[
                    self.prompt_text,
                    image_part
                ],
                config={
                    'response_mime_type': 'application/json',
                },
            )

            result = json.loads(response.text)
            self._validate_response(result)

            return {
                "image_path": str(image_source.path if isinstance(image_source, ImageSource) else image_source),
                **result
            }

        except Exception as e:
            raise APIError(f"Error classifying image with Gemini: {str(e)}")

    @classmethod
    def create(cls, settings_dict: dict) -> 'GeminiClassifier':
        """
        Create a classifier instance from a dictionary of settings.

        Args:
            settings_dict: Dictionary containing settings

        Returns:
            GeminiClassifier instance
        """
        return cls(settings=settings_dict)
