"""
AsyncGeminiSREClient - Async version of the main client.

Provides async/await support for all operations with full SRE features.
"""

import asyncio
import logging
from typing import Any, Optional

from google import genai

from gemini_sre.core.circuit_breaker import CircuitBreaker, CircuitState
from gemini_sre.core.deduplication import DeduplicationCache
from gemini_sre.core.logging import StructuredLogger
from gemini_sre.core.monitoring import MonitoringClient
from gemini_sre.core.retry import RetryConfig
from gemini_sre.proxies.async_caches import AsyncCachesProxy
from gemini_sre.proxies.async_chats import AsyncChatsProxy
from gemini_sre.proxies.async_files import AsyncFilesProxy

# Import async proxies (will create these next)
from gemini_sre.proxies.async_models import AsyncModelsProxy
from gemini_sre.proxies.async_operations import AsyncOperationsProxy
from gemini_sre.proxies.async_tunings import AsyncTuningsProxy


class AsyncGeminiSREClient:
    """
    Async production-ready Gemini client with SRE features.

    Wraps the official Google GenAI SDK with:
    - Async/await support
    - Automatic retry with exponential backoff
    - Multi-region failover
    - Circuit breaker pattern
    - Cloud Monitoring integration
    - Structured logging

    Usage:
        async with AsyncGeminiSREClient(project_id="my-project") as client:
            response = await client.models.generate_content(...)
    """

    def __init__(
        self,
        project_id: str,
        locations: Optional[list[str]] = None,
        *,
        # SDK configuration
        api_key: Optional[str] = None,
        vertexai: bool = True,
        http_options: Optional[dict] = None,
        # SRE features
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 16.0,
        exp_base: float = 2.0,
        jitter: float = 0.5,
        enable_region_failover: bool = True,
        enable_circuit_breaker: bool = True,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_success_threshold: int = 2,
        circuit_breaker_timeout: int = 60,
        circuit_breaker_window: int = 120,
        enable_monitoring: bool = True,
        enable_logging: bool = True,
        # Advanced options
        deduplication_cache_ttl: int = 3600,
        custom_retry_config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize AsyncGeminiSREClient.

        Args:
            project_id: GCP project ID
            locations: List of regions for failover (default: ["us-central1", "europe-west1"])
            api_key: API key for Gemini Developer API (if not using Vertex AI)
            vertexai: Use Vertex AI (True) or Gemini Developer API (False)
            http_options: HTTP client options

            max_retries: Maximum API retry attempts
            initial_delay: Initial retry delay in seconds
            max_delay: Maximum retry delay in seconds
            exp_base: Exponential backoff base
            jitter: Jitter factor (0.0-1.0)

            enable_region_failover: Enable multi-region failover
            enable_circuit_breaker: Enable circuit breaker for failing regions
            circuit_breaker_failure_threshold: Open circuit after N failures
            circuit_breaker_success_threshold: Close circuit after N successes
            circuit_breaker_timeout: Seconds before retrying failed region
            circuit_breaker_window: Time window for counting failures

            enable_monitoring: Enable Cloud Monitoring metrics
            enable_logging: Enable structured logging

            deduplication_cache_ttl: TTL for deduplication cache (seconds)
            custom_retry_config: Custom retry config per method type
        """
        self.project_id = project_id
        self.locations = locations or ["us-central1", "europe-west1", "europe-west3"]
        self.vertexai = vertexai
        self.api_key = api_key
        self.http_options = http_options

        # SRE configuration
        self._retry_config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exp_base=exp_base,
            jitter=jitter,
            custom_config=custom_retry_config,
        )

        self._enable_region_failover = enable_region_failover
        self._enable_circuit_breaker = enable_circuit_breaker

        # Initialize circuit breaker
        if enable_circuit_breaker:
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=circuit_breaker_failure_threshold,
                success_threshold=circuit_breaker_success_threshold,
                timeout=circuit_breaker_timeout,
                window=circuit_breaker_window,
            )
        else:
            self._circuit_breaker = None

        # Initialize monitoring
        if enable_monitoring:
            self._monitoring = MonitoringClient(project_id=project_id)
        else:
            self._monitoring = None

        # Initialize logging
        if enable_logging:
            self._logger = StructuredLogger(project_id=project_id)
        else:
            self._logger = logging.getLogger(__name__)

        # Initialize deduplication cache
        self._dedup_cache = DeduplicationCache(ttl=deduplication_cache_ttl)

        # Per-region SDK clients (lazy initialized)
        self._clients: dict[str, genai.Client] = {}

        # Initialize namespace proxies
        self.models = AsyncModelsProxy(self)
        self.files = AsyncFilesProxy(self)
        self.chats = AsyncChatsProxy(self)
        self.tunings = AsyncTuningsProxy(self)
        self.caches = AsyncCachesProxy(self)
        self.operations = AsyncOperationsProxy(self)

        # Compatibility layer for libraries expecting .aio namespace (e.g. Mirascope)
        self.aio = self

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close all resources."""
        # Note: genai.Client doesn't require explicit close
        # This is here for future resource cleanup if needed
        pass

    def _get_client(self, location: str) -> genai.Client:
        """
        Get or create SDK client for specific region.

        Note: This is synchronous because genai.Client initialization
        is synchronous. The actual API calls will be async.
        """
        if location not in self._clients:
            if self.vertexai:
                self._clients[location] = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=location,
                    http_options=self.http_options,
                )
            else:
                self._clients[location] = genai.Client(
                    api_key=self.api_key,
                    http_options=self.http_options,
                )

        return self._clients[location]

    async def _execute_with_failover(
        self,
        operation_func,
        operation_type: str,
        request_id: Optional[str] = None,
    ):
        """
        Execute async operation with retry and failover logic.

        Args:
            operation_func: Async function that takes (client, location) and returns result
            operation_type: Type of operation for retry config
            request_id: Optional request ID for tracking

        Returns:
            Operation result
        """
        retry_config = self._retry_config.get_config(operation_type)

        if not self._enable_region_failover:
            # Single region, no failover
            location = self.locations[0]
            client = self._get_client(location)
            return await self._execute_with_retry(
                lambda: operation_func(client, location),
                retry_config=retry_config,
                location=location,
                request_id=request_id,
            )

        # Multi-region failover
        available_locations = self._get_available_locations()
        last_exception = None

        for attempt, location in enumerate(available_locations):
            try:
                client = self._get_client(location)
                result = await self._execute_with_retry(
                    lambda c=client, loc=location: operation_func(c, loc),
                    retry_config=retry_config,
                    location=location,
                    request_id=request_id,
                )

                # Success - record for circuit breaker
                if self._circuit_breaker:
                    self._circuit_breaker.record_success(location)

                return result

            except Exception as e:
                last_exception = e

                # Record failure for circuit breaker
                if self._circuit_breaker:
                    self._circuit_breaker.record_failure(location, e)

                self._logger.warning(f"Region {location} failed (attempt {attempt + 1}): {e}")

                # Try next region
                continue

        # All regions failed
        self._logger.error(f"All regions failed for request_id={request_id}")
        raise last_exception

    async def _execute_with_retry(
        self,
        operation_func,
        retry_config: dict[str, Any],
        location: str,
        request_id: Optional[str],
    ):
        """Execute async operation with retry logic."""
        import time

        max_retries = retry_config["max_retries"]

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                result = await operation_func()
                latency = time.time() - start_time

                # Record success metrics
                if self._monitoring:
                    self._monitoring.record_success(
                        latency=latency,
                        retry_count=attempt,
                        location=location,
                    )

                return result

            except Exception as e:
                if attempt >= max_retries:
                    # Max retries exhausted
                    if self._monitoring:
                        self._monitoring.record_failure(
                            error=str(e),
                            retry_count=attempt,
                            location=location,
                        )
                    raise

                # Calculate backoff delay
                delay = self._calculate_backoff(attempt, retry_config)
                self._logger.info(f"Retry {attempt + 1}/{max_retries} after {delay:.2f}s: {e}")
                await asyncio.sleep(delay)  # Use asyncio.sleep for async

    def _calculate_backoff(self, attempt: int, config: dict[str, Any]) -> float:
        """Calculate exponential backoff with jitter."""
        import random

        base_delay = config["initial_delay"] * (config["exp_base"] ** attempt)
        delay = min(base_delay, config["max_delay"])

        # Add jitter
        jitter_amount = delay * config["jitter"] * random.random()  # nosec B311
        return delay + jitter_amount

    def _get_available_locations(self) -> list[str]:
        """Get list of available locations (excluding circuit-open regions)."""
        if not self._circuit_breaker:
            return self.locations

        available = []
        for location in self.locations:
            state = self._circuit_breaker.get_state(location)
            if state != CircuitState.OPEN:
                available.append(location)

        # If all circuits are open, fallback to all locations
        if not available:
            self._logger.warning("All circuits open, using all locations as fallback")
            return self.locations

        return available
