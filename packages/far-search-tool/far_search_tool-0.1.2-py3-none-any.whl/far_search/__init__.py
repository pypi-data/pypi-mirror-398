"""
FAR Search Tool for LangChain

A LangChain tool for semantic search over Federal Acquisition Regulations (FAR).
"""

from far_search.tool import FARSearchTool
from far_search.exceptions import FARSearchError, FARAPIError, FARRateLimitError

__version__ = "0.1.2"
__all__ = ["FARSearchTool", "FARSearchError", "FARAPIError", "FARRateLimitError"]

