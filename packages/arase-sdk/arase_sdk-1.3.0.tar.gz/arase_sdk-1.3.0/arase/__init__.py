"""
ARASE SDK - Official Python SDK
حزمة اريز - مكتبة Python الرسمية

The official SDK for integrating ARASE Search API into your Python applications.
الحزمة الرسمية لدمج واجهة برمجة تطبيقات اريز للبحث في تطبيقات Python.

Example | مثال:
    >>> from arase import AraseClient
    >>> client = AraseClient()  # Reads from ARASE_API_KEY env var
    >>> results = client.search("What is Saudi Vision 2030?")
    >>> print(results.answer)

See https://arase.masarat.sa/docs for full documentation.
"""

from .client import AraseClient, AraseAPIError
from .types import (
    SearchOptions,
    SearchResponse,
    SearchResult,
    ImageResult,
    VideoResult,
    NewsResult,
    PlaceResult,
    ShoppingResult,
    ScholarResult,
    StockResult,
    StocksResponse,
    WeatherForecast,
    WeatherResponse,
    ExtractOptions,
    ExtractResponse,
)

__version__ = "1.3.0"
__author__ = "MASARAT SA"
__email__ = "dev@masarat.sa"
__url__ = "https://arase.masarat.sa"

__all__ = [
    # Main client | العميل الرئيسي
    "AraseClient",
    "AraseAPIError",
    # Search types | أنواع البحث
    "SearchOptions",
    "SearchResponse",
    "SearchResult",
    "ImageResult",
    "VideoResult",
    "NewsResult",
    "PlaceResult",
    "ShoppingResult",
    "ScholarResult",
    "StockResult",
    "StocksResponse",
    "WeatherForecast",
    "WeatherResponse",
    # Extract types | أنواع الاستخراج
    "ExtractOptions",
    "ExtractResponse",
]
