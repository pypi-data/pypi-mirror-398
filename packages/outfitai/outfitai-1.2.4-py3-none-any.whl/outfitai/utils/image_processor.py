from PIL import Image, UnidentifiedImageError, ImageFile
from pathlib import Path
import base64
from typing import Optional, Union
from functools import lru_cache
from enum import Enum
from dataclasses import dataclass
import aiohttp
from urllib.parse import urlparse
from google.genai import types
from ..error.exceptions import ImageProcessingError
from ..config.settings import Settings
from .logger import Logger


class ImageSourceType(Enum):
    LOCAL = "local"
    URL = "url"


@dataclass
class ImageSource:
    type: ImageSourceType
    path: str


class ImageProcessor:
    SUPPORTED_EXTENSIONS = {".png", ".jpeg", ".jpg", ".webp", ".gif"}

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.logger = Logger(self.settings).setup_logger(__name__)

    async def process_image(self, image_source: Union[str, ImageSource]) -> Union[str, types.Part]:
        """
        Process image from either local path or URL.
        Returns:
        - For OpenAI: URL string or base64 encoded string
        - For Gemini: types.Part object containing image bytes
        """
        # Convert string input to ImageSource
        if isinstance(image_source, str):
            source_type = ImageSourceType.URL if self._is_url(
                image_source) else ImageSourceType.LOCAL
            image_source = ImageSource(type=source_type, path=image_source)

        # Validate source
        await self._validate_source(image_source)

        if self.settings.OUTFITAI_PROVIDER == "openai":
            return await self._process_for_openai(image_source)
        else:
            return await self._process_for_gemini(image_source)

    async def _process_for_openai(self, source: ImageSource) -> str:
        """Process image for OpenAI API"""
        if source.type == ImageSourceType.URL:
            return source.path
        else:
            return f"data:image/jpeg;base64,{self._encode_image(source.path)}"

    async def _process_for_gemini(self, source: ImageSource) -> types.Part:
        """Process image for Gemini API"""
        if source.type == ImageSourceType.LOCAL:
            with open(source.path, 'rb') as image_file:
                image_bytes = image_file.read()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.path) as response:
                    if response.status != 200:
                        raise ImageProcessingError(
                            f"Failed to fetch image from URL: {source.path}")
                    image_bytes = await response.read()

        # Detect mime type from path
        extension = Path(source.path).suffix.lower()
        mime_type = f"image/{extension[1:]}" if extension != '.jpg' else "image/jpeg"

        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    async def _validate_source(self, source: ImageSource) -> None:
        """Validate image source"""
        if source.type == ImageSourceType.LOCAL:
            self._check_image_file(source.path)
        else:
            await self._validate_url(source.path)

    async def _validate_url(self, url: str) -> None:
        """Validate URL and check if it points to a supported image"""
        if not self._is_url(url):
            raise ImageProcessingError("Invalid URL format")

        # Check file extension from URL
        path = urlparse(url).path
        ext = Path(path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ImageProcessingError(
                f"Unsupported file extension in URL: {ext}")

        # Validate URL accessibility
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as response:
                    if response.status != 200:
                        raise ImageProcessingError(
                            f"Failed to access URL: {url}")

                    # Verify content type
                    content_type = response.headers.get("content-type", "")
                    if not content_type.startswith("image/"):
                        raise ImageProcessingError(
                            f"URL does not point to an image: {url}")
            except aiohttp.ClientError as e:
                raise ImageProcessingError(f"Failed to validate URL: {str(e)}")

    @staticmethod
    def _is_url(path: str) -> bool:
        """Check if path is a URL"""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _check_image_file(self, image_path: Union[str, Path]) -> None:
        """
        Validates if the image file is supported and can be processed.

        Args:
            image_path: Path to the image file

        Raises:
            ImageProcessingError: If image validation fails
        """
        image_path = Path(image_path)
        if not self._is_supported_extension(image_path):
            raise ImageProcessingError("File extension not supported")

        if self._is_animated_gif(image_path):
            raise ImageProcessingError("Animated GIF not supported")

        try:
            self._load_image(image_path)
        except Exception as e:
            if isinstance(e, UnidentifiedImageError):
                raise ImageProcessingError("Failed to identify image file")
            raise ImageProcessingError(f"Failed to process image: {str(e)}")

    def _encode_image(self, image_path: str) -> str:
        """Encode local image file to base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            raise ImageProcessingError(f"Failed to encode image: {str(e)}")

    @lru_cache(maxsize=10)
    def _load_image(self, image_path: Union[str, Path]) -> ImageFile:
        """
        Loads and returns a copy of the image with caching.

        Args:
            image_path: Path to the image file

        Returns:
            Copy of the loaded image

        Raises:
            ImageProcessingError: If image loading fails
        """
        try:
            with Image.open(image_path) as img:
                return img.copy()
        except Exception as e:
            raise ImageProcessingError(f"Failed to load image: {str(e)}")

    def _is_supported_extension(self, image_path: Path) -> bool:
        """Checks if the image file extension is supported."""
        extension = image_path.suffix.lower()
        if extension == ".gif" and not self.settings.OUTFITAI_PROVIDER == "openai":
            return False
        return extension in self.SUPPORTED_EXTENSIONS

    def _is_animated_gif(self, image_path: Path) -> bool:
        """Checks if the GIF image is animated."""
        if image_path.suffix.lower() != '.gif':
            return False

        try:
            img = self._load_image(image_path)
            try:
                img.seek(1)
                return True
            except EOFError:
                return False
        except Exception as e:
            raise ImageProcessingError(
                f"Error checking GIF animation: {str(e)}")
