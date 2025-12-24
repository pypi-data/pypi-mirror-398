"""
Span Context Manager for Aigie.
"""

import asyncio
from typing import Dict, Any, Optional, TYPE_CHECKING
from uuid import uuid4
import httpx
from .buffer import EventBuffer, EventType

if TYPE_CHECKING:
    from .trace import TraceContext


class SpanContext:
    """
    Context manager for creating and managing spans.
    
    Usage:
        async with trace.span("operation", type="llm") as span:
            span.set_input({"prompt": "Hello"})
            result = await llm.ainvoke("Hello")
            span.set_output({"response": result})
    """
    
    def __init__(
        self,
        client: httpx.AsyncClient,
        api_url: str,
        trace_id: str,
        name: str,
        span_type: str,
        parent_id: Optional[str] = None,
        buffer: Optional[EventBuffer] = None
    ):
        self.client = client
        self.api_url = api_url
        self.buffer = buffer
        self.trace_id = trace_id
        self.name = name
        self.span_type = span_type
        self.parent_id = parent_id
        # Pre-generate ID so children can reference it before span is entered
        self.id: str = str(uuid4())
        self._input: Dict[str, Any] = {}
        self._output: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        # Public property for accessing output (used by use-case apps)
        self.output: Dict[str, Any] = {}

        # LLM-specific fields (for Generation/LLM spans)
        self._model: Optional[str] = None
        self._prompt_tokens: int = 0
        self._completion_tokens: int = 0
        self._total_tokens: int = 0
        self._input_cost: float = 0.0
        self._output_cost: float = 0.0
        self._total_cost: float = 0.0
        self._level: Optional[str] = None  # ERROR, WARNING, INFO
        self._status_message: Optional[str] = None
        self._start_time: Optional[Any] = None  # Set in __aenter__

        # Additional fields for observability
        self._completion_start_time: Optional[Any] = None  # TTFT - Time to First Token
        self._model_parameters: Optional[Dict[str, Any]] = None  # Model config (temperature, etc)
        self._latency_seconds: Optional[float] = None  # Total latency in seconds
        self._agent_type: Optional[str] = None  # Agent type for dashboard grouping
    
    async def __aenter__(self):
        """Create the span when entering context."""
        from datetime import datetime

        # ID is pre-generated in __init__ so children can reference it
        # Store start_time for later use in SPAN_UPDATE
        self._start_time = datetime.utcnow()

        payload = {
            "id": self.id,
            "trace_id": self.trace_id,
            "name": self.name,
            "type": self.span_type,
            "start_time": self._start_time.isoformat(),
            "input": self._input,
            "output": self._output,
            "metadata": self._metadata
        }
        
        # Add parent_id as direct field (not in metadata)
        if self.parent_id:
            payload["parent_id"] = self.parent_id
        
        # Use buffer if available, otherwise send directly with retry logic
        if self.buffer:
            # IMPORTANT: When using buffer, we DON'T send SPAN_CREATE here.
            # Instead, we only send SPAN_UPDATE in __aexit__ which contains ALL data
            # (name, type, start_time, end_time, tokens, model, etc.)
            # This ensures all span data arrives in a single event, avoiding the
            # timing issue where SPAN_CREATE and SPAN_UPDATE get split into separate
            # batches and the backend fails to merge them properly.
            # The start_time is already recorded above, so we just return.
            return self
        else:
            # Direct API call with retry logic (original behavior)
            max_retries = 3
            base_delay = 0.1
            
            for attempt in range(max_retries):
                try:
                    response = await self.client.post(
                        f"{self.api_url}/v1/spans",
                        json=payload,
                        timeout=10.0
                    )
                    
                    if response.status_code == 404:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"⚠️  Span creation failed (404), retrying in {delay*1000:.0f}ms (attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            response.raise_for_status()
                    
                    response.raise_for_status()
                    span_data = response.json()
                    self.id = span_data.get("id", self.id)
                    return self
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 404 or attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
            
            raise RuntimeError("Failed to create span after retries")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Update the span when exiting context."""
        from datetime import datetime

        if self.id:
            status = "failure" if exc_val else "success"
            end_time = datetime.utcnow()

            data = {
                "id": self.id,  # Include ID for buffered updates
                "span_id": self.id,  # Alternative field name
                "trace_id": self.trace_id,  # Required by backend for span updates
                "name": self.name,  # Include name for merge fallback
                "type": self.span_type,  # Include type for merge fallback
                "start_time": self._start_time.isoformat() if self._start_time else None,  # For merge fallback
                "input": self._input,
                "output": self._output,
                "metadata": self._metadata,  # Include metadata
                "status": status,
                "end_time": end_time.isoformat()
            }

            # Include parent_id for merge fallback (in case span-create wasn't processed yet)
            if self.parent_id:
                data["parent_id"] = self.parent_id

            if exc_val:
                data["error_message"] = str(exc_val)
                data["error_type"] = type(exc_val).__name__

            # Include LLM-specific fields if set
            if self._model:
                data["model"] = self._model

            # Include usage object in multiple formats for maximum compatibility
            # Different backends expect different field names
            if self._prompt_tokens > 0 or self._completion_tokens > 0 or self._total_tokens > 0 or \
               self._input_cost > 0 or self._output_cost > 0 or self._total_cost > 0:
                # Format 1: usage.input/output
                data["usage"] = {
                    "input": self._prompt_tokens,
                    "output": self._completion_tokens,
                    "total": self._total_tokens,
                    "unit": "TOKENS",
                    "input_cost": self._input_cost if self._input_cost > 0 else None,
                    "output_cost": self._output_cost if self._output_cost > 0 else None,
                    "total_cost": self._total_cost if self._total_cost > 0 else None,
                }

                # Format 2: token_usage.prompt_tokens/completion_tokens (backend extraction format)
                data["token_usage"] = {
                    "prompt_tokens": self._prompt_tokens,
                    "completion_tokens": self._completion_tokens,
                    "total_tokens": self._total_tokens,
                    "input_cost": self._input_cost if self._input_cost > 0 else None,
                    "output_cost": self._output_cost if self._output_cost > 0 else None,
                    "total_cost": self._total_cost if self._total_cost > 0 else None,
                }

            # Also include direct fields for backward compatibility with older backends
            if self._prompt_tokens > 0 or self._completion_tokens > 0 or self._total_tokens > 0:
                data["prompt_tokens"] = self._prompt_tokens
                data["completion_tokens"] = self._completion_tokens
                data["total_tokens"] = self._total_tokens
            if self._input_cost > 0 or self._output_cost > 0 or self._total_cost > 0:
                data["input_cost"] = self._input_cost
                data["output_cost"] = self._output_cost
                data["total_cost"] = self._total_cost
            if self._level:
                data["level"] = self._level
            if self._status_message:
                data["status_message"] = self._status_message

            # Include additional observability fields
            if self._completion_start_time:
                data["completion_start_time"] = self._completion_start_time.isoformat() if hasattr(self._completion_start_time, 'isoformat') else str(self._completion_start_time)
                # Also calculate TTFT if we have start_time
                if self._start_time and hasattr(self._completion_start_time, 'timestamp'):
                    ttft_ms = (self._completion_start_time - self._start_time).total_seconds() * 1000
                    data["time_to_first_token_ms"] = ttft_ms
                    # Add to metadata for compatibility
                    if "metadata" not in data:
                        data["metadata"] = {}
                    data["metadata"]["time_to_first_token_ms"] = ttft_ms

            if self._model_parameters:
                data["model_parameters"] = self._model_parameters

            if self._latency_seconds is not None:
                data["latency_seconds"] = self._latency_seconds
            elif self._start_time:
                # Calculate latency from start to end
                latency = (end_time - self._start_time).total_seconds()
                data["latency_seconds"] = latency

            if self._agent_type:
                data["agent_type"] = self._agent_type
                # Also add to metadata for backward compatibility
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"]["agent_type"] = self._agent_type

            # Ensure metadata has token_usage (input_tokens, output_tokens, total_tokens)
            if self._prompt_tokens > 0 or self._completion_tokens > 0 or self._total_tokens > 0:
                if "metadata" not in data:
                    data["metadata"] = {}
                # Token usage object
                data["metadata"]["token_usage"] = {
                    "input_tokens": self._prompt_tokens,
                    "output_tokens": self._completion_tokens,
                    "total_tokens": self._total_tokens,
                    "unit": "TOKENS"
                }
                # Also add direct fields in metadata for backend extraction
                data["metadata"]["prompt_tokens"] = self._prompt_tokens
                data["metadata"]["completion_tokens"] = self._completion_tokens
                data["metadata"]["total_tokens"] = self._total_tokens
                if self._total_cost > 0:
                    data["metadata"]["cost"] = self._total_cost
                    data["metadata"]["estimated_cost"] = self._total_cost
                    data["metadata"]["input_cost"] = self._input_cost
                    data["metadata"]["output_cost"] = self._output_cost
                    data["metadata"]["total_cost"] = self._total_cost

            # Add model to metadata for backend extraction
            if self._model:
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"]["model"] = self._model

            # Add model_parameters to metadata for backend extraction
            if self._model_parameters:
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"]["model_parameters"] = self._model_parameters

            # Use buffer if available, otherwise send directly
            if self.buffer:
                # Since we don't send SPAN_CREATE in __aenter__ when using buffer,
                # we send SPAN_CREATE here with the complete span data.
                # This ensures the span is created with all data in one event.
                await self.buffer.add(EventType.SPAN_CREATE, data)
            else:
                await self.client.put(
                    f"{self.api_url}/v1/spans/{self.id}",
                    json=data
                )
    
    def set_input(self, data: Dict[str, Any]) -> None:
        """Set span input data."""
        self._input = data
        # Note: Input will be included in __aexit__ update
        # If immediate update needed, use await span.update_input() instead
    
    def set_output(self, data: Dict[str, Any]) -> None:
        """Set span output data."""
        self._output = data
        self.output = data  # Update public property for local access
    
    def set_metadata(self, data: Dict[str, Any]) -> None:
        """Set span metadata."""
        self._metadata = data

    def set_model(self, model: str) -> None:
        """Set the model name for LLM spans."""
        self._model = model

    def set_usage(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: Optional[int] = None,
        input_cost: float = 0.0,
        output_cost: float = 0.0,
        total_cost: Optional[float] = None
    ) -> None:
        """Set token usage and cost data for LLM spans."""
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._total_tokens = total_tokens if total_tokens is not None else (prompt_tokens + completion_tokens)
        self._input_cost = input_cost
        self._output_cost = output_cost
        self._total_cost = total_cost if total_cost is not None else (input_cost + output_cost)

    def set_level(self, level: str, status_message: Optional[str] = None) -> None:
        """Set the log level and optional status message (for errors)."""
        self._level = level
        if status_message:
            self._status_message = status_message

    def set_completion_start_time(self, completion_start_time: Any) -> None:
        """Set the completion start time (Time to First Token)."""
        self._completion_start_time = completion_start_time

    def set_model_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set model parameters (temperature, top_p, etc.)."""
        self._model_parameters = parameters

    def set_latency(self, latency_seconds: float) -> None:
        """Set the total latency in seconds."""
        self._latency_seconds = latency_seconds

    def set_agent_type(self, agent_type: str) -> None:
        """Set the agent type for dashboard grouping."""
        self._agent_type = agent_type

    async def update_input(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Update span input immediately (if span already created)."""
        if data:
            self._input = data
        if self.id:
            await self.client.put(
                f"{self.api_url}/v1/spans/{self.id}",
                json={"input": self._input}
            )
    
    async def complete(self, status: str = "success", error: Optional[Exception] = None) -> None:
        """
        Manually complete the span.
        
        Args:
            status: Span status (success, failure)
            error: Optional error exception
        """
        if not self.id:
            return
        
        data = {
            "id": self.id,
            "span_id": self.id,
            "trace_id": self.trace_id,  # Required by backend for span updates
            "output": self._output,
            "status": status
        }
        if error:
            data["error_message"] = str(error)
        
        # Use buffer if available
        if self.buffer:
            await self.buffer.add(EventType.SPAN_UPDATE, data)
        else:
            await self.client.put(
                f"{self.api_url}/v1/spans/{self.id}",
                json=data
            )

