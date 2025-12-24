"""
Retry and timeout utilities for CrewAI integration.

Provides decorators and context managers for handling transient failures
with exponential backoff and configurable timeouts.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Common transient errors that should be retried
TRANSIENT_ERRORS = (
    TimeoutError,
    ConnectionError,
    ConnectionResetError,
    ConnectionRefusedError,
    OSError,  # Includes network errors
)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_error: Optional[Exception] = None, attempts: int = 0):
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts


class TimeoutExceededError(Exception):
    """Raised when an operation exceeds its timeout."""

    def __init__(self, message: str, timeout: float, operation: str = ""):
        super().__init__(message)
        self.timeout = timeout
        self.operation = operation


class CrewExecutionError(Exception):
    """Raised when a CrewAI crew execution fails."""

    def __init__(self, message: str, task: Optional[str] = None, agent: Optional[str] = None):
        super().__init__(message)
        self.task = task
        self.agent = agent


async def with_timeout(
    coro: Any,
    timeout: float,
    operation_name: str = "operation",
) -> Any:
    """Execute a coroutine with a timeout.

    Args:
        coro: The coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name of the operation (for error messages)

    Returns:
        The result of the coroutine

    Raises:
        TimeoutExceededError: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutExceededError(
            f"{operation_name} timed out after {timeout}s",
            timeout=timeout,
            operation=operation_name,
        )


async def with_retry(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    operation_name: str = "operation",
    **kwargs,
) -> Any:
    """Execute a function with retry logic.

    Uses exponential backoff between retries.

    Args:
        func: The async function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (doubles each retry)
        retry_on: List of exception types to retry on (None = use defaults)
        operation_name: Name of the operation (for logging)
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function

    Raises:
        RetryExhaustedError: If all retries are exhausted
    """
    retry_errors = tuple(retry_on) if retry_on else TRANSIENT_ERRORS
    last_error: Optional[Exception] = None
    delay = retry_delay

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except retry_errors as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"{operation_name} failed after {max_retries + 1} attempts: {e}"
                )

        except Exception as e:
            # Non-retryable error
            raise

    raise RetryExhaustedError(
        f"{operation_name} failed after {max_retries + 1} attempts",
        last_error=last_error,
        attempts=max_retries + 1,
    )


async def with_timeout_and_retry(
    func: Callable[..., Any],
    *args,
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    operation_name: str = "operation",
    **kwargs,
) -> Any:
    """Execute a function with both timeout and retry logic.

    Each attempt has its own timeout. Retries are attempted if the operation
    times out or encounters a transient error.

    Args:
        func: The async function to execute
        *args: Positional arguments for the function
        timeout: Timeout per attempt in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        retry_on: List of exception types to retry on
        operation_name: Name of the operation
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function
    """
    # Include TimeoutExceededError in retryable errors
    retry_errors = list(retry_on) if retry_on else list(TRANSIENT_ERRORS)
    retry_errors.append(TimeoutExceededError)
    retry_errors.append(asyncio.TimeoutError)

    async def timed_func(*a, **kw):
        if asyncio.iscoroutinefunction(func):
            return await with_timeout(func(*a, **kw), timeout, operation_name)
        else:
            return func(*a, **kw)

    return await with_retry(
        timed_func,
        *args,
        max_retries=max_retries,
        retry_delay=retry_delay,
        retry_on=retry_errors,
        operation_name=operation_name,
        **kwargs,
    )


def retry_decorator(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    timeout: Optional[float] = None,
):
    """Decorator to add retry logic to an async function.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        retry_on: List of exception types to retry on
        timeout: Optional timeout per attempt

    Example:
        @retry_decorator(max_retries=3, timeout=30.0)
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            operation_name = func.__name__

            if timeout:
                return await with_timeout_and_retry(
                    func,
                    *args,
                    timeout=timeout,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    retry_on=retry_on,
                    operation_name=operation_name,
                    **kwargs,
                )
            else:
                return await with_retry(
                    func,
                    *args,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    retry_on=retry_on,
                    operation_name=operation_name,
                    **kwargs,
                )

        return wrapper
    return decorator


class RetryContext:
    """Context manager for retry operations with metrics tracking.

    Tracks retry attempts, total time, and errors for observability.

    Example:
        async with RetryContext(max_retries=3, operation="crew_kickoff") as ctx:
            result = await ctx.execute(crew.kickoff_async, inputs)
            print(f"Completed in {ctx.total_time}s with {ctx.attempts} attempts")
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        retry_on: Optional[List[Type[Exception]]] = None,
        operation: str = "operation",
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.retry_on = retry_on
        self.operation = operation

        # Metrics
        self.attempts = 0
        self.total_time = 0.0
        self.errors: List[Exception] = []
        self.success = False
        self._start_time: Optional[float] = None

    async def __aenter__(self) -> "RetryContext":
        self._start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._start_time:
            self.total_time = time.perf_counter() - self._start_time
        return False  # Don't suppress exceptions

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute the function with retry logic.

        Args:
            func: The async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the function
        """
        retry_errors = tuple(self.retry_on) if self.retry_on else TRANSIENT_ERRORS
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            self.attempts = attempt + 1

            try:
                if self.timeout:
                    result = await with_timeout(
                        func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs),
                        self.timeout,
                        self.operation,
                    )
                else:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                self.success = True
                return result

            except (TimeoutExceededError, asyncio.TimeoutError, *retry_errors) as e:
                self.errors.append(e)

                if attempt < self.max_retries:
                    logger.warning(
                        f"{self.operation} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise RetryExhaustedError(
                        f"{self.operation} failed after {self.max_retries + 1} attempts",
                        last_error=e,
                        attempts=self.attempts,
                    )

            except Exception as e:
                self.errors.append(e)
                raise

    def get_metrics(self) -> dict:
        """Get retry metrics for tracing."""
        return {
            "attempts": self.attempts,
            "total_time": self.total_time,
            "success": self.success,
            "error_count": len(self.errors),
            "errors": [str(e) for e in self.errors[-3:]],  # Last 3 errors
        }


class CrewRetryContext(RetryContext):
    """Specialized retry context for CrewAI operations.

    Tracks additional crew-specific metrics like tasks completed and agent steps.

    Example:
        async with CrewRetryContext(max_retries=3, operation="crew_run") as ctx:
            result = await ctx.execute(crew.kickoff_async, inputs)
            print(f"Tasks completed: {ctx.tasks_completed}")
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        retry_on: Optional[List[Type[Exception]]] = None,
        operation: str = "crew_execution",
    ):
        super().__init__(max_retries, retry_delay, timeout, retry_on, operation)
        self.tasks_completed: List[str] = []
        self.agent_steps: List[Dict[str, Any]] = []
        self.failed_task: Optional[str] = None
        self.failed_agent: Optional[str] = None

    def record_task(self, task_description: str) -> None:
        """Record a completed task."""
        self.tasks_completed.append(task_description)

    def record_agent_step(self, agent_role: str, step_info: Dict[str, Any]) -> None:
        """Record an agent step."""
        self.agent_steps.append({
            "agent": agent_role,
            **step_info,
        })

    def record_failure(self, task: Optional[str] = None, agent: Optional[str] = None) -> None:
        """Record where failure occurred."""
        self.failed_task = task
        self.failed_agent = agent

    def get_metrics(self) -> dict:
        """Get crew-specific retry metrics for tracing."""
        base_metrics = super().get_metrics()
        base_metrics.update({
            "tasks_completed": self.tasks_completed,
            "agent_step_count": len(self.agent_steps),
            "failed_task": self.failed_task,
            "failed_agent": self.failed_agent,
        })
        return base_metrics
