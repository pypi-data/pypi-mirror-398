"""
Decorator utilities for Aigie SDK.
"""

import functools
import asyncio
from typing import Any, Callable, Optional, Dict, List


class TraceDecorator:
    """
    Decorator class for tracing functions.
    
    Supports both:
    - @aigie.trace (no parentheses)
    - @aigie.trace(name="function") (with parentheses)
    """
    
    def __init__(self, aigie_client, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None):
        self.aigie = aigie_client
        self.name = name
        self.metadata = metadata or {}
        self.tags = tags or []
    
    def __call__(self, func: Optional[Callable] = None, *, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None):
        """
        Called when decorator is used.
        
        If func is provided, it's being used as @aigie.trace (no parentheses)
        If func is None, it's being used as @aigie.trace() (with parentheses)
        """
        # If called with keyword args, update them
        if name is not None:
            self.name = name
        if metadata is not None:
            self.metadata = metadata
        if tags is not None:
            self.tags = tags
        
        # If func is provided, we're decorating it directly
        if func is not None:
            return self._decorate(func)
        
        # Otherwise, return a decorator function
        def decorator(f):
            return self._decorate(f)
        return decorator
    
    def _decorate(self, func: Callable):
        """Internal method to create the decorated function."""
        trace_name = self.name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self.aigie.trace(trace_name, metadata=self.metadata, tags=self.tags) as trace:
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        await trace.complete(status="failure", error=e)
                        raise
            
            return async_wrapper
        else:
            # Sync function - for now raise error, can be enhanced later
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                raise RuntimeError(
                    f"Function {func.__name__} is not async. "
                    "Use async def or use trace context manager directly."
                )
            return sync_wrapper


class SpanDecorator:
    """
    Decorator class for creating spans.
    
    Usage:
        @trace.span(name="operation", type="llm")
        async def operation():
            pass
    """
    
    def __init__(self, trace_context, name: Optional[str] = None, type: str = "tool"):
        self.trace = trace_context
        self.name = name
        self.span_type = type
    
    def __call__(self, func: Optional[Callable] = None, *, name: Optional[str] = None, type: Optional[str] = None):
        """Called when decorator is used."""
        if name is not None:
            self.name = name
        if type is not None:
            self.span_type = type
        
        if func is not None:
            return self._decorate(func)
        
        def decorator(f):
            return self._decorate(f)
        return decorator
    
    def _decorate(self, func: Callable):
        """Internal method to create the decorated function."""
        span_name = self.name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self.trace.span(span_name, type=self.span_type) as span:
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        # Error will be captured in span.__aexit__
                        raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                raise RuntimeError(
                    f"Function {func.__name__} is not async. "
                    "Use async def or use span context manager directly."
                )
            return sync_wrapper








