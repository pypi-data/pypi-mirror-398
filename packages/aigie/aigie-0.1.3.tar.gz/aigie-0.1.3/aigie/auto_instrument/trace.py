"""
Automatic trace creation for workflows.

Provides utilities to automatically create traces when workflows start,
without requiring manual trace creation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable to track current trace
_current_trace: ContextVar[Optional[Any]] = ContextVar('_current_trace', default=None)


async def get_or_create_trace(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
) -> Any:
    """
    Get current trace or create a new one if none exists.
    
    This is used by auto-instrumentation to ensure traces exist
    without requiring manual creation.
    
    Args:
        name: Trace name
        metadata: Optional metadata
        tags: Optional tags
    
    Returns:
        TraceContext instance
    """
    from ..client import get_aigie
    
    # Check if we already have a trace in context
    current = _current_trace.get()
    if current:
        return current
    
    # Get global aigie instance
    aigie = get_aigie()
    if not aigie or not aigie._initialized:
        # No aigie instance, return None (instrumentation will skip)
        return None
    
    # Create new trace
    try:
        trace = aigie.trace(
            name=name,
            metadata=metadata or {},
            tags=tags or []
        )
        
        # Enter the trace context (it's an async context manager)
        trace_context = await trace.__aenter__()
        
        # Store in context variable
        _current_trace.set(trace_context)
        
        return trace_context
    except Exception as e:
        logger.warning(f"Failed to create auto-trace: {e}")
        return None


def get_current_trace() -> Optional[Any]:
    """Get the current trace from context."""
    return _current_trace.get()


def set_current_trace(trace: Optional[Any]) -> None:
    """Set the current trace in context."""
    _current_trace.set(trace)


def clear_current_trace() -> None:
    """Clear the current trace from context."""
    _current_trace.set(None)


def get_or_create_trace_sync(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
) -> Any:
    """
    Synchronous version of get_or_create_trace.
    
    This handles sync contexts by running async code in a new event loop
    if needed, or reusing existing loop if available.
    
    Args:
        name: Trace name
        metadata: Optional metadata
        tags: Optional tags
    
    Returns:
        TraceContext instance or None
    """
    # Check if we already have a trace in context
    current = _current_trace.get()
    if current:
        return current
    
    # Try to get trace synchronously
    try:
        # Check if we're in an async context
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop:
            # We're in an async context - can't use sync version
            # Return None and let async version handle it
            return None
        
        # No running loop - we can create one
        return asyncio.run(get_or_create_trace(name, metadata, tags))
    except Exception as e:
        logger.warning(f"Failed to create sync trace: {e}")
        return None

