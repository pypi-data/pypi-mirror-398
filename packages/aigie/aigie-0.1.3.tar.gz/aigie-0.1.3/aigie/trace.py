"""
Trace Context Manager for Aigie.
"""

import asyncio
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from uuid import uuid4
import httpx
from .span import SpanContext
from .buffer import EventBuffer, EventType
from .sampling import should_send_event

if TYPE_CHECKING:
    from .client import Aigie


class TraceContext:
    """
    Context manager for creating and managing traces.
    
    Usage:
        async with aigie.trace("My Workflow") as trace:
            async with trace.span("operation", type="llm") as span:
                result = await do_work()
                span.set_output({"result": result})
    """
    
    def __init__(
        self,
        client: httpx.AsyncClient,
        api_url: str,
        name: str,
        metadata: Dict[str, Any],
        tags: List[str],
        buffer: Optional[EventBuffer] = None,
        sample_rate: Optional[float] = None
    ):
        self.client = client
        self.api_url = api_url
        self.buffer = buffer
        self.name = name
        self.metadata = metadata
        self.tags = tags
        self.sample_rate = sample_rate
        self.id: Optional[str] = None
        self._spans: List[SpanContext] = []
        self._spans_data: List[Dict[str, Any]] = []  # Store span data to send with trace
        self._prompt: Optional[Any] = None  # Prompt object
        self._trace_context: Optional[Any] = None  # W3C trace context
        self._evaluation_hooks: List[Any] = []  # Evaluation hooks
        self._evaluation_results: List[Dict[str, Any]] = []  # Evaluation results
        self._callback_execution_data: Optional[Dict[str, Any]] = None  # Execution data from callback handler
    
    async def __aenter__(self):
        """Create the trace when entering context."""
        # Track feature usage
        try:
            from .licensing import track_feature
            track_feature("tracing")
        except Exception:
            pass  # Don't fail if tracking fails

        # Set this trace as the current trace for auto-instrumentation
        from .auto_instrument.trace import set_current_trace
        set_current_trace(self)

        if not self.id:
            self.id = str(uuid4())
        # Prepare spans data if any spans were created before trace creation
        spans_data = []
        for span_ctx in self._spans:
            if hasattr(span_ctx, '_input') and hasattr(span_ctx, '_output'):
                spans_data.append({
                    "name": span_ctx.name,
                    "type": span_ctx.span_type,
                    "input": span_ctx._input,
                    "output": span_ctx._output,
                    "metadata": span_ctx._metadata,
                    "parent_id": span_ctx.parent_id
                })
        
        # Ensure session/user tracking metadata is properly structured
        enriched_metadata = dict(self.metadata)
        
        # Standardize session/user tracking keys (if present)
        if "user_id" in enriched_metadata or "userId" in enriched_metadata:
            enriched_metadata["user_id"] = enriched_metadata.get("user_id") or enriched_metadata.get("userId")
        if "session_id" in enriched_metadata or "sessionId" in enriched_metadata:
            enriched_metadata["session_id"] = enriched_metadata.get("session_id") or enriched_metadata.get("sessionId")
        if "environment" in enriched_metadata or "env" in enriched_metadata:
            enriched_metadata["environment"] = enriched_metadata.get("environment") or enriched_metadata.get("env")
        if "release_version" in enriched_metadata or "version" in enriched_metadata:
            enriched_metadata["release_version"] = enriched_metadata.get("release_version") or enriched_metadata.get("version")
        
        # Extract fields from metadata to direct fields
        user_id = enriched_metadata.get("user_id") or enriched_metadata.get("userId")
        session_id = enriched_metadata.get("session_id") or enriched_metadata.get("sessionId")
        environment = enriched_metadata.get("environment") or enriched_metadata.get("env", "default")
        release = enriched_metadata.get("release") or enriched_metadata.get("release_version")
        version = enriched_metadata.get("version")
        input_data = enriched_metadata.get("input")
        output_data = enriched_metadata.get("output")
        
        payload = {
            "id": self.id,
            "name": self.name,
            "status": "running",
            "metadata": enriched_metadata,
            "tags": self.tags,
            "spans": spans_data if spans_data else []
        }
        
        # Add direct fields
        if user_id:
            payload["user_id"] = user_id
        if session_id:
            payload["session_id"] = session_id
        if environment:
            payload["environment"] = environment
        if release:
            payload["release"] = release
        if version:
            payload["version"] = version
        if input_data is not None:
            payload["input"] = input_data
        if output_data is not None:
            payload["output"] = output_data
        
        # Check sampling before sending
        if not should_send_event(self.id, self.sample_rate):
            # Not sampled - skip sending but still return context for local use
            return self
        
        # Use buffer if available, otherwise send directly
        if self.buffer:
            await self.buffer.add(
                EventType.TRACE_CREATE,
                payload
            )
            # Flush immediately to ensure trace is created before any spans
            # This prevents the backend from auto-creating traces for orphan spans
            await self.buffer.flush()
        else:
            # Direct API call (no buffering)
            response = await self.client.post(
                f"{self.api_url}/v1/traces",
                json=payload
            )
            response.raise_for_status()
            trace_data = response.json()
            
            # Handle 207 Multi-Status response (async queue pattern)
            if response.status_code == 207:
                self.id = trace_data.get("trace_id") or trace_data.get("id") or self.id
            else:
                self.id = trace_data.get("id") or self.id
            
            if not self.id:
                raise ValueError(f"Trace ID not found in response: {trace_data}")
        
        return self
    
    def set_callback_execution_data(self, execution_data: Dict[str, Any]) -> None:
        """
        Set execution data from callback handler.
        
        Args:
            execution_data: Dictionary with execution_path, execution_timing, execution_status, execution_errors
        """
        self._callback_execution_data = execution_data
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete the trace when exiting context."""
        from datetime import datetime

        # Clear current trace from context for auto-instrumentation
        from .auto_instrument.trace import clear_current_trace
        clear_current_trace()
        
        # Collect all spans that were created during trace execution
        # Spans are created via separate API calls, but we collect their data
        # to send with the trace update for better atomicity
        spans_data = []
        for span_ctx in self._spans:
            # Include span data even if it was created separately
            # The backend will handle duplicates (check by ID if provided)
            span_data = {
                "name": span_ctx.name,
                "type": span_ctx.span_type,
                "input": span_ctx._input,
                "output": span_ctx._output,
                "metadata": span_ctx._metadata,
            }
            if span_ctx.id:
                span_data["id"] = span_ctx.id
            if span_ctx.parent_id:
                span_data["parent_id"] = span_ctx.parent_id
            spans_data.append(span_data)
        
        if self.id:
            status = "failure" if exc_val else "success"
            error_data = {}
            if exc_val:
                error_data = {
                    "error_message": str(exc_val),
                    "error_type": type(exc_val).__name__
                }
            
            # Set end_time for trace completion
            end_time = datetime.utcnow()
            
            # Try to aggregate cost and tokens from spans
            total_cost = 0.0
            total_tokens = 0
            input_tokens = 0
            output_tokens = 0
            model_names = []
            tool_names = []
            chain_names = []
            
            # Prioritize callback execution data over API fetch
            execution_path = []
            execution_timing = {}
            execution_status = {}
            execution_errors = {}
            
            # Use callback execution data if available
            if self._callback_execution_data:
                execution_path = self._callback_execution_data.get('execution_path', [])
                execution_timing = self._callback_execution_data.get('execution_timing', {})
                execution_status = self._callback_execution_data.get('execution_status', {})
                execution_errors = self._callback_execution_data.get('execution_errors', {})
            
            # Query spans for this trace to aggregate metrics and merge execution data
            try:
                # Check if client is available before making request
                if not self.client:
                    raise ConnectionError("Client not initialized")
                
                # Try the trace-specific spans endpoint
                spans_response = await self.client.get(
                    f"{self.api_url}/v1/spans/trace/{self.id}",
                    timeout=5.0
                )
                spans_list = []
                
                if spans_response.status_code == 200:
                    spans_data = spans_response.json()
                    # Handle paginated response
                    if isinstance(spans_data, dict):
                        if 'items' in spans_data:
                            spans_list = spans_data['items']
                        elif 'data' in spans_data:
                            spans_list = spans_data['data']
                        elif isinstance(spans_data.get('spans'), list):
                            spans_list = spans_data['spans']
                    elif isinstance(spans_data, list):
                        spans_list = spans_data
                    
                    # Merge callback execution data with span data for completeness
                    # Sort spans by start_time to build/merge execution path
                    sorted_spans = sorted(
                        [s for s in spans_list if s.get('start_time')],
                        key=lambda s: s.get('start_time', '')
                    )
                    
                    # If we don't have callback execution data, extract from spans
                    if not self._callback_execution_data:
                        for span in sorted_spans:
                            span_type = span.get('type', '')
                            span_name = span.get('name', '')
                            span_start = span.get('start_time')
                            span_end = span.get('end_time')
                            span_error = span.get('error') or span.get('error_message')
                            
                            # Only include agent, chain, tool, llm, and retriever spans in execution path
                            if span_type in ['agent', 'chain', 'tool', 'llm', 'retriever']:
                                if span_name and span_name not in execution_path:
                                    execution_path.append(span_name)
                                
                                # Build execution timing
                                if span_name and span_start:
                                    timing_data = {
                                        'start_time': span_start,
                                        'end_time': span_end,
                                        'duration_ms': 0
                                    }
                                    
                                    # Calculate duration if we have both start and end
                                    if span_start and span_end:
                                        try:
                                            from datetime import datetime
                                            start_dt = datetime.fromisoformat(span_start.replace('Z', '+00:00'))
                                            end_dt = datetime.fromisoformat(span_end.replace('Z', '+00:00'))
                                            duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
                                            timing_data['duration_ms'] = duration_ms
                                        except Exception:
                                            pass
                                    
                                    execution_timing[span_name] = timing_data
                                
                                # Build execution status
                                if span_name:
                                    if span_error:
                                        execution_status[span_name] = 'failed'
                                        execution_errors[span_name] = span_error
                                    elif span_end:
                                        execution_status[span_name] = 'completed'
                                    else:
                                        execution_status[span_name] = 'running'
                    else:
                        # Merge callback data with span data - add any missing spans from API
                        callback_path_set = set(execution_path)
                        for span in sorted_spans:
                            span_type = span.get('type', '')
                            span_name = span.get('name', '')
                            
                            # Add spans not in callback execution path
                            if span_type in ['agent', 'chain', 'tool', 'llm', 'retriever']:
                                if span_name and span_name not in callback_path_set:
                                    execution_path.append(span_name)
                                    callback_path_set.add(span_name)
                                    
                                    # Add timing if missing
                                    if span_name not in execution_timing:
                                        span_start = span.get('start_time')
                                        span_end = span.get('end_time')
                                        if span_start:
                                            timing_data = {
                                                'start_time': span_start,
                                                'end_time': span_end,
                                                'duration_ms': 0
                                            }
                                            if span_start and span_end:
                                                try:
                                                    from datetime import datetime
                                                    start_dt = datetime.fromisoformat(span_start.replace('Z', '+00:00'))
                                                    end_dt = datetime.fromisoformat(span_end.replace('Z', '+00:00'))
                                                    duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
                                                    timing_data['duration_ms'] = duration_ms
                                                except Exception:
                                                    pass
                                            execution_timing[span_name] = timing_data
                                    
                                    # Add status if missing
                                    if span_name not in execution_status:
                                        span_error = span.get('error') or span.get('error_message')
                                        if span_error:
                                            execution_status[span_name] = 'failed'
                                            execution_errors[span_name] = span_error
                                        elif span.get('end_time'):
                                            execution_status[span_name] = 'completed'
                                        else:
                                            execution_status[span_name] = 'running'
                    
                    # Extract metrics from spans (always do this regardless of callback data)
                    for span in sorted_spans:
                        
                        # Extract token usage and cost from metadata
                        metadata = span.get('metadata', {})
                        token_usage = metadata.get('token_usage', {})
                        
                        if token_usage:
                            if isinstance(token_usage, dict):
                                total_tokens += token_usage.get('total_tokens', 0)
                                input_tokens += token_usage.get('input_tokens', 0)
                                output_tokens += token_usage.get('output_tokens', 0)
                                total_cost += token_usage.get('estimated_cost', 0.0)
                        
                        # Extract model names from LLM spans
                        if span.get('type') == 'llm':
                            model_name = metadata.get('model_name') or metadata.get('model') or span.get('name', '').replace('LLM: ', '')
                            if model_name and model_name not in model_names:
                                model_names.append(model_name)
                        
                        # Extract tool names
                        if span.get('type') == 'tool':
                            tool_name = span.get('name', '')
                            if tool_name and tool_name not in tool_names:
                                tool_names.append(tool_name)
                        
                        # Extract chain names
                        if span.get('type') == 'chain':
                            chain_name = span.get('name', '')
                            if chain_name and chain_name not in chain_names:
                                chain_names.append(chain_name)
            except (ConnectionError, httpx.ConnectError, httpx.TimeoutException) as e:
                # Connection errors are expected when backend is not available
                # Silently continue without aggregation
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Backend not available, skipping span aggregation for trace {self.id}: {e}")
            except Exception as e:
                # Other errors - log but continue
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Failed to aggregate spans for trace {self.id}: {e}")
            
            # Enrich metadata with aggregated information
            enriched_metadata = dict(self.metadata)
            if model_names:
                enriched_metadata['models_used'] = model_names
            if tool_names:
                enriched_metadata['tools_used'] = tool_names
            if chain_names:
                enriched_metadata['chains_used'] = chain_names
            if total_tokens > 0:
                enriched_metadata['token_summary'] = {
                    'total_tokens': total_tokens,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens
                }
            if total_cost > 0:
                enriched_metadata['cost_summary'] = {
                    'total_cost': total_cost
                }
            
            # Add execution data to metadata if available
            if execution_path:
                enriched_metadata['execution_path'] = execution_path
                enriched_metadata['execution_timing'] = execution_timing
                enriched_metadata['execution_status'] = execution_status
                if execution_errors:
                    enriched_metadata['execution_errors'] = execution_errors
                
                # Add edge conditions and agent iterations from callback data if available
                if self._callback_execution_data:
                    if 'edge_conditions' in self._callback_execution_data:
                        enriched_metadata['edge_conditions'] = self._callback_execution_data['edge_conditions']
                    if 'agent_iterations' in self._callback_execution_data:
                        enriched_metadata['agent_iterations'] = self._callback_execution_data['agent_iterations']
            
            # Update trace with final status, end_time, and aggregated metrics
            update_data = {
                "id": self.id,  # Include ID for buffered updates
                "trace_id": self.id,  # Alternative field name
                "status": status,
                "end_time": end_time.isoformat(),
                "total_cost": total_cost if total_cost > 0 else None,
                "total_tokens": total_tokens if total_tokens > 0 else None,
                "metadata": enriched_metadata,
                **error_data
            }
            
            # Include execution data directly in update payload for easier backend processing
            # Always include execution data if available, even if path is empty (for debugging)
            if execution_path or self._callback_execution_data:
                if execution_path:
                    update_data['execution_path'] = execution_path
                    update_data['execution_timing'] = execution_timing
                    update_data['execution_status'] = execution_status
                    if execution_errors:
                        update_data['execution_errors'] = execution_errors
                
                # Include edge conditions, agent iterations, and other runtime metadata if available
                if self._callback_execution_data:
                    for key in ['edge_conditions', 'agent_iterations', 'retry_info', 'state_transitions', 'nested_workflows']:
                        if key in self._callback_execution_data:
                            update_data[key] = self._callback_execution_data[key]
                            enriched_metadata[key] = self._callback_execution_data[key]
                
                # Validate execution data before sending
                import logging
                logger = logging.getLogger(__name__)
                if execution_path:
                    logger.debug(f"Sending execution data for trace {self.id}: {len(execution_path)} steps")
                else:
                    logger.debug(f"Trace {self.id} has no execution path but has callback data")
            
            if spans_data:
                update_data["spans"] = spans_data
            
            # Use buffer if available, otherwise send directly
            try:
                if self.buffer:
                    await self.buffer.add(EventType.TRACE_UPDATE, update_data)
                else:
                    response = await self.client.put(
                        f"{self.api_url}/v1/traces/{self.id}",
                        json=update_data
                    )
                    response.raise_for_status()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send trace update for {self.id}: {e}", exc_info=True)
                # Re-raise to let caller handle
                raise
    
    def span(
        self,
        name: str,
        type: str = "tool",
        parent: Optional[str] = None,
        stream: bool = False
    ) -> Any:
        """
        Create a span within this trace.
        
        Args:
            name: Span name
            type: Span type (llm, tool, agent, chain, workflow)
            parent: Optional parent span ID (can be span ID string or SpanContext object)
            stream: Whether to enable streaming (returns StreamingSpan)
            
        Returns:
            SpanContext manager (or StreamingSpan if stream=True)
        """
        if not self.id:
            raise RuntimeError("Trace not created yet. Use 'async with trace:' first.")
        
        # Handle parent - can be span ID string or SpanContext object
        parent_id = None
        if parent:
            if isinstance(parent, str):
                parent_id = parent
            elif hasattr(parent, 'id'):
                parent_id = parent.id
        
        span_ctx = SpanContext(
            client=self.client,
            api_url=self.api_url,
            trace_id=self.id,
            name=name,
            span_type=type,
            parent_id=parent_id,
            buffer=self.buffer
        )
        # Track span for later collection (even if created via separate API call)
        self._spans.append(span_ctx)
        
        # Return streaming span if requested
        if stream:
            from .streaming import StreamingSpan
            return StreamingSpan(span_ctx, stream=True)
        
        return span_ctx
    
    def set_prompt(self, prompt: Any) -> None:
        """
        Associate a prompt with this trace.
        
        Args:
            prompt: Prompt object from PromptManager
        """
        self._prompt = prompt
    
    def set_trace_context(self, context: Any) -> None:
        """
        Set W3C trace context for distributed tracing.
        
        Args:
            context: TraceContext object
        """
        self._trace_context = context
    
    def get_trace_context(self) -> Optional[Any]:
        """Get W3C trace context."""
        return self._trace_context
    
    def get_trace_headers(self) -> Dict[str, str]:
        """
        Get W3C trace context headers for HTTP propagation.
        
        Returns:
            Dictionary of headers to add to HTTP requests
        """
        if self._trace_context:
            return self._trace_context.to_headers()
        return {}
    
    def add_evaluation_hook(self, hook: Any) -> None:
        """
        Add an evaluation hook to run on trace completion.
        
        Args:
            hook: EvaluationHook instance
        """
        self._evaluation_hooks.append(hook)
    
    async def run_evaluations(
        self,
        expected: Any,
        actual: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run all evaluation hooks.
        
        Args:
            expected: Expected value
            actual: Actual value
            context: Optional context
            
        Returns:
            List of evaluation results
        """
        results = []
        for hook in self._evaluation_hooks:
            try:
                result = await hook.run(expected, actual, context)
                results.append({
                    "name": hook.name,
                    "score": result.score,
                    "score_type": result.score_type.value,
                    "metadata": result.metadata,
                    "explanation": result.explanation
                })
            except Exception as e:
                # Don't fail trace on evaluation errors
                print(f"⚠️  Evaluation hook {hook.name} failed: {e}")
        
        self._evaluation_results = results
        return results
    
    def get_evaluation_results(self) -> List[Dict[str, Any]]:
        """Get evaluation results."""
        return self._evaluation_results
    
    async def complete(self, status: str = "success", error: Optional[Exception] = None) -> None:
        """
        Manually complete the trace.
        
        Args:
            status: Trace status (success, failure, error)
            error: Optional error exception
        """
        if not self.id:
            return
        
        data = {
            "id": self.id,
            "trace_id": self.id,
            "status": status
        }
        if error:
            data.update({
                "error_message": str(error),
                "error_type": type(error).__name__
            })
        
        # Use buffer if available
        if self.buffer:
            await self.buffer.add(EventType.TRACE_UPDATE, data)
        else:
            await self.client.put(
                f"{self.api_url}/v1/traces/{self.id}",
                json=data
            )

