import openai
import json
from typing import Dict, Any, Optional, Union
from ..utils.image_processor import ImageSource
from ..error.exceptions import APIError
from .base import BaseClassifier
from ..config.settings import Settings


class OpenAIClassifier(BaseClassifier):
    def __init__(self, settings: Optional[Union[Settings, dict]] = None):
        """
        Initialize OpenAI classifier with optional settings.

        Args:
            settings: Optional Settings instance or dictionary of settings
        """
        try:
            if isinstance(settings, dict):
                settings = Settings.from_dict(settings)
            elif settings is None:
                settings = Settings()

            super().__init__(settings)
            self.client = openai.AsyncOpenAI(
                api_key=self.settings.OPENAI_API_KEY)
            self.prompt_text = self._create_prompt()

        except ValueError as e:
            raise ValueError(str(e)) from e

    async def classify_single(self, image_source: Union[str, ImageSource]) -> Dict[str, Any]:
        """
        Classify a single clothing item.

        Args:
            image_source: Path to the image file

        Returns:
            Dictionary containing classification results
        """
        try:
            image_data = await self.image_processor.process_image(image_source)

            response = await self.client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data,  # URL or base64 data URL
                                "detail": "low"
                            }
                        }
                    ]
                }],
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            self._validate_response(result)

            return {
                "image_path": str(image_source.path if isinstance(image_source, ImageSource) else image_source),
                **result
            }

        except Exception as e:
            raise APIError(f"Error classifying image: {str(e)}")

    @classmethod
    def create(cls, settings_dict: dict) -> 'OpenAIClassifier':
        """
        Create a classifier instance from a dictionary of settings.

        Args:
            settings_dict: Dictionary containing settings

        Returns:
            OpenAIClassifier instance
        """
        return cls(settings=settings_dict)
