# __init__.py
"""
EPUB to Text/Markdown Converter

A professional tool for converting EPUB files to various formats with advanced features:
- Single file or batch processing
- Multiple output formats (text, markdown, JSON)
- Image extraction and linking
- Chapter-wise splitting
- Recursive directory scanning
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .reader import EpubReader
from .extractor import EpubExtractor
from .converter import ContentConverter
from .processor import EpubProcessor
from .batch_processor import BatchProcessor

# For backward compatibility
from .wrapper import EpubContentFeedAI

__all__ = [
    'EpubReader',
    'EpubExtractor', 
    'ContentConverter',
    'EpubProcessor',
    'BatchProcessor',
    'EpubContentFeedAI'  # Legacy class
]