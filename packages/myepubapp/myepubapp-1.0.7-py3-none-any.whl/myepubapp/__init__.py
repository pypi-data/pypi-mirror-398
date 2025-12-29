"""
MyEPUBApp
=========
A modular EPUB generator that converts text files to EPUB format.
"""

from .core.book import Book
from .core.chapter import Chapter
from .core.metadata import Metadata
from .generators.content import ContentGenerator
from .utils.logger import setup_logger

# Setup default logger
logger = setup_logger()

__version__ = "1.0.7"
__author__ = "MyEPUBApp Developer"
