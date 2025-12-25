"""
Retry configuration for Scout SDK API requests.
"""

import logging
import requests
from typing import Callable, TypedDict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    RetryCallState,
)

logger = logging.getLogger(__name__)


class RetryConfig(TypedDict, total=False):
    """
    Configuration for retry strategy.

    Attributes:
        max_attempts: Maximum number of attempts including the initial attempt (default: 10).
                     For example, max_attempts=3 means 1 initial attempt + up to 2 retries.
                     Set to 0 or 1 to disable retries.
        multiplier: Exponential backoff multiplier (default: 1)
        min_wait: Minimum wait time in seconds (default: 0.5)
        max_wait: Maximum wait time in seconds (default: 10)
    """

    max_attempts: int
    multiplier: int
    min_wait: float
    max_wait: float


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """
    Log retry attempts with details about the exception and attempt number.

    Args:
        retry_state: The retry state object from tenacity
    """
    if retry_state.outcome is None:
        return

    exception = retry_state.outcome.exception()
    if exception is None:
        return

    attempt_number = retry_state.attempt_number

    error_details = f"type={type(exception).__name__}"
    if hasattr(exception, "response") and exception.response is not None:
        error_details += f", status_code={exception.response.status_code}"

    next_action = retry_state.next_action
    sleep_time = next_action.sleep if next_action is not None else 0

    logger.warning(
        f"🔄 SDK Retry attempt {attempt_number} - {error_details} - "
        f"Next retry in {sleep_time}s"
    )


def should_retry(exception: BaseException) -> bool:
    """
    Determine if a request should be retried based on the exception.

    Retries on:
        - Rate limiting (429)
        - Server errors (500, 502, 503, 504)
        - Network errors (ConnectionError, Timeout)

    Args:
        exception: The exception raised during the request

    Returns:
        bool: True if the request should be retried
    """
    # Retry on connection and timeout errors
    if isinstance(
        exception,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
    ):
        return True

    # Retry on specific HTTP status codes
    if isinstance(exception, requests.exceptions.HTTPError):
        if hasattr(exception, "response") and exception.response is not None:
            return exception.response.status_code in [429, 502, 503, 504]

    return False


def no_retry_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that doesn't retry - just executes the function once.
    Used when retry is explicitly disabled (max_attempts <= 1).
    """
    return func


def create_retry_strategy(
    max_attempts: int = 10,
    multiplier: int = 1,
    min_wait: float = 0.5,
    max_wait: float = 10,
) -> Callable[..., Any]:
    """
    Create a custom retry decorator with specific parameters.

    Args:
        max_attempts: Maximum number of attempts including the initial attempt (default: 10).
                     For example, max_attempts=3 means 1 initial attempt + up to 2 retries.
                     Set to 0 or 1 to disable retries.
        multiplier: Exponential backoff multiplier (default: 1)
        min_wait: Minimum wait time in seconds (default: 0.5)
        max_wait: Maximum wait time in seconds (default: 10)

    Returns:
        A retry decorator configured with the specified parameters.
        Returns a no-op decorator if max_attempts is 0 or 1.

    Example:
        # Disable retries
        no_retry = create_retry_strategy(max_attempts=0)

        # Create a quick retry strategy (3 total attempts = 1 initial + up to 2 retries)
        quick_retry = create_retry_strategy(max_attempts=3, min_wait=1, max_wait=5)

        # Create an aggressive retry strategy (20 total attempts = 1 initial + up to 19 retries)
        aggressive_retry = create_retry_strategy(max_attempts=20, multiplier=2, max_wait=60)
    """
    # If max_attempts is 0 or 1, disable retries
    if max_attempts <= 1:
        return no_retry_decorator

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception(should_retry),
        before_sleep=log_retry_attempt,
        reraise=True,
    )


# Default retry decorator for API calls
retry_on_api_errors = create_retry_strategy()
