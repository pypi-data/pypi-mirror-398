import logging
import sys
from typing import Optional
from pathlib import Path
from ..config.settings import Settings


class Logger:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def setup_logger(self, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """Configure and return a logger instance."""
        logger = logging.getLogger(name)

        if logger.hasHandlers():
            return logger

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if log_file is specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.setLevel(self.settings.LOG_LEVEL)
        return logger
