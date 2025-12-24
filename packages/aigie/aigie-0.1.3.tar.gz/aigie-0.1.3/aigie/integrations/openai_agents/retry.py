"""
Retry and timeout utilities for OpenAI Agents SDK integration.

Provides decorators and context managers for handling transient failures
with exponential backoff and configurable timeouts.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, List, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Common transient errors that should be retried
TRANSIENT_ERRORS = (
    TimeoutError,
    ConnectionError,
    ConnectionResetError,
    ConnectionRefusedError,
    OSError,
)


class AgentExecutionError(Exception):
    """Raised when an agent execution fails."""

    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        phase: Optional[str] = None,
    ):
        super().__init__(message)
        self.agent_name = agent_name
        self.phase = phase  # generation, tool_call, handoff, etc.


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


async def with_timeout(
    coro: Any,
    timeout: float,
    operation_name: str = "operation",
) -> Any:
    """Execute a coroutine with a timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name for error messages

    Returns:
        Result of the coroutine

    Raises:
        TimeoutExceededError: If timeout is exceeded
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

    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries (doubles each retry)
        retry_on: List of exception types to retry on
        operation_name: Name for logging
        **kwargs: Keyword arguments for func

    Returns:
        Result of the function

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

        except Exception:
            # Non-retryable error, re-raise immediately
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

    Args:
        func: Function to execute
        *args: Positional arguments for func
        timeout: Timeout per attempt in seconds
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries
        retry_on: List of exception types to retry on
        operation_name: Name for logging
        **kwargs: Keyword arguments for func

    Returns:
        Result of the function
    """
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
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries
        retry_on: List of exception types to retry on
        timeout: Optional timeout per attempt

    Returns:
        Decorated function
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

    Example:
        async with RetryContext(max_retries=3, timeout=30.0) as ctx:
            result = await ctx.execute(some_async_function, arg1, arg2)
            print(ctx.get_metrics())
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
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the function
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
        """Get retry metrics for tracing.

        Returns:
            Dictionary with retry metrics
        """
        return {
            "attempts": self.attempts,
            "total_time": self.total_time,
            "success": self.success,
            "error_count": len(self.errors),
            "errors": [str(e) for e in self.errors[-3:]],  # Last 3 errors
        }


class WorkflowRetryContext(RetryContext):
    """Specialized retry context for OpenAI Agents SDK workflows.

    Tracks additional metrics specific to agent workflows.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        retry_on: Optional[List[Type[Exception]]] = None,
        operation: str = "workflow",
    ):
        super().__init__(max_retries, retry_delay, timeout, retry_on, operation)

        # Workflow-specific metrics
        self.agents_executed: int = 0
        self.generations: int = 0
        self.tool_calls: int = 0
        self.handoffs: int = 0
        self.failed_agent: Optional[str] = None
        self.failed_phase: Optional[str] = None

    def record_agent(self, agent_name: str) -> None:
        """Record an agent execution."""
        self.agents_executed += 1

    def record_generation(self) -> None:
        """Record a generation."""
        self.generations += 1

    def record_tool_call(self) -> None:
        """Record a tool call."""
        self.tool_calls += 1

    def record_handoff(self) -> None:
        """Record a handoff."""
        self.handoffs += 1

    def record_failure(self, agent: Optional[str] = None, phase: Optional[str] = None) -> None:
        """Record where failure occurred.

        Args:
            agent: Agent that failed
            phase: Phase that failed (generation, tool_call, handoff, guardrail)
        """
        self.failed_agent = agent
        self.failed_phase = phase

    def get_metrics(self) -> dict:
        """Get workflow-specific retry metrics for tracing.

        Returns:
            Dictionary with retry metrics
        """
        base_metrics = super().get_metrics()
        base_metrics.update({
            "agents_executed": self.agents_executed,
            "generations": self.generations,
            "tool_calls": self.tool_calls,
            "handoffs": self.handoffs,
            "failed_agent": self.failed_agent,
            "failed_phase": self.failed_phase,
        })
        return base_metrics
