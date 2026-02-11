"""Retry logic with exponential backoff"""
import asyncio
from typing import Callable, Any
from config import MAX_SUBMISSION_RETRIES, RETRY_BACKOFF_FACTOR
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RetryStrategy:
    """Exponential backoff retry strategy"""

    def __init__(
        self,
        max_retries: int = MAX_SUBMISSION_RETRIES,
        backoff_factor: float = RETRY_BACKOFF_FACTOR
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry.

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for func

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")

                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")

        raise last_exception
