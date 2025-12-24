"""Retry logic with exponential backoff."""

import time
import logging
from typing import Callable, Type, Tuple, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            retry_on: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.retry_on = retry_on or (Exception,)


def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator to add retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        retry_on: Tuple of exception types to retry on
    
    Example:
        from canvelete.exceptions import RateLimitError, ServerError
        
        @with_retry(
            max_attempts=5,
            backoff_factor=2,
            retry_on=(RateLimitError, ServerError)
        )
        def make_api_call():
            return client.designs.list()
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        max_delay=max_delay,
        retry_on=retry_on,
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = config.initial_delay
            
            while attempt < config.max_attempts:
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    attempt += 1
                    
                    if attempt >= config.max_attempts:
                        logger.error(
                            f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}"
                        )
                        raise
                    
                    # Check if it's a rate limit error with retry-after header
                    if hasattr(e, 'retry_after') and e.retry_after:
                        delay = float(e.retry_after)
                        logger.warning(
                            f"Rate limited. Retrying after {delay}s (attempt {attempt}/{config.max_attempts})"
                        )
                    else:
                        logger.warning(
                            f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                    
                    time.sleep(delay)
                    
                    # Exponential backoff
                    delay = min(delay * config.backoff_factor, config.max_delay)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def retry_on_rate_limit(func: Callable) -> Callable:
    """
    Convenience decorator for retrying on rate limit errors.
    
    Example:
        @retry_on_rate_limit
        def make_api_call():
            return client.designs.list()
    """
    from ..exceptions import RateLimitError, ServerError
    
    return with_retry(
        max_attempts=5,
        backoff_factor=2,
        retry_on=(RateLimitError, ServerError),
    )(func)
