import time
from typing import Callable, Any, Tuple, Type
import httpx


DEFAULT_RETRIES = 3
DEFAULT_DELAY = 1.5


def with_retry(
    func: Callable[..., Any],
    retries: int = DEFAULT_RETRIES,
    delay: float = DEFAULT_DELAY,
    retry_on: Tuple[Type[Exception], ...] = (
        httpx.TimeoutException,
        httpx.NetworkError,
    ),
) -> Any:
    """
    Execute a function with retry logic.

    Usage:
        response = with_retry(lambda: client.get("/health"))
    """

    last_exception = None

    for attempt in range(1, retries + 1):
        try:
            return func()
        except retry_on as e:
            last_exception = e
            if attempt >= retries:
                break
            time.sleep(delay * attempt)

    raise last_exception
