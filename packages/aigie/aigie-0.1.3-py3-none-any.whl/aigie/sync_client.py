"""
Synchronous API wrapper for Aigie SDK.

Provides synchronous versions of all Aigie methods for use in non-async codebases.
"""

import asyncio
from typing import Dict, Any, Optional, List
from .client import Aigie
from .config import Config
from .trace import TraceContext
from .span import SpanContext


class AigieSync:
    """
    Synchronous wrapper for Aigie client.
    
    Usage:
        from aigie import AigieSync
        
        aigie = AigieSync()
        aigie.initialize()  # Blocking
        
        with aigie.trace("My Workflow") as trace:
            with trace.span("operation") as span:
                result = do_work()
                span.set_output({"result": result})
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize synchronous Aigie client.
        
        Args:
            api_url: Aigie API URL
            api_key: API key for authentication
            config: Optional Config object
        """
        self._async_client = Aigie(api_url=api_url, api_key=api_key, config=config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we need to use a different approach
                # For now, raise an error suggesting async usage
                raise RuntimeError(
                    "Cannot run sync Aigie in async context. "
                    "Use async Aigie client instead or run in a separate thread."
                )
            return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(coro)
    
    def initialize(self) -> None:
        """Initialize the client (blocking)."""
        self._run_async(self._async_client.initialize())
    
    def trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> "TraceContextSync":
        """
        Create a new trace context manager (synchronous).
        
        Args:
            name: Trace name
            metadata: Optional metadata dictionary
            tags: Optional list of tags
            
        Returns:
            TraceContextSync manager
        """
        # Create the async trace context
        async_trace_ctx = self._async_client.trace(name, metadata=metadata, tags=tags)
        # Create sync wrapper that will handle async context manager
        return TraceContextSync(async_trace_ctx, self)
    
    @property
    def callback(self):
        """Get LangChain callback handler."""
        return self._async_client.callback
    
    def remediate(self, trace_id: str, error: Exception) -> Dict[str, Any]:
        """Trigger autonomous remediation (blocking)."""
        return self._run_async(self._async_client.remediate(trace_id, error))
    
    def detect_precursors(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect error precursors (blocking)."""
        return self._run_async(self._async_client.detect_precursors(context))
    
    def apply_preventive_fix(self, trace_id: str, precursors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply preventive fixes (blocking)."""
        return self._run_async(self._async_client.apply_preventive_fix(trace_id, precursors))
    
    def flush(self) -> None:
        """Manually flush all buffered events (blocking)."""
        self._run_async(self._async_client.flush())
    
    def close(self) -> None:
        """Close the client (blocking)."""
        self._run_async(self._async_client.close())
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class TraceContextSync:
    """Synchronous wrapper for TraceContext."""
    
    def __init__(self, async_trace_ctx, sync_client: "AigieSync"):
        self._async_trace_ctx = async_trace_ctx
        self._async_trace: Optional[TraceContext] = None
        self._sync_client = sync_client
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        return self._sync_client._run_async(coro)
    
    @property
    def id(self) -> Optional[str]:
        """Get trace ID."""
        if self._async_trace:
            return self._async_trace.id
        return None
    
    @property
    def name(self) -> str:
        """Get trace name."""
        if self._async_trace:
            return self._async_trace.name
        return ""
    
    def span(
        self,
        name: str,
        type: str = "tool",
        parent: Optional[str] = None
    ) -> "SpanContextSync":
        """Create a span (synchronous)."""
        if not self._async_trace:
            raise RuntimeError("Trace not initialized. Use 'with trace:' first.")
        async_span = self._async_trace.span(name, type=type, parent=parent)
        return SpanContextSync(async_span, self)
    
    def complete(self, status: str = "success", error: Optional[Exception] = None) -> None:
        """Manually complete the trace (blocking)."""
        if self._async_trace:
            self._run_async(self._async_trace.complete(status, error))
    
    def __enter__(self):
        """Context manager entry."""
        self._async_trace = self._run_async(self._async_trace_ctx.__aenter__())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._async_trace:
            self._run_async(self._async_trace.__aexit__(exc_type, exc_val, exc_tb))


class SpanContextSync:
    """Synchronous wrapper for SpanContext."""
    
    def __init__(self, async_span: SpanContext, trace_context: TraceContextSync):
        self._async_span = async_span
        self._trace_context = trace_context
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        return self._trace_context._run_async(coro)
    
    @property
    def id(self) -> Optional[str]:
        """Get span ID."""
        return self._async_span.id
    
    def set_input(self, data: Dict[str, Any]) -> None:
        """Set span input data."""
        self._async_span.set_input(data)
    
    def set_output(self, data: Dict[str, Any]) -> None:
        """Set span output data."""
        self._async_span.set_output(data)
    
    def set_metadata(self, data: Dict[str, Any]) -> None:
        """Set span metadata."""
        self._async_span.set_metadata(data)
    
    def complete(self, status: str = "success", error: Optional[Exception] = None) -> None:
        """Manually complete the span (blocking)."""
        self._run_async(self._async_span.complete(status, error))
    
    def __enter__(self):
        """Context manager entry."""
        self._run_async(self._async_span.__aenter__())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._run_async(self._async_span.__aexit__(exc_type, exc_val, exc_tb))

