"""
Error Handler
Provides retry logic and error classification.
"""
import asyncio
import structlog
from typing import Callable, Any

logger = structlog.get_logger()

class ErrorHandler:
    
    async def retry_async(
        self, 
        func: Callable, 
        retries: int = 3, 
        delay: float = 1.0,
        *args, **kwargs
    ) -> Any:
        """Retry an async function with exponential backoff."""
        last_exception = None
        
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                wait_time = delay * (2 ** attempt)
                logger.warning(
                    "Operation failed, retrying",
                    attempt=attempt+1,
                    error=str(e),
                    wait_s=wait_time
                )
                await asyncio.sleep(wait_time)
        
        logger.error("Operation failed after retries", error=str(last_exception))
        raise last_exception