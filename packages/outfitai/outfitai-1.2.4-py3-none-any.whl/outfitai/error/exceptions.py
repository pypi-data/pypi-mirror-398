class ClothingClassifierError(Exception):
    """Base exception for the clothing classifier."""
    pass


class ImageProcessingError(ClothingClassifierError):
    """Raised when there's an error processing an image."""
    pass


class APIError(ClothingClassifierError):
    """Raised when there's an error with the OpenAI API."""
    pass


class ValidationError(ClothingClassifierError):
    """Raised when there's an error validating the response."""
    pass
