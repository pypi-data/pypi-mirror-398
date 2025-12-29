"""
ARASE Client
العميل الرئيسي لـ ARASE API

The main client for interacting with ARASE Search API.
العميل الرئيسي للتفاعل مع واجهة برمجة تطبيقات اريز للبحث.
"""

import os
import httpx
from typing import Optional, Dict, Any, List

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
    ResponseMeta,
    CreditsInfo,
)


DEFAULT_BASE_URL = "https://arase.masarat.sa/v1"
DEFAULT_TIMEOUT = 30.0


class AraseAPIError(Exception):
    """
    ARASE API Error class.
    فئة خطأ واجهة برمجة تطبيقات اريز.
    
    Raised when an API request fails.
    يتم طرحها عند فشل طلب API.
    
    Attributes:
        message: Error message | رسالة الخطأ
        code: Error code | رمز الخطأ
        status: HTTP status code | رمز حالة HTTP
    
    Example | مثال:
        >>> try:
        ...     results = client.search("query")
        ... except AraseAPIError as e:
        ...     print(f"Error {e.code}: {e.message}")
    """
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", status: int = 0):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(f"{code}: {message}")


class AraseClient:
    """
    ARASE API Client.
    عميل واجهة برمجة تطبيقات اريز.
    
    The main client for interacting with ARASE Search API.
    العميل الرئيسي للتفاعل مع واجهة برمجة تطبيقات اريز للبحث.
    
    Args:
        api_key: Your ARASE API key. If not provided, reads from ARASE_API_KEY env var.
                 مفتاح API الخاص بك. إذا لم يتم توفيره، يقرأ من متغير البيئة ARASE_API_KEY.
        base_url: Custom API base URL (optional).
                  رابط API مخصص (اختياري).
        timeout: Request timeout in seconds (default: 30).
                 مهلة الطلب بالثواني (افتراضي: 30).
    
    Example | مثال:
        >>> # Option 1: Use environment variable (recommended)
        >>> # الخيار 1: استخدام متغير البيئة (مستحسن)
        >>> client = AraseClient()
        >>> 
        >>> # Option 2: Pass API key directly
        >>> # الخيار 2: تمرير مفتاح API مباشرة
        >>> client = AraseClient(api_key="arase_YOUR_API_KEY")
        >>> 
        >>> # Search the web | البحث في الويب
        >>> results = client.search("What is Saudi Vision 2030?")
        >>> print(results.answer)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        # Get API key from parameter or environment variable
        # الحصول على مفتاح API من المعامل أو متغير البيئة
        self.api_key = api_key or os.environ.get("ARASE_API_KEY")
        
        if not self.api_key:
            raise AraseAPIError(
                "API key is required. Pass it as a parameter or set ARASE_API_KEY environment variable.\n"
                "مفتاح API مطلوب. قم بتمريره كمعامل أو قم بتعيين متغير البيئة ARASE_API_KEY.",
                code="MISSING_API_KEY",
                status=401,
            )
        
        self.base_url = base_url or os.environ.get("ARASE_BASE_URL", DEFAULT_BASE_URL)
        self.timeout = timeout
        
        # Create HTTP client | إنشاء عميل HTTP
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """
        Close the HTTP client.
        إغلاق عميل HTTP.
        """
        self._client.close()
    
    def _request(self, endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal HTTP request method.
        طريقة طلب HTTP الداخلية.
        """
        try:
            response = self._client.post(endpoint, json=body)
            
            if not response.is_success:
                try:
                    error_data = response.json()
                    raise AraseAPIError(
                        message=error_data.get("message", f"HTTP {response.status_code}"),
                        code=error_data.get("code", "UNKNOWN_ERROR"),
                        status=response.status_code,
                    )
                except (ValueError, KeyError):
                    raise AraseAPIError(
                        message=f"HTTP {response.status_code}",
                        code="HTTP_ERROR",
                        status=response.status_code,
                    )
            
            return response.json()
            
        except httpx.TimeoutException:
            raise AraseAPIError(
                "Request timeout | انتهت مهلة الطلب",
                code="TIMEOUT",
                status=408,
            )
        except httpx.RequestError as e:
            raise AraseAPIError(
                f"Network error: {str(e)} | خطأ في الشبكة",
                code="NETWORK_ERROR",
                status=0,
            )
    
    def _parse_search_response(self, data: Dict[str, Any]) -> SearchResponse:
        """
        Parse API response into SearchResponse object.
        تحويل استجابة API إلى كائن SearchResponse.
        """
        # Parse results | تحليل النتائج
        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score"),
                published_date=r.get("publishedDate"),
                source=r.get("source"),
                raw_content=r.get("rawContent"),
            )
            for r in data.get("results", [])
        ]
        
        # Parse images | تحليل الصور
        images = None
        if data.get("images"):
            images = [
                ImageResult(
                    title=i.get("title", ""),
                    image_url=i.get("imageUrl", ""),
                    thumbnail_url=i.get("thumbnailUrl", ""),
                    source_url=i.get("sourceUrl"),
                    width=i.get("width"),
                    height=i.get("height"),
                )
                for i in data["images"]
            ]
        
        # Parse videos | تحليل الفيديوهات
        videos = None
        if data.get("videos"):
            videos = [
                VideoResult(
                    title=v.get("title", ""),
                    url=v.get("url", ""),
                    thumbnail_url=v.get("thumbnailUrl", ""),
                    duration=v.get("duration"),
                    platform=v.get("platform"),
                    channel=v.get("channel"),
                    views=v.get("views"),
                    description=v.get("description"),
                )
                for v in data["videos"]
            ]
        
        # Parse news | تحليل الأخبار
        news = None
        if data.get("news"):
            news = [
                NewsResult(
                    title=n.get("title", ""),
                    url=n.get("url", ""),
                    content=n.get("content", ""),
                    source=n.get("source"),
                    published_date=n.get("publishedDate"),
                    image_url=n.get("imageUrl"),
                )
                for n in data["news"]
            ]
        
        # Parse places | تحليل الأماكن
        places = None
        if data.get("places"):
            places = [
                PlaceResult(
                    title=p.get("title", ""),
                    address=p.get("address", ""),
                    latitude=p.get("latitude"),
                    longitude=p.get("longitude"),
                    rating=p.get("rating"),
                    rating_count=p.get("ratingCount"),
                    type=p.get("type"),
                    phone=p.get("phone"),
                    website=p.get("website"),
                    hours=p.get("hours"),
                )
                for p in data["places"]
            ]
        
        # Parse shopping | تحليل التسوق
        shopping = None
        if data.get("shopping"):
            shopping = [
                ShoppingResult(
                    title=s.get("title", ""),
                    url=s.get("url", ""),
                    price=s.get("price"),
                    source=s.get("source"),
                    image_url=s.get("imageUrl"),
                    rating=s.get("rating"),
                )
                for s in data["shopping"]
            ]
        
        # Parse scholar | تحليل الأبحاث
        scholar = None
        if data.get("scholar"):
            scholar = [
                ScholarResult(
                    title=sc.get("title", ""),
                    url=sc.get("url", ""),
                    snippet=sc.get("snippet"),
                    authors=sc.get("authors"),
                    year=sc.get("year"),
                    citations=sc.get("citations"),
                )
                for sc in data["scholar"]
            ]
        
        # Parse stocks | تحليل الأسهم
        stocks = None
        if data.get("stocks"):
            stocks_data = data["stocks"]
            stock_results = [
                StockResult(
                    symbol=s.get("symbol", ""),
                    name=s.get("name", ""),
                    price=s.get("price", 0.0),
                    currency=s.get("currency", "SAR"),
                    change=s.get("change", 0.0),
                    change_percent=s.get("changePercent", 0.0),
                    volume=s.get("volume"),
                )
                for s in stocks_data.get("results", [])
            ]
            stocks = StocksResponse(
                results=stock_results,
                query_intent=stocks_data.get("queryIntent"),
                market=stocks_data.get("market"),
                summary=stocks_data.get("summary"),
            )
        
        # Parse weather | تحليل الطقس
        weather = None
        if data.get("weather"):
            weather_data = data["weather"]
            forecast = [
                WeatherForecast(
                    date=f.get("date", ""),
                    maxtemp_c=f.get("maxtempC", 0.0),
                    mintemp_c=f.get("mintempC", 0.0),
                    condition=f.get("condition", ""),
                )
                for f in weather_data.get("forecast", [])
            ]
            weather = WeatherResponse(
                location=weather_data.get("location", {}),
                current=weather_data.get("current", {}),
                forecast=forecast,
                summary=weather_data.get("summary"),
                advice=weather_data.get("advice"),
            )
        
        # Parse meta | تحليل البيانات الوصفية
        meta = None
        if data.get("meta"):
            meta_data = data["meta"]
            credits = None
            if meta_data.get("credits"):
                credits = CreditsInfo(
                    cost=meta_data["credits"].get("cost", 0),
                    remaining=meta_data["credits"].get("remaining", 0),
                )
            meta = ResponseMeta(
                response_time=meta_data.get("responseTime", 0),
                credits=credits,
            )
        
        return SearchResponse(
            query=data.get("query", ""),
            results=results,
            answer=data.get("answer"),
            images=images,
            videos=videos,
            news=news,
            maps=places,  # maps and places are the same
            places=places,
            shopping=shopping,
            scholar=scholar,
            stocks=stocks,
            weather=weather,
            meta=meta,
        )
    
    def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None,
        **kwargs,
    ) -> SearchResponse:
        """
        Search the web using ARASE AI.
        البحث في الويب باستخدام اريز AI.
        
        Args:
            query: The search query | استعلام البحث
            options: Search options | خيارات البحث
            **kwargs: Additional options as keyword arguments | خيارات إضافية
        
        Returns:
            SearchResponse: Search results | نتائج البحث
        
        Example | مثال:
            >>> # Simple search | بحث بسيط
            >>> results = client.search("What is Saudi Vision 2030?")
            >>> results = client.search("ما هي رؤية السعودية 2030؟")
            >>> 
            >>> # Advanced search | بحث متقدم
            >>> results = client.search(
            ...     "Best restaurants in Riyadh",
            ...     options=SearchOptions(
            ...         include_answer=True,
            ...         include_places=True,
            ...         max_results=10,
            ...     )
            ... )
            >>> 
            >>> # Or use keyword arguments | أو استخدم الكلمات المفتاحية
            >>> results = client.search(
            ...     "أفضل المطاعم في الرياض",
            ...     include_answer=True,
            ...     include_places=True,
            ... )
        """
        opts = options or SearchOptions()
        
        # Override with kwargs | تجاوز بالكلمات المفتاحية
        for key, value in kwargs.items():
            if hasattr(opts, key):
                setattr(opts, key, value)
        
        body = {
            "query": query,
            "search_depth": opts.search_depth,
            "max_results": opts.max_results,
            "include_answer": opts.include_answer,
            "include_raw_content": opts.include_raw_content,
            "include_images": opts.include_images,
            "include_videos": opts.include_videos,
            "include_news": opts.include_news,
            "include_maps": opts.include_maps,
            "include_places": opts.include_places,
            "include_shopping": opts.include_shopping,
            "include_scholar": opts.include_scholar,
            "include_stocks": opts.include_stocks,
            "include_weather": opts.include_weather,
            "topic": opts.topic,
        }
        
        if opts.max_steps:
            body["max_steps"] = opts.max_steps
        if opts.user_location:
            body["user_location"] = opts.user_location
        if opts.options:
            body["options"] = opts.options
        
        data = self._request("/search", body)
        return self._parse_search_response(data)
    
    def extract(
        self,
        url: str,
        options: Optional[ExtractOptions] = None,
        **kwargs,
    ) -> ExtractResponse:
        """
        Extract content from a webpage.
        استخراج محتوى من صفحة ويب.
        
        Args:
            url: The URL to extract from | الرابط للاستخراج منه
            options: Extract options | خيارات الاستخراج
            **kwargs: Additional options | خيارات إضافية
        
        Returns:
            ExtractResponse: Extracted content | المحتوى المستخرج
        
        Example | مثال:
            >>> content = client.extract("https://example.com/article")
            >>> print(content.content)
            >>> 
            >>> # With summary | مع تلخيص
            >>> content = client.extract(
            ...     "https://example.com/article",
            ...     include_summary=True,
            ... )
            >>> print(content.summary)
        """
        opts = options or ExtractOptions()
        
        for key, value in kwargs.items():
            if hasattr(opts, key):
                setattr(opts, key, value)
        
        body = {
            "mode": "extract",
            "url": url,
            "include_summary": opts.include_summary,
        }
        
        data = self._request("/search", body)
        
        # Parse meta | تحليل البيانات الوصفية
        meta = None
        if data.get("meta"):
            meta_data = data["meta"]
            credits = None
            if meta_data.get("credits"):
                credits = CreditsInfo(
                    cost=meta_data["credits"].get("cost", 0),
                    remaining=meta_data["credits"].get("remaining", 0),
                )
            meta = ResponseMeta(
                response_time=meta_data.get("responseTime", 0),
                credits=credits,
            )
        
        return ExtractResponse(
            url=data.get("url", url),
            content=data.get("content", ""),
            success=data.get("success", True),
            summary=data.get("summary"),
            meta=meta,
        )
    
    def search_images(self, query: str, max_results: int = 10) -> SearchResponse:
        """
        Search for images.
        البحث عن الصور.
        
        Args:
            query: Search query | استعلام البحث
            max_results: Maximum results (default: 10) | الحد الأقصى للنتائج
        
        Returns:
            SearchResponse: Results with images | نتائج مع صور
        """
        return self.search(query, include_images=True, max_results=max_results)
    
    def search_videos(self, query: str, max_results: int = 10) -> SearchResponse:
        """
        Search for videos.
        البحث عن الفيديوهات.
        
        Args:
            query: Search query | استعلام البحث
            max_results: Maximum results (default: 10) | الحد الأقصى للنتائج
        
        Returns:
            SearchResponse: Results with videos | نتائج مع فيديوهات
        """
        return self.search(query, include_videos=True, max_results=max_results)
    
    def search_news(self, query: str, max_results: int = 10) -> SearchResponse:
        """
        Search for news articles.
        البحث عن المقالات الإخبارية.
        
        Args:
            query: Search query | استعلام البحث
            max_results: Maximum results (default: 10) | الحد الأقصى للنتائج
        
        Returns:
            SearchResponse: Results with news | نتائج مع أخبار
        """
        return self.search(query, include_news=True, max_results=max_results)
    
    def search_places(
        self,
        query: str,
        max_results: int = 10,
        user_location: Optional[Dict[str, float]] = None,
    ) -> SearchResponse:
        """
        Search for places and locations.
        البحث عن الأماكن والمواقع.
        
        Args:
            query: Search query | استعلام البحث
            max_results: Maximum results (default: 10) | الحد الأقصى للنتائج
            user_location: User's location {"lat": float, "lng": float} | موقع المستخدم
        
        Returns:
            SearchResponse: Results with places | نتائج مع أماكن
        
        Example | مثال:
            >>> # Search near Riyadh | البحث قرب الرياض
            >>> places = client.search_places(
            ...     "restaurants",
            ...     user_location={"lat": 24.7136, "lng": 46.6753}
            ... )
        """
        opts = SearchOptions(
            include_places=True,
            max_results=max_results,
            user_location=user_location,
        )
        return self.search(query, options=opts)
    
    def search_scholar(self, query: str, max_results: int = 10) -> SearchResponse:
        """
        Search for academic papers and research.
        البحث عن الأوراق الأكاديمية والأبحاث.
        
        Args:
            query: Search query | استعلام البحث
            max_results: Maximum results (default: 10) | الحد الأقصى للنتائج
        
        Returns:
            SearchResponse: Results with academic papers | نتائج مع أوراق أكاديمية
        """
        return self.search(
            query,
            include_scholar=True,
            topic="academic",
            max_results=max_results,
        )


# Async client for asyncio support | عميل غير متزامن لدعم asyncio
class AsyncAraseClient:
    """
    Async ARASE API Client.
    عميل واجهة برمجة تطبيقات اريز غير المتزامن.
    
    Same as AraseClient but with async/await support.
    نفس AraseClient ولكن مع دعم async/await.
    
    Example | مثال:
        >>> async with AsyncAraseClient() as client:
        ...     results = await client.search("query")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.environ.get("ARASE_API_KEY")
        
        if not self.api_key:
            raise AraseAPIError(
                "API key is required. Pass it as a parameter or set ARASE_API_KEY environment variable.\n"
                "مفتاح API مطلوب. قم بتمريره كمعامل أو قم بتعيين متغير البيئة ARASE_API_KEY.",
                code="MISSING_API_KEY",
                status=401,
            )
        
        self.base_url = base_url or os.environ.get("ARASE_BASE_URL", DEFAULT_BASE_URL)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def _request(self, endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if not self._client:
            raise AraseAPIError(
                "Client not initialized. Use 'async with AsyncAraseClient() as client:'",
                code="CLIENT_NOT_INITIALIZED",
            )
        
        try:
            response = await self._client.post(endpoint, json=body)
            
            if not response.is_success:
                try:
                    error_data = response.json()
                    raise AraseAPIError(
                        message=error_data.get("message", f"HTTP {response.status_code}"),
                        code=error_data.get("code", "UNKNOWN_ERROR"),
                        status=response.status_code,
                    )
                except (ValueError, KeyError):
                    raise AraseAPIError(
                        message=f"HTTP {response.status_code}",
                        code="HTTP_ERROR",
                        status=response.status_code,
                    )
            
            return response.json()
            
        except httpx.TimeoutException:
            raise AraseAPIError(
                "Request timeout | انتهت مهلة الطلب",
                code="TIMEOUT",
                status=408,
            )
        except httpx.RequestError as e:
            raise AraseAPIError(
                f"Network error: {str(e)} | خطأ في الشبكة",
                code="NETWORK_ERROR",
                status=0,
            )
    
    async def search(self, query: str, **kwargs) -> SearchResponse:
        """Async search - see AraseClient.search for docs."""
        # Reuse sync client's parsing logic
        sync_client = AraseClient.__new__(AraseClient)
        
        opts = SearchOptions()
        for key, value in kwargs.items():
            if hasattr(opts, key):
                setattr(opts, key, value)
        
        body = {
            "query": query,
            "search_depth": opts.search_depth,
            "max_results": opts.max_results,
            "include_answer": opts.include_answer,
            "include_raw_content": opts.include_raw_content,
            "include_images": opts.include_images,
            "include_videos": opts.include_videos,
            "include_news": opts.include_news,
            "include_maps": opts.include_maps,
            "include_places": opts.include_places,
            "include_shopping": opts.include_shopping,
            "include_scholar": opts.include_scholar,
            "topic": opts.topic,
        }
        
        data = await self._request("/search", body)
        return sync_client._parse_search_response(data)
