from abc import ABC, abstractmethod
from typing import Dict, List, Any, Union
from pathlib import Path
import asyncio

from ..error.exceptions import ValidationError
from ..config.settings import Settings
from ..utils.logger import Logger
from ..utils.image_processor import ImageProcessor, ImageSource


class BaseClassifier(ABC):
    """Base class for all image classifiers."""

    def __init__(self, settings: Settings):
        """
        Initialize the base classifier.

        Args:
            settings: Settings instance containing configuration
        """
        self.settings = settings
        logger_manager = Logger(self.settings)
        self.logger = logger_manager.setup_logger(__name__)
        self.image_processor = ImageProcessor(self.settings)
        self._init_constants()

    def _init_constants(self):
        """Initialize constant values used in classification."""
        self.color_values = [
            "white", "gray", "black", "red", "orange",
            "yellow", "green", "blue", "indigo", "purple", "other"
        ]
        self.category_values = [
            "tops", "bottoms", "outerwear", "dresses",
            "shoes", "bags", "hats", "accessories", "other"
        ]
        self.dress_code_values = [
            "casual wear", "business attire", "campus style", "date night outfit",
            "travel wear", "wedding attire", "loungewear", "resort wear", "other"
        ]
        self.season_values = ["spring", "summer", "fall", "winter"]

    def _create_prompt(self) -> str:
        """Create the prompt for the API."""
        return f"""
        Analyze the clothing item in the image and classify it according to these rules.
        Return a JSON object with these keys:
        - 'color': 1 value from {self.color_values}
        - 'category': 1 value from {self.category_values}
        - 'dress_code': 1 value from {self.dress_code_values}
        - 'season': 1+ values from {self.season_values} (array)
        """

    def _validate_response(self, data: Dict[str, Any]) -> None:
        """
        Validate the API response format and values.

        Args:
            data: Response data to validate

        Raises:
            ValidationError: If the response format is invalid
        """
        required_keys = ["color", "category", "dress_code", "season"]

        # Check required keys
        for key in required_keys:
            if key not in data:
                raise ValidationError(f"Missing required key: {key}")

        # Validate color
        if data["color"] not in self.color_values:
            raise ValidationError(f"Invalid category: {data['color']}")

        # Validate category
        if data["category"] not in self.category_values:
            raise ValidationError(f"Invalid category: {data['category']}")

        # Validate dress_code
        if data["dress_code"] not in self.dress_code_values:
            raise ValidationError(f"Invalid dress_code: {data['dress_code']}")

        # Validate seasons
        if not isinstance(data["season"], list):
            raise ValidationError("Season must be a list")

        for season in data["season"]:
            if season not in self.season_values:
                raise ValidationError(f"Invalid season: {season}")

    @abstractmethod
    async def classify_single(self, image_source: Union[str, ImageSource]) -> Dict[str, Any]:
        """
        Classify a single clothing item.

        Args:
            image_source: Path to the image file

        Returns:
            Dictionary containing classification results
        """
        pass

    async def classify_batch(
        self,
        image_paths: Union[str, Path, List[Union[str, Path]]],
        batch_size: int = None
    ) -> List[Dict[str, Any]]:
        """
        Classify multiple clothing items in batches.

        Args:
            image_paths: Directory path or list of image paths
            batch_size: Optional batch size for processing

        Returns:
            List of dictionaries containing classification results
        """
        batch_size = batch_size or self.settings.BATCH_SIZE

        # Handle directory input
        if isinstance(image_paths, (str, Path)):
            path = Path(image_paths)
            if path.is_dir():
                image_paths = [
                    p for p in path.glob("*")
                    if p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', 'gif']
                ]
            else:
                raise ValueError(
                    "When providing a single path, it must be a directory")

        image_paths = [str(path) for path in image_paths]
        results = []

        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]
            tasks = [self.classify_single(path) for path in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Error in batch processing: {str(result)}")
                    results.append({"error": str(result)})
                else:
                    results.append(result)

        return results
