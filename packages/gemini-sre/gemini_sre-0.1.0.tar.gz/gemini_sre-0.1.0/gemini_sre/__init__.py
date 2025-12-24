"""
Gemini SRE Client - Production-ready Google Gemini API wrapper.

Provides enterprise-grade reliability features:
- Automatic retry with exponential backoff
- Multi-region failover
- Circuit breaker pattern
- Cloud Monitoring integration
- Structured logging
- Deduplication for non-idempotent operations
- Full async/await support

Usage (Sync):
    from gemini_sre import GeminiSREClient

    client = GeminiSREClient(
        project_id="my-project",
        locations=["us-central1", "europe-west1"],
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain quantum computing",
    )

Usage (Async):
    from gemini_sre import AsyncGeminiSREClient
    import asyncio

    async def main():
        async with AsyncGeminiSREClient(
            project_id="my-project",
            locations=["us-central1", "europe-west1"],
        ) as client:
            response = await client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Explain quantum computing",
            )

    asyncio.run(main())
"""

from gemini_sre.async_client import AsyncGeminiSREClient
from gemini_sre.client import GeminiSREClient

__version__ = "0.1.0"
__all__ = ["GeminiSREClient", "AsyncGeminiSREClient"]
