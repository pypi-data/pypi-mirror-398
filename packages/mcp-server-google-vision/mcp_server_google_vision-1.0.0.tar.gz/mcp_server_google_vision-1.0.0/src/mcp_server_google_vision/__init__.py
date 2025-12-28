"""
MCP Server Google Vision - OCR capabilities for LLMs via Google Cloud Vision API

Developed by Kohen Avocats (https://kohenavocats.com)
Author: Maître Hassan KOHEN, avocat pénaliste à Paris
"""

__version__ = "1.0.0"
__author__ = "Hassan Kohen"
__email__ = "contact@kohenavocats.com"

from .server import mcp, analyze_image, analyze_pdf

__all__ = ["mcp", "analyze_image", "analyze_pdf", "__version__"]
