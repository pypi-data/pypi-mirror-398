"""
OpenTelemetry integration for Aigie SDK.

This module provides OpenTelemetry exporter and span processor integration,
allowing Aigie to work with standard observability tools like Datadog, New Relic, Jaeger, etc.
"""

from typing import Optional, Dict, Any, List
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semantic_conventions.trace import SpanAttributes
import time


class AigieSpanExporter(SpanExporter):
    """
    OpenTelemetry span exporter that sends spans to Aigie backend.
    
    Usage:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from aigie.opentelemetry import AigieSpanExporter
        
        provider = TracerProvider()
        exporter = AigieSpanExporter(aigie_client)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    """
    
    def __init__(self, aigie_client):
        """
        Initialize Aigie span exporter.
        
        Args:
            aigie_client: Aigie client instance
        """
        self.aigie = aigie_client
        self._trace_map: Dict[str, str] = {}  # Map OTel trace_id to Aigie trace_id
    
    def export(self, spans) -> SpanExportResult:
        """
        Export spans to Aigie backend.
        
        Args:
            spans: List of OpenTelemetry spans
            
        Returns:
            SpanExportResult indicating success or failure
        """
        try:
            # Group spans by trace
            traces: Dict[str, List[Any]] = {}
            
            for span in spans:
                trace_id = format(span.context.trace_id, '032x')
                
                if trace_id not in traces:
                    traces[trace_id] = []
                traces[trace_id].append(span)
            
            # Create/update traces and spans
            for trace_id, span_list in traces.items():
                # Get or create Aigie trace ID
                aigie_trace_id = self._trace_map.get(trace_id)
                
                if not aigie_trace_id:
                    # Create new trace
                    # Use the first span's name as trace name
                    trace_name = span_list[0].name if span_list else "otel_trace"
                    
                    # Create trace (this would need async handling in real implementation)
                    # For now, we'll use the buffer if available
                    if self.aigie._buffer:
                        import asyncio
                        from .buffer import EventType
                        
                        # Create trace
                        trace_payload = {
                            "name": trace_name,
                            "status": "running",
                            "metadata": {
                                "otel_trace_id": trace_id,
                                "source": "opentelemetry"
                            }
                        }
                        
                        # This is a simplified version - in production, you'd want
                        # to handle this properly with async/await
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # If loop is running, schedule the coroutine
                                asyncio.create_task(
                                    self.aigie._buffer.add(EventType.TRACE_CREATE, trace_payload)
                                )
                            else:
                                loop.run_until_complete(
                                    self.aigie._buffer.add(EventType.TRACE_CREATE, trace_payload)
                                )
                        except RuntimeError:
                            # No event loop, create one
                            asyncio.run(
                                self.aigie._buffer.add(EventType.TRACE_CREATE, trace_payload)
                            )
                
                # Export spans
                for span in span_list:
                    self._export_span(span, aigie_trace_id or trace_id)
            
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"⚠️  Failed to export spans to Aigie: {e}")
            return SpanExportResult.FAILURE
    
    def _export_span(self, span: Any, trace_id: str) -> None:
        """Export a single span to Aigie."""
        try:
            # Convert OTel span to Aigie span format
            span_payload = {
                "trace_id": trace_id,
                "name": span.name,
                "type": self._get_span_type(span),
                "input": self._extract_input(span),
                "output": self._extract_output(span),
                "metadata": self._extract_metadata(span),
                "status": "success" if span.status.status_code == StatusCode.OK else "failure"
            }
            
            # Add error information if present
            if span.status.status_code == StatusCode.ERROR and span.status.description:
                span_payload["error_message"] = span.status.description
            
            # Add timing information
            if span.start_time and span.end_time:
                duration_ns = (span.end_time - span.start_time)
                span_payload["duration_ns"] = int(duration_ns)
            
            # Use buffer if available
            if self.aigie._buffer:
                import asyncio
                from .buffer import EventType
                
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            self.aigie._buffer.add(EventType.SPAN_CREATE, span_payload)
                        )
                    else:
                        loop.run_until_complete(
                            self.aigie._buffer.add(EventType.SPAN_CREATE, span_payload)
                        )
                except RuntimeError:
                    asyncio.run(
                        self.aigie._buffer.add(EventType.SPAN_CREATE, span_payload)
                    )
        except Exception as e:
            print(f"⚠️  Failed to export span {span.name}: {e}")
    
    def _get_span_type(self, span: Any) -> str:
        """Determine span type from OTel span attributes."""
        # Check for common OTel attributes
        attrs = span.attributes or {}
        
        # LLM spans
        if "llm" in span.name.lower() or "openai" in span.name.lower():
            return "llm"
        
        # Tool spans
        if "tool" in span.name.lower() or "function" in span.name.lower():
            return "tool"
        
        # Agent spans
        if "agent" in span.name.lower():
            return "agent"
        
        # Chain spans
        if "chain" in span.name.lower():
            return "chain"
        
        # Default
        return "tool"
    
    def _extract_input(self, span: Any) -> Dict[str, Any]:
        """Extract input data from OTel span."""
        attrs = span.attributes or {}
        input_data = {}
        
        # Common OTel attributes
        if "input" in attrs:
            input_data["input"] = attrs["input"]
        if "prompt" in attrs:
            input_data["prompt"] = attrs["prompt"]
        if "query" in attrs:
            input_data["query"] = attrs["query"]
        
        return input_data
    
    def _extract_output(self, span: Any) -> Dict[str, Any]:
        """Extract output data from OTel span."""
        attrs = span.attributes or {}
        output_data = {}
        
        # Common OTel attributes
        if "output" in attrs:
            output_data["output"] = attrs["output"]
        if "response" in attrs:
            output_data["response"] = attrs["response"]
        if "result" in attrs:
            output_data["result"] = attrs["result"]
        
        return output_data
    
    def _extract_metadata(self, span: Any) -> Dict[str, Any]:
        """Extract metadata from OTel span."""
        attrs = span.attributes or {}
        metadata = {}
        
        # Copy relevant attributes as metadata
        for key, value in attrs.items():
            if key not in ["input", "output", "prompt", "query", "response", "result"]:
                metadata[key] = value
        
        return metadata
    
    def shutdown(self) -> None:
        """Shutdown the exporter."""
        # Flush any remaining events
        if self.aigie._buffer:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.aigie.flush())
                else:
                    loop.run_until_complete(self.aigie.flush())
            except RuntimeError:
                asyncio.run(self.aigie.flush())


def setup_opentelemetry(aigie_client, service_name: Optional[str] = None) -> None:
    """
    Setup OpenTelemetry with Aigie exporter.
    
    Usage:
        from aigie import Aigie
        from aigie.opentelemetry import setup_opentelemetry
        
        aigie = Aigie()
        await aigie.initialize()
        
        setup_opentelemetry(aigie, service_name="my-service")
        
        # Now all OTel spans will be exported to Aigie
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("my_operation"):
            # Your code here
            pass
    
    Args:
        aigie_client: Aigie client instance
        service_name: Optional service name for OTel
    """
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    
    # Create resource with service name
    resource = Resource.create({"service.name": service_name or "aigie-service"})
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Create Aigie exporter
    exporter = AigieSpanExporter(aigie_client)
    
    # Add batch span processor
    provider.add_span_processor(BatchSpanProcessor(exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)








