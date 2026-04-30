import random
from config import settings
from schemas import CrawlResponse

_MOCK_ARTICLES = [
    {
        "title": "The Rise of Microservices Architecture in Modern Applications",
        "text": (
            "Microservices architecture has fundamentally changed how we build and deploy software. "
            "Instead of monolithic applications, teams now break systems into small, independent services "
            "that communicate over well-defined APIs. Each service handles a specific business capability "
            "and can be developed, deployed, and scaled independently.\n\n"
            "The benefits are substantial. Development teams can work in parallel without stepping on each "
            "other's toes. A bug in the payment service won't bring down the entire e-commerce platform. "
            "Services can be written in different programming languages, choosing the best tool for each job.\n\n"
            "Tools like Docker and Kubernetes have made microservices more accessible. Container orchestration "
            "handles service discovery, load balancing, and automatic restarts. Message queues like RabbitMQ "
            "and Kafka enable asynchronous communication, decoupling services further."
        ),
    },
    {
        "title": "How Artificial Intelligence is Transforming Content Creation",
        "text": (
            "Artificial intelligence is reshaping the landscape of content creation in ways that seemed "
            "impossible just five years ago. Large language models can now draft articles, generate marketing "
            "copy, write code, and even produce creative fiction.\n\n"
            "Text-to-speech technology has matured dramatically. Neural voices now sound remarkably natural, "
            "with proper intonation, pacing, and emotional nuance. Podcasting can now be automated from a "
            "written article to a polished audio episode in minutes.\n\n"
            "Content summarization is another transformative application. Long research papers and complex "
            "reports can be distilled into concise summaries without losing key insights."
        ),
    },
    {
        "title": "Python FastAPI: Building High-Performance APIs with Modern Python",
        "text": (
            "FastAPI has rapidly become one of the most popular Python web frameworks, and for good reason. "
            "It combines the simplicity of Flask with automatic data validation, serialization, and interactive "
            "API documentation.\n\n"
            "The framework's killer feature is its use of Python type hints to automatically generate request "
            "validation and OpenAPI documentation. Invalid requests are rejected with clear error messages "
            "before your code even runs.\n\n"
            "Async support is first-class. FastAPI runs on ASGI, allowing handlers to be defined with "
            "async def for truly non-blocking I/O operations, handling thousands of concurrent connections."
        ),
    },
]


def crawl_url(url: str) -> CrawlResponse:
    if settings.use_mock:
        # ❌ XÓA BLOCK NÀY KHI CHUYỂN THẬT
        article = random.choice(_MOCK_ARTICLES)
        text = article["text"]
        return CrawlResponse(
            url=url,
            title=article["title"],
            text=text,
            word_count=len(text.split()),
            is_mock=True,
        )

    # ✅ VIẾT CRAWLER THẬT VÀO ĐÂY
    pass
