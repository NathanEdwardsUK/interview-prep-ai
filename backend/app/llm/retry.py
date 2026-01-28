"""Retry helper for LLM calls with exponential backoff."""
import asyncio
import logging

logger = logging.getLogger(__name__)

LLM_RETRY_ATTEMPTS = 3
LLM_RETRY_BASE_DELAY = 1.0  # seconds


async def with_retry(coro, attempts: int = LLM_RETRY_ATTEMPTS, base_delay: float = LLM_RETRY_BASE_DELAY):
    """Execute coroutine with exponential backoff. Raises last exception if all retries fail."""
    last_exc = None
    for attempt in range(attempts):
        try:
            return await coro()
        except Exception as e:
            last_exc = e
            logger.warning("LLM call failed (attempt %s/%s): %s", attempt + 1, attempts, e)
            if attempt < attempts - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
    raise last_exc
