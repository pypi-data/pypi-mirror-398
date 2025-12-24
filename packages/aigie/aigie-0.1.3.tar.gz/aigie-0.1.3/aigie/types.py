"""
Type definitions for Aigie SDK.

This module provides type hints and type aliases for better IDE support.
"""

from typing import Dict, Any, Optional, List, Union, Literal
from typing_extensions import TypedDict, NotRequired

# Status types
TraceStatus = Literal["success", "failure", "error", "timeout", "cancelled", "running"]
SpanStatus = Literal["success", "failure", "error"]
SpanType = Literal["llm", "tool", "agent", "chain", "workflow"]

# Metadata and tags
Metadata = Dict[str, Any]
Tags = List[str]

# API request/response types
class TraceCreateRequest(TypedDict):
    """Request payload for creating a trace."""
    name: str
    status: NotRequired[TraceStatus]
    metadata: NotRequired[Metadata]
    tags: NotRequired[Tags]
    spans: NotRequired[List[Dict[str, Any]]]

class TraceUpdateRequest(TypedDict):
    """Request payload for updating a trace."""
    status: NotRequired[TraceStatus]
    error_message: NotRequired[str]
    error_type: NotRequired[str]
    spans: NotRequired[List[Dict[str, Any]]]

class SpanCreateRequest(TypedDict):
    """Request payload for creating a span."""
    trace_id: str
    name: str
    type: SpanType
    input: NotRequired[Dict[str, Any]]
    output: NotRequired[Dict[str, Any]]
    metadata: NotRequired[Metadata]
    parent_id: NotRequired[str]

class SpanUpdateRequest(TypedDict):
    """Request payload for updating a span."""
    input: NotRequired[Dict[str, Any]]
    output: NotRequired[Dict[str, Any]]
    status: NotRequired[SpanStatus]
    error_message: NotRequired[str]

# Response types
class TraceResponse(TypedDict):
    """Response from trace API."""
    id: str
    name: str
    status: TraceStatus
    metadata: Metadata
    tags: Tags
    start_time: NotRequired[str]
    end_time: NotRequired[str]
    duration_ns: NotRequired[int]

class SpanResponse(TypedDict):
    """Response from span API."""
    id: str
    trace_id: str
    name: str
    type: SpanType
    input: Dict[str, Any]
    output: Dict[str, Any]
    metadata: Metadata
    status: NotRequired[SpanStatus]
    parent_id: NotRequired[str]
    start_time: NotRequired[str]
    end_time: NotRequired[str]
    duration_ns: NotRequired[int]

# Configuration types
class RetryConfig(TypedDict):
    """Retry configuration."""
    max_retries: int
    base_delay: float
    max_delay: float
    exponential_base: float
    jitter: bool

class BufferConfig(TypedDict):
    """Buffer configuration."""
    max_size: int
    flush_interval: float
    enable_buffering: bool








