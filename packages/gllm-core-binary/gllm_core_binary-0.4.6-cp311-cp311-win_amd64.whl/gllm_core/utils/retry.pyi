from _typeshed import Incomplete
from gllm_core.utils import LoggerManager as LoggerManager
from gllm_core.utils.concurrency import syncify as syncify
from pydantic import BaseModel
from typing import Any, Callable, TypeVar, overload

logger: Incomplete
T = TypeVar('T')
BASE_EXPONENTIAL_BACKOFF: float

class RetryConfig(BaseModel):
    """Configuration for retry behavior.

    Attributes:
        max_retries (int): Maximum number of retry attempts.
        base_delay (float): Base delay in seconds between retries.
        max_delay (float): Maximum delay in seconds between retries.
        jitter (bool): Whether to add random jitter to delays.
        timeout (float | None): Overall timeout in seconds for the entire operation. If None, timeout is disabled.
        retry_on_exceptions (tuple[type[Exception], ...]): Tuple of exception types to retry on.
    """
    max_retries: int
    base_delay: float
    max_delay: float
    jitter: bool
    timeout: float | None
    retry_on_exceptions: tuple[type[Exception], ...]
    def validate_delay_constraints(self) -> RetryConfig:
        """Validates that max_delay is greater than or equal to base_delay.

        Returns:
            RetryConfig: The validated configuration.

        Raises:
            ValueError: If max_delay is less than base_delay.
        """

@overload
async def retry(func: Callable[..., Any], *args: Any, retry_config: RetryConfig | None = None, **kwargs: Any) -> T: ...
@overload
def retry(config: RetryConfig | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
