"""
Context propagation system for automatic trace/span relationships.

This module provides automatic context propagation using Python's contextvars,
enabling seamless parent-child relationships without manual ID passing.
"""

import contextvars
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


# Context variables for thread-safe trace context propagation
_current_trace_context: contextvars.ContextVar[Optional["RunContext"]] = contextvars.ContextVar(
    "_current_trace_context", default=None
)

_current_span_context: contextvars.ContextVar[Optional["RunContext"]] = contextvars.ContextVar(
    "_current_span_context", default=None
)

# Global configuration context
_global_tags: contextvars.ContextVar[Optional[List[str]]] = contextvars.ContextVar(
    "_global_tags", default=None
)

_global_metadata: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "_global_metadata", default=None
)

_tracing_enabled: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_tracing_enabled", default=True
)

_project_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_project_name", default=None
)


@dataclass
class RunContext:
    """
    Execution context for a trace or span.

    Contains all contextual information needed for nested execution tracking.
    """
    id: str
    name: str
    type: str  # "trace" or "span"
    span_type: Optional[str] = None  # For spans: "llm", "tool", "agent", etc.
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None

    # Additional context for features
    project_name: Optional[str] = None
    environment: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for API calls."""
        data = {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata,
            "tags": self.tags,
        }

        if self.parent_id:
            data["parent_id"] = self.parent_id
        if self.span_type:
            data["type"] = self.span_type
        if self.project_name:
            data["project_name"] = self.project_name
        if self.environment:
            data["environment"] = self.environment
        if self.user_id:
            data["user_id"] = self.user_id
        if self.session_id:
            data["session_id"] = self.session_id

        return data


def get_current_trace_context() -> Optional[RunContext]:
    """
    Get the current trace context from contextvar.

    Returns:
        Current trace context or None if no trace is active
    """
    return _current_trace_context.get()


def set_current_trace_context(context: Optional[RunContext]) -> None:
    """
    Set the current trace context.

    Args:
        context: Trace context to set
    """
    _current_trace_context.set(context)


def get_current_span_context() -> Optional[RunContext]:
    """
    Get the current span context from contextvar.

    Returns:
        Current span context or None if no span is active
    """
    return _current_span_context.get()


def set_current_span_context(context: Optional[RunContext]) -> None:
    """
    Set the current span context.

    Args:
        context: Span context to set
    """
    _current_span_context.set(context)


def get_parent_context() -> Optional[RunContext]:
    """
    Get the parent context (span if available, otherwise trace).

    This determines what the parent_id should be for a new span.

    Returns:
        Parent context (span > trace > None)
    """
    span_ctx = get_current_span_context()
    if span_ctx:
        return span_ctx

    trace_ctx = get_current_trace_context()
    return trace_ctx


def is_tracing_enabled() -> bool:
    """
    Check if tracing is enabled in current context.

    Returns:
        True if tracing is enabled, False otherwise
    """
    return _tracing_enabled.get()


def set_tracing_enabled(enabled: bool) -> None:
    """
    Enable or disable tracing in current context.

    Args:
        enabled: Whether tracing should be enabled
    """
    _tracing_enabled.set(enabled)


def get_global_tags() -> List[str]:
    """
    Get global tags for current context.

    Returns:
        List of global tags
    """
    return _global_tags.get() or []


def set_global_tags(tags: List[str]) -> None:
    """
    Set global tags for current context.

    Args:
        tags: List of tags to apply to all traces/spans
    """
    _global_tags.set(tags)


def add_global_tags(tags: List[str]) -> None:
    """
    Add tags to global tag list.

    Args:
        tags: Tags to add
    """
    current = get_global_tags()
    current.extend(tags)
    set_global_tags(current)


def get_global_metadata() -> Dict[str, Any]:
    """
    Get global metadata for current context.

    Returns:
        Dictionary of global metadata
    """
    return _global_metadata.get() or {}


def set_global_metadata(metadata: Dict[str, Any]) -> None:
    """
    Set global metadata for current context.

    Args:
        metadata: Metadata to apply to all traces/spans
    """
    _global_metadata.set(metadata)


def add_global_metadata(metadata: Dict[str, Any]) -> None:
    """
    Add metadata to global metadata dict.

    Args:
        metadata: Metadata to add
    """
    current = get_global_metadata()
    current.update(metadata)
    set_global_metadata(current)


def get_project_name() -> Optional[str]:
    """
    Get project name for current context.

    Returns:
        Project name or None
    """
    return _project_name.get()


def set_project_name(name: Optional[str]) -> None:
    """
    Set project name for current context.

    Args:
        name: Project name
    """
    _project_name.set(name)


class tracing_context:
    """
    Context manager for setting tracing configuration.

    Usage:
        with tracing_context(
            enabled=True,
            tags=["production", "critical"],
            metadata={"version": "1.0.0"},
            project_name="customer-support"
        ):
            # All traces/spans created here will inherit these settings
            await my_agent.run()
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project_name: Optional[str] = None,
    ):
        """
        Initialize tracing context manager.

        Args:
            enabled: Whether to enable tracing
            tags: Tags to add to all traces/spans
            metadata: Metadata to add to all traces/spans
            project_name: Project name for grouping
        """
        self.enabled = enabled
        self.tags = tags or []
        self.metadata = metadata or {}
        self.project_name = project_name

        # Store previous values for restoration
        self._prev_enabled = None
        self._prev_tags = None
        self._prev_metadata = None
        self._prev_project = None

    def __enter__(self):
        """Enter context and set values."""
        # Save previous values
        self._prev_enabled = is_tracing_enabled()
        self._prev_tags = get_global_tags().copy()
        self._prev_metadata = get_global_metadata().copy()
        self._prev_project = get_project_name()

        # Set new values
        if self.enabled is not None:
            set_tracing_enabled(self.enabled)
        if self.tags:
            add_global_tags(self.tags)
        if self.metadata:
            add_global_metadata(self.metadata)
        if self.project_name:
            set_project_name(self.project_name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous values."""
        set_tracing_enabled(self._prev_enabled)
        set_global_tags(self._prev_tags)
        set_global_metadata(self._prev_metadata)
        set_project_name(self._prev_project)
        return False


def merge_tags(*tag_lists: Optional[List[str]]) -> List[str]:
    """
    Merge multiple tag lists, removing duplicates while preserving order.

    Args:
        *tag_lists: Variable number of tag lists

    Returns:
        Merged list of unique tags
    """
    seen = set()
    result = []

    # Start with global tags
    for tag in get_global_tags():
        if tag not in seen:
            seen.add(tag)
            result.append(tag)

    # Add tags from provided lists
    for tag_list in tag_lists:
        if tag_list:
            for tag in tag_list:
                if tag not in seen:
                    seen.add(tag)
                    result.append(tag)

    return result


def merge_metadata(*metadata_dicts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple metadata dictionaries.

    Later dicts override earlier ones for conflicting keys.

    Args:
        *metadata_dicts: Variable number of metadata dicts

    Returns:
        Merged metadata dictionary
    """
    result = get_global_metadata().copy()

    for metadata_dict in metadata_dicts:
        if metadata_dict:
            result.update(metadata_dict)

    return result
