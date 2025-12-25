from typing import Union, Dict, Type
from ..config.settings import Settings
from .base import BaseClassifier
from .openai_classifier import OpenAIClassifier
from .gemini_classifier import GeminiClassifier
from ..error.exceptions import ClothingClassifierError


class ClassifierFactory:
    """Factory class for creating classifier instances."""

    _classifiers: Dict[str, Type[BaseClassifier]] = {
        'openai': OpenAIClassifier,
        'gemini': GeminiClassifier
    }

    @classmethod
    def create_classifier(
        cls,
        settings: Union[Settings, dict, None] = None
    ) -> BaseClassifier:
        """
        Create and return appropriate classifier instance based on settings.

        Args:
            settings: Settings instance or dictionary containing configuration
                     If None, default Settings will be used

        Returns:
            Instance of appropriate classifier (OpenAI or Gemini)

        Raises:
            ClothingClassifierError: If provider is invalid or initialization fails
        """
        try:
            # Handle different types of settings input
            if isinstance(settings, dict):
                settings = Settings.from_dict(settings)
            elif settings is None:
                settings = Settings()
            elif not isinstance(settings, Settings):
                raise ValueError(
                    "settings must be dict, Settings instance, or None")

            # Get the appropriate classifier class
            classifier_class = cls._classifiers.get(
                settings.OUTFITAI_PROVIDER.lower())
            if not classifier_class:
                raise ValueError(
                    f"Invalid API provider: {settings.OUTFITAI_PROVIDER}. "
                    f"Must be one of: {', '.join(cls._classifiers.keys())}"
                )

            # Create and return classifier instance
            return classifier_class(settings)

        except Exception as e:
            raise ClothingClassifierError(
                f"Failed to create classifier: {str(e)}"
            ) from e
