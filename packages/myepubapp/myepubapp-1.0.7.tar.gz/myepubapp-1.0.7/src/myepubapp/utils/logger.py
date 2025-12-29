import logging
import os
from pathlib import Path
from typing import Optional


def setup_logger(name: Optional[str] = None, debug: bool = False) -> logging.Logger:
    """Setup and return logger instance"""

    logger = logging.getLogger(name or __name__)

    # If logger already has handlers, return it directly
    if logger.handlers:
        return logger

    # Set log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler - use user directory instead of project directory
    try:
        # Get user application data directory
        if os.name == "nt":  # Windows
            app_data = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
            log_dir = Path(app_data) / "myepubapp" / "logs"
        else:  # Unix-like systems (Linux, macOS)
            log_dir = Path.home() / ".local" / "share" / "myepubapp" / "logs"

        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "myepubapp.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except (OSError, PermissionError) as e:
        # If unable to create log file, use console logging only
        logger.warning(f"Unable to create log file, using console logging only: {e}")

    # Set log level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger
