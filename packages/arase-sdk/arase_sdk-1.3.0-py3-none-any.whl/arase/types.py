"""
ARASE SDK Types
أنواع البيانات لـ ARASE SDK

Type definitions for the ARASE Search API SDK.
تعريفات الأنواع لحزمة SDK الخاصة بواجهة برمجة تطبيقات اريز للبحث.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal


# ================================================
# Search Options | خيارات البحث
# ================================================

@dataclass
class SearchOptions:
    """
    Options for customizing search requests.
    خيارات لتخصيص طلبات البحث.
    """
    
    # Search depth level | مستوى عمق البحث
    # "basic": Fast search | بحث سريع
    # "advanced": More comprehensive | أكثر شمولاً
    # "deep": Multi-step research | بحث متعدد الخطوات
    search_depth: Literal["basic", "advanced", "deep"] = "basic"
    
    # Maximum number of results (1-20) | الحد الأقصى لعدد النتائج (1-20)
    max_results: int = 10
    
    # Include AI-generated answer | تضمين إجابة مولدة بالذكاء الاصطناعي
    include_answer: bool = False
    
    # Include raw HTML content | تضمين المحتوى الخام HTML
    include_raw_content: bool = False
    
    # Include image results | تضمين نتائج الصور
    include_images: bool = False
    
    # Include video results | تضمين نتائج الفيديوهات
    include_videos: bool = False
    
    # Include news articles | تضمين المقالات الإخبارية
    include_news: bool = False
    
    # Include map results | تضمين نتائج الخرائط
    include_maps: bool = False
    
    # Include place results | تضمين نتائج الأماكن
    include_places: bool = False
    
    # Include shopping results | تضمين نتائج التسوق
    include_shopping: bool = False
    
    # Include academic results | تضمين النتائج الأكاديمية
    include_scholar: bool = False
    
    # Include stock market results | تضمين نتائج سوق الأسهم
    include_stocks: bool = False
    
    # Include weather forecast results | تضمين نتائج توقعات الطقس
    include_weather: bool = False
    
    # Search topic category | فئة موضوع البحث
    topic: Literal["general", "news", "academic"] = "general"
    
    # Maximum steps for deep search | الحد الأقصى لخطوات البحث العميق
    max_steps: Optional[int] = None
    
    # User's location for nearby search | موقع المستخدم للبحث القريب
    user_location: Optional[Dict[str, float]] = None
    
    # Advanced options for specific features | خيارات متقدمة لميزات محددة
    options: Optional[Dict[str, Any]] = None


# ================================================
# Search Results | نتائج البحث
# ================================================

@dataclass
class SearchResult:
    """
    A single web search result.
    نتيجة بحث ويب واحدة.
    """
    # Result title | عنوان النتيجة
    title: str
    # Result URL | رابط النتيجة
    url: str
    # Result content/snippet | محتوى/مقتطف النتيجة
    content: str
    # Relevance score (0-1) | درجة الصلة (0-1)
    score: Optional[float] = None
    # Publication date | تاريخ النشر
    published_date: Optional[str] = None
    # Source/domain name | اسم المصدر/النطاق
    source: Optional[str] = None
    # Raw HTML content | المحتوى الخام HTML
    raw_content: Optional[str] = None


@dataclass
class ImageResult:
    """
    An image search result.
    نتيجة بحث صورة.
    """
    # Image title | عنوان الصورة
    title: str
    # Full image URL | رابط الصورة الكاملة
    image_url: str
    # Thumbnail URL | رابط الصورة المصغرة
    thumbnail_url: str
    # Source page URL | رابط الصفحة المصدر
    source_url: Optional[str] = None
    # Image width | عرض الصورة
    width: Optional[int] = None
    # Image height | ارتفاع الصورة
    height: Optional[int] = None


@dataclass
class VideoResult:
    """
    A video search result.
    نتيجة بحث فيديو.
    """
    # Video title | عنوان الفيديو
    title: str
    # Video URL | رابط الفيديو
    url: str
    # Thumbnail URL | رابط الصورة المصغرة
    thumbnail_url: str
    # Video duration | مدة الفيديو
    duration: Optional[str] = None
    # Platform (YouTube, etc.) | المنصة
    platform: Optional[str] = None
    # Channel name | اسم القناة
    channel: Optional[str] = None
    # View count | عدد المشاهدات
    views: Optional[str] = None
    # Description | الوصف
    description: Optional[str] = None


@dataclass
class NewsResult:
    """
    A news article search result.
    نتيجة بحث مقال إخباري.
    """
    # Article title | عنوان المقال
    title: str
    # Article URL | رابط المقال
    url: str
    # Article content | محتوى المقال
    content: str
    # News source | المصدر الإخباري
    source: Optional[str] = None
    # Publication date | تاريخ النشر
    published_date: Optional[str] = None
    # Article image URL | رابط صورة المقال
    image_url: Optional[str] = None


@dataclass
class PlaceResult:
    """
    A place/location search result.
    نتيجة بحث مكان/موقع.
    """
    # Place name | اسم المكان
    title: str
    # Address | العنوان
    address: str
    # Latitude | خط العرض
    latitude: Optional[float] = None
    # Longitude | خط الطول
    longitude: Optional[float] = None
    # Rating (0-5) | التقييم
    rating: Optional[float] = None
    # Number of reviews | عدد التقييمات
    rating_count: Optional[int] = None
    # Place type | نوع المكان
    type: Optional[str] = None
    # Phone number | رقم الهاتف
    phone: Optional[str] = None
    # Website URL | رابط الموقع
    website: Optional[str] = None
    # Opening hours | ساعات العمل
    hours: Optional[str] = None


@dataclass
class ShoppingResult:
    """
    A shopping/product search result.
    نتيجة بحث تسوق/منتج.
    """
    # Product name | اسم المنتج
    title: str
    # Product URL | رابط المنتج
    url: str
    # Price | السعر
    price: Optional[str] = None
    # Store name | اسم المتجر
    source: Optional[str] = None
    # Product image URL | رابط صورة المنتج
    image_url: Optional[str] = None
    # Rating | التقييم
    rating: Optional[float] = None


@dataclass
class ScholarResult:
    """
    An academic/scholarly search result.
    نتيجة بحث أكاديمي/علمي.
    """
    # Paper title | عنوان البحث
    title: str
    # Paper URL | رابط البحث
    url: str
    # Abstract/snippet | الملخص
    snippet: Optional[str] = None
    # Authors list | قائمة المؤلفين
    authors: Optional[List[str]] = None
    # Publication year | سنة النشر
    year: Optional[str] = None
    # Citation count | عدد الاستشهادات
    citations: Optional[int] = None


@dataclass
class StockResult:
    """
    A stock market result.
    نتيجة سوق الأسهم.
    """
    # Stock symbol | رمز السهم
    symbol: str
    # Company name | اسم الشركة
    name: str
    # Current price | السعر الحالي
    price: float
    # Currency | العملة
    currency: str
    # Price change | تغيير السعر
    change: float
    # Change percentage | نسبة التغيير
    change_percent: float
    # Trading volume | حجم التداول
    volume: Optional[int] = None


@dataclass
class StocksResponse:
    """
    Stock search response.
    استجابة بحث الأسهم.
    """
    # Stock results | نتائج الأسهم
    results: List[StockResult] = field(default_factory=list)
    # Query intent | نية الاستعلام
    query_intent: Optional[str] = None
    # Market type | نوع السوق
    market: Optional[str] = None
    # AI-generated summary | ملخص AI
    summary: Optional[str] = None


@dataclass
class WeatherForecast:
    """
    Weather forecast for a single day.
    توقعات الطقس ليوم واحد.
    """
    # Date | التاريخ
    date: str
    # Maximum temperature (Celsius) | الحرارة العظمى (مئوية)
    maxtemp_c: float
    # Minimum temperature (Celsius) | الحرارة الصغرى (مئوية)
    mintemp_c: float
    # Weather condition | حالة الطقس
    condition: str


@dataclass
class WeatherResponse:
    """
    Weather search response.
    استجابة بحث الطقس.
    """
    # Location info | معلومات الموقع
    location: Dict[str, str] = field(default_factory=dict)
    # Current weather | الطقس الحالي
    current: Dict[str, Any] = field(default_factory=dict)
    # Forecast days | أيام التوقعات
    forecast: List[WeatherForecast] = field(default_factory=list)
    # AI-generated summary | ملخص AI
    summary: Optional[str] = None
    # AI-generated advice | نصائح AI
    advice: Optional[str] = None


@dataclass
class CreditsInfo:
    """
    Credit usage information.
    معلومات استخدام الرصيد.
    """
    # Credits used | الرصيد المستخدم
    cost: int
    # Remaining credits | الرصيد المتبقي
    remaining: int


@dataclass
class ResponseMeta:
    """
    Response metadata.
    بيانات وصفية للاستجابة.
    """
    # Response time in ms | وقت الاستجابة بالملي ثانية
    response_time: float
    # Credit usage | استخدام الرصيد
    credits: Optional[CreditsInfo] = None


# ================================================
# Search Response | استجابة البحث
# ================================================

@dataclass
class SearchResponse:
    """
    The response from a search request.
    الاستجابة من طلب البحث.
    """
    # Original query | الاستعلام الأصلي
    query: str
    # Web results | نتائج الويب
    results: List[SearchResult] = field(default_factory=list)
    # AI answer | إجابة الذكاء الاصطناعي
    answer: Optional[str] = None
    # Image results | نتائج الصور
    images: Optional[List[ImageResult]] = None
    # Video results | نتائج الفيديوهات
    videos: Optional[List[VideoResult]] = None
    # News results | نتائج الأخبار
    news: Optional[List[NewsResult]] = None
    # Map results | نتائج الخرائط
    maps: Optional[List[PlaceResult]] = None
    # Place results | نتائج الأماكن
    places: Optional[List[PlaceResult]] = None
    # Shopping results | نتائج التسوق
    shopping: Optional[List[ShoppingResult]] = None
    # Academic results | نتائج أكاديمية
    scholar: Optional[List[ScholarResult]] = None
    # Stock market results | نتائج سوق الأسهم
    stocks: Optional[StocksResponse] = None
    # Weather forecast results | نتائج توقعات الطقس
    weather: Optional[WeatherResponse] = None
    # Response metadata | البيانات الوصفية
    meta: Optional[ResponseMeta] = None


# ================================================
# Extract Options | خيارات الاستخراج
# ================================================

@dataclass
class ExtractOptions:
    """
    Options for content extraction.
    خيارات لاستخراج المحتوى.
    """
    # Include AI summary | تضمين تلخيص AI
    include_summary: bool = False


@dataclass
class ExtractResponse:
    """
    The response from a content extraction request.
    الاستجابة من طلب استخراج المحتوى.
    """
    # The extracted URL | الرابط المستخرج
    url: str
    # Extracted content | المحتوى المستخرج
    content: str
    # Whether extraction was successful | هل نجح الاستخراج
    success: bool
    # AI summary | تلخيص AI
    summary: Optional[str] = None
    # Response metadata | البيانات الوصفية
    meta: Optional[ResponseMeta] = None
