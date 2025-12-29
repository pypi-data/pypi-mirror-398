# ARASE Python SDK

المكتبة الرسمية لـ ARASE - محرك البحث الذكي بالذكاء الاصطناعي.

Official Python SDK for ARASE - AI-powered search engine API.

## Installation | التثبيت

```bash
pip install arase-sdk
```

## Quick Start | البداية السريعة

### Option 1: Environment Variable (Recommended) | الخيار 1: متغير البيئة (مستحسن)

```bash
# .env file | ملف .env
ARASE_API_KEY=arase_YOUR_API_KEY
```

```python
from arase import AraseClient

# Automatically reads from ARASE_API_KEY environment variable
# يقرأ تلقائياً من متغير البيئة ARASE_API_KEY
client = AraseClient()

results = client.search("ما هي رؤية السعودية 2030؟")
print(results.answer)
```

### Option 2: Direct API Key | الخيار 2: مفتاح API مباشر

```python
from arase import AraseClient

client = AraseClient(api_key="arase_YOUR_API_KEY")

results = client.search("What is Saudi Vision 2030?")
print(results.answer)
```

## Environment Variables | متغيرات البيئة

| Variable         | Description               | الوصف                      |
| ---------------- | ------------------------- | -------------------------- |
| `ARASE_API_KEY`  | Your API key (required)   | مفتاح API الخاص بك (مطلوب) |
| `ARASE_BASE_URL` | Custom API URL (optional) | رابط API مخصص (اختياري)    |

## Features | الميزات

### Web Search | بحث الويب

```python
results = client.search("أفضل المطاعم في الرياض", include_answer=True)

print(results.answer)   # AI-generated answer | إجابة AI
print(results.results)  # Web results | نتائج الويب
```

### Image Search | بحث الصور

```python
results = client.search_images("برج المملكة الرياض")
for image in results.images:
    print(image.image_url)
```

### News Search | بحث الأخبار

```python
results = client.search_news("أخبار السعودية اليوم")
for article in results.news:
    print(f"{article.title} - {article.source}")
```

### Places Search | بحث الأماكن

```python
# Search near Riyadh | البحث قرب الرياض
results = client.search_places(
    "مقاهي قريبة",
    user_location={"lat": 24.7136, "lng": 46.6753}
)
for place in results.places:
    print(f"{place.title} - {place.rating}⭐")
```

### Academic Search | بحث أكاديمي

```python
results = client.search_scholar("artificial intelligence")
for paper in results.scholar:
    print(f"{paper.title} ({paper.year}) - {paper.citations} citations")
```

### Stock Market Search | بحث سوق الأسهم

```python
# Basic stock search | بحث بسيط
stocks = client.search(
    "كم سعر سهم أرامكو؟",
    include_stocks=True,
)

if stocks.stocks:
    for stock in stocks.stocks.results:
        print(f"{stock.name}: {stock.price} {stock.currency}")
        print(f"Change: {stock.change_percent}%")

# With AI summary (+1 request) | مع ملخص AI (+1 طلب)
stocks_with_summary = client.search(
    "Compare Aramco vs Al Rajhi",
    include_stocks=True,
    options={
        "stocks": {
            "summary": True
        }
    },
)

print(stocks_with_summary.stocks.summary)
```

### Weather Search | بحث الطقس

```python
# Basic weather | طقس بسيط
weather = client.search(
    "الطقس في جدة",
    include_weather=True,
)

if weather.weather:
    location = weather.weather.location
    current = weather.weather.current
    print(f"{location['name']}: {current['temp_c']}°C, {current['condition']}")

    # Forecast | التوقعات
    for day in weather.weather.forecast:
        print(f"{day.date}: {day.mintemp_c}°C - {day.maxtemp_c}°C")

# With AI summary and advice (+1 request) | مع ملخص ونصائح AI
weather_with_summary = client.search(
    "Weather in Riyadh",
    include_weather=True,
    options={
        "weather": {
            "summary": True
        }
    },
)

print(weather_with_summary.weather.summary)
print(weather_with_summary.weather.advice)
```

### Content Extraction | استخراج المحتوى

```python
content = client.extract(
    "https://example.com/article",
    include_summary=True
)
print(content.content)
print(content.summary)
```

## Advanced Options | خيارات متقدمة

```python
from arase import AraseClient, SearchOptions

client = AraseClient()

# Using SearchOptions | استخدام SearchOptions
options = SearchOptions(
    search_depth="deep",      # basic | advanced | deep
    max_results=20,
    include_answer=True,
    include_images=True,
    include_videos=True,
    include_news=True,
    include_places=True,
    include_shopping=True,
    include_scholar=True,
    include_stocks=True,      # 🆕 Stock market data
    include_weather=True,     # 🆕 Weather forecasts
    topic="general",          # general | news | academic
    max_steps=3,              # For deep search | للبحث العميق

    # Optional AI summaries | ملخصات AI اختيارية
    options={
        "stocks": {
            "summary": True  # +1 request | +1 طلب
        },
        "weather": {
            "summary": True  # +1 request | +1 طلب
        },
    },
)

results = client.search("query", options=options)

# Or use keyword arguments | أو استخدم الكلمات المفتاحية
results = client.search(
    "query",
    include_answer=True,
    max_results=10,
)
```

## Async Support | دعم Async

```python
import asyncio
from arase import AsyncAraseClient

async def main():
    async with AsyncAraseClient() as client:
        results = await client.search("query", include_answer=True)
        print(results.answer)

asyncio.run(main())
```

## Error Handling | معالجة الأخطاء

```python
from arase import AraseClient, AraseAPIError

client = AraseClient()

try:
    results = client.search("query")
except AraseAPIError as e:
    print(f"Error {e.code}: {e.message}")
    print(f"Status: {e.status}")
```

## Context Manager | مدير السياق

```python
from arase import AraseClient

# Automatically closes connection | يغلق الاتصال تلقائياً
with AraseClient() as client:
    results = client.search("query")
    print(results.answer)
```

## Type Hints | تلميحات الأنواع

Full type hints support for better IDE experience:

```python
from arase import (
    AraseClient,
    SearchOptions,
    SearchResponse,
    SearchResult,
    ImageResult,
    StockResult,        # 🆕 New: Stock data types
    StocksResponse,     # 🆕 New: Stock response
    WeatherForecast,    # 🆕 New: Weather forecast
    WeatherResponse,    # 🆕 New: Weather response
    # ... etc
)
```

## Links | روابط

- 📖 [Documentation | التوثيق](https://arase.masarat.sa/docs)
- 🎮 [Playground | ساحة التجربة](https://arase.masarat.sa/platform)
- 🔑 [Get API Key | احصل على مفتاح](https://arase.masarat.sa/platform)
- 💻 [GitHub](https://github.com/masarat-sa/arase-python)

## License

MIT
