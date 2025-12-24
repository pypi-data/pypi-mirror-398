"""
Aigie Client - Main SDK class for integrating Aigie monitoring.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Callable, Awaitable, TYPE_CHECKING
import httpx
from .trace import TraceContext
from .config import Config
from .buffer import EventBuffer, EventType, BufferedEvent
from .sampling import should_send_event

if TYPE_CHECKING:
    from .interceptor import InterceptorChain, PreCallHook, PostCallHook, InterceptionContext
    from .rules import LocalRulesEngine, Rule
    from .realtime import BackendConnector, AutoFixApplicator
    from .drift import DriftMonitor
    from .judge import LLMJudge, JudgeConfig, ContextAggregator
    from .runtime import SpanInterceptor, SpanInterceptorConfig, RemediationLoop, RemediationConfig
    from .licensing import LicenseValidator, LicenseInfo

logger = logging.getLogger(__name__)

# Global singleton instance
_global_aigie: Optional['Aigie'] = None
_instrumentation_enabled: bool = False


class Aigie:
    """
    Main Aigie client for monitoring AI agent workflows.

    Usage:
        aigie = Aigie()
        await aigie.initialize()

        async with aigie.trace("My Workflow") as trace:
            # Your code here
            pass

    With data masking:
        def mask_pii(data: dict) -> dict:
            # Redact emails, phone numbers, etc.
            return redacted_data

        aigie = Aigie(mask=mask_pii)

    With debug mode:
        aigie = Aigie(debug=True)  # or AIGIE_DEBUG=true
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Config] = None,
        # NEW: Direct constructor parameters for common options
        mask: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        debug: bool = False,
    ):
        """
        Initialize Aigie client.

        Args:
            api_url: Aigie API URL (defaults to AIGIE_API_URL env var or config)
            api_key: API key for authentication (defaults to AIGIE_API_KEY env var or config)
            config: Optional Config object (if provided, overrides api_url/api_key)
            mask: Optional function to mask sensitive data (PII protection)
            debug: Enable debug mode for detailed logging
        """
        # Use config if provided, otherwise create from params/env
        if config:
            self.config = config
            self.api_url = config.api_url
            self.api_key = config.api_key
        else:
            self.config = Config(
                api_url=api_url or os.getenv("AIGIE_API_URL", "http://localhost:8000/api"),
                api_key=api_key or os.getenv("AIGIE_API_KEY", "test-api-key"),
                mask=mask,
                debug=debug or os.getenv("AIGIE_DEBUG", "").lower() in ("true", "1", "yes"),
            )
            self.api_url = self.config.api_url
            self.api_key = self.config.api_key

        # Store mask function for use in traces/spans
        self._mask_fn = mask or self.config.mask
        self._debug = debug or self.config.debug

        # Set global mask function for decorators
        if self._mask_fn:
            from . import decorators_v3
            decorators_v3.set_global_mask_fn(self._mask_fn)

        # Set debug mode
        if self._debug:
            from . import decorators_v3
            decorators_v3.set_debug_mode(True)
            logger.setLevel(logging.DEBUG)
            logger.debug("Aigie client initialized in debug mode")

        self.client: Optional[httpx.AsyncClient] = None
        self._initialized: bool = False
        self._buffer: Optional[EventBuffer] = None

        # Real-time interception components
        self._interceptor_chain: Optional["InterceptorChain"] = None
        self._rules_engine: Optional["LocalRulesEngine"] = None
        self._backend_connector: Optional["BackendConnector"] = None
        self._drift_monitor: Optional["DriftMonitor"] = None
        self._auto_fix_applicator: Optional["AutoFixApplicator"] = None

        # LLM Judge and Runtime components
        self._llm_judge: Optional["LLMJudge"] = None
        self._context_aggregator: Optional["ContextAggregator"] = None
        self._span_interceptor: Optional["SpanInterceptor"] = None
        self._remediation_loop: Optional["RemediationLoop"] = None

        # License validation (for self-hosted installations)
        self._license_validator: Optional["LicenseValidator"] = None
        self._license_info: Optional["LicenseInfo"] = None
    
    async def initialize(self) -> None:
        """Initialize the HTTP client, event buffer, and interception components.

        This method also:
        - Sets this instance as the global Aigie instance (for get_aigie())
        - Enables auto-instrumentation for LangChain, LangGraph, and LLM clients

        This makes the SDK work like competitors (AgentOps, Helicone) where
        just creating and initializing the client automatically instruments everything.
        """
        if not self._initialized:
            # Set this instance as the global instance so get_aigie() returns it
            # This enables auto-instrumentation to find the client
            global _global_aigie
            if _global_aigie is None:
                _global_aigie = self

            self.client = httpx.AsyncClient(
                timeout=self.config.timeout,
                limits=httpx.Limits(max_connections=self.config.max_connections),
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
            )

            # Initialize event buffer if enabled
            if self.config.enable_buffering:
                self._buffer = EventBuffer(
                    max_size=self.config.batch_size,
                    flush_interval=self.config.flush_interval,
                    max_retries=self.config.max_retries,
                    retry_delay=self.config.retry_delay
                )
                self._buffer.set_flusher(self._flush_events)
                await self._buffer.start_background_flusher()

            # Validate configuration for self-hosted deployments
            self.config.validate_and_warn()

            # Initialize license validation if aigie token is provided
            if self.config.aigie_token and not self.config.skip_license_validation:
                await self._initialize_license()

            # Initialize real-time interception components if enabled
            if self.config.enable_interception:
                await self._initialize_interception()

            self._initialized = True

            # Enable auto-instrumentation unless explicitly disabled
            # This patches LangChain, LangGraph, and LLM clients to automatically create traces
            # Check both enable_auto_instrument (default True) and disable_auto_instrument (default False)
            should_auto_instrument = getattr(self.config, 'enable_auto_instrument', True)
            explicitly_disabled = getattr(self.config, 'disable_auto_instrument', False)

            if should_auto_instrument and not explicitly_disabled:
                _enable_auto_instrumentation()
                logger.info("Auto-instrumentation enabled - LLM calls will be automatically traced")

    async def _initialize_interception(self) -> None:
        """Initialize real-time interception components."""
        from .interceptor import InterceptorChain
        from .rules import LocalRulesEngine
        from .drift import DriftMonitor, DriftConfig
        from .realtime import AutoFixApplicator, FixConfig

        logger.info("Initializing real-time interception components")

        # Initialize local rules engine with config-based rules
        self._rules_engine = LocalRulesEngine(config=self.config)
        logger.debug(f"Rules engine initialized with {len(self._rules_engine.list_rules())} rules")

        # Initialize drift monitor
        drift_config = DriftConfig(
            topic_drift_threshold=self.config.drift_threshold,
            behavior_drift_threshold=self.config.drift_threshold,
            enable_topic_detection=self.config.enable_drift_detection,
            enable_behavior_detection=self.config.enable_drift_detection,
            enable_quality_detection=self.config.enable_drift_detection,
            enable_coherence_detection=self.config.enable_drift_detection,
        )
        self._drift_monitor = DriftMonitor(config=drift_config)

        # Initialize auto-fix applicator
        fix_config = FixConfig(
            max_retries=self.config.auto_fix_max_retries,
            fallback_models=getattr(self.config, 'fallback_models', []),
        )
        self._auto_fix_applicator = AutoFixApplicator(config=fix_config)

        # Initialize interceptor chain with rules engine
        self._interceptor_chain = InterceptorChain(
            rules_engine=self._rules_engine,
            local_timeout_ms=self.config.local_decision_timeout_ms,
            backend_timeout_ms=self.config.backend_consultation_timeout_ms,
        )

        # Initialize backend connector for real-time consultation if enabled
        if self.config.enable_backend_realtime:
            from .realtime import BackendConnector

            self._backend_connector = BackendConnector(
                api_url=self.api_url,
                api_key=self.api_key,
                request_timeout=self.config.backend_consultation_timeout_ms / 1000,
            )

            # Set backend connector on interceptor chain
            self._interceptor_chain.set_backend_connector(self._backend_connector)

            # Connect to backend WebSocket
            try:
                connected = await self._backend_connector.connect()
                if connected:
                    logger.info("Connected to Aigie backend for real-time interception")
                else:
                    logger.warning("Failed to connect to backend, operating in local-only mode")
            except Exception as e:
                logger.warning(f"Backend connection failed: {e}, operating in local-only mode")

        # Register drift monitor alerts with interceptor chain
        async def on_drift_alert(alert):
            logger.warning(f"Drift alert: {alert.drift_type.value} - {alert.reason}")
            # Could trigger auto-fix or notification here

        self._drift_monitor.on_alert(on_drift_alert)

        # Initialize LLM Judge and Runtime components
        await self._initialize_judge_and_runtime()

        logger.info("Real-time interception initialized successfully")

    async def _initialize_license(self) -> None:
        """Initialize license validation for self-hosted installations."""
        from .licensing import (
            LicenseValidator,
            LicenseError,
            LicenseExpiredError,
            LicenseRevokedError,
        )

        logger.info("Initializing license validation")

        self._license_validator = LicenseValidator(
            license_key=self.config.aigie_token,
            license_server_url=self.config.license_server_url,
            installation_id=self.config.installation_id,
            enable_telemetry=self.config.enable_usage_telemetry,
        )

        try:
            # Validate license with the licensing server
            self._license_info = await self._license_validator.validate()

            if not self._license_info.valid:
                raise LicenseError(self._license_info.error or "License validation failed")

            logger.info(
                f"License validated: tier={self._license_info.tier}, "
                f"features={list(self._license_info.features.keys())}"
            )

            # Start background tasks for heartbeat and usage reporting
            await self._license_validator.start_background_tasks()

        except LicenseExpiredError as e:
            logger.error(f"License expired: {e}")
            raise
        except LicenseRevokedError as e:
            logger.error(f"License revoked: {e}")
            raise
        except LicenseError as e:
            logger.error(f"License validation failed: {e}")
            raise
        except Exception as e:
            # For network errors, log warning but allow operation if license was previously valid
            logger.warning(f"License validation error (non-fatal): {e}")

    async def _initialize_judge_and_runtime(self) -> None:
        """Initialize LLM Judge and Runtime components for step-level retry."""
        from .judge import LLMJudge, JudgeConfig, ContextAggregator, JudgeCriteria
        from .runtime import (
            SpanInterceptor, SpanInterceptorConfig,
            RemediationLoop, RemediationConfig, OperationalMode
        )

        logger.info("Initializing LLM Judge and Runtime components")

        # Initialize context aggregator for full history tracking
        self._context_aggregator = ContextAggregator(
            max_history_size=100,
            include_tool_outputs=True,
            track_metrics=True,
        )

        # Initialize LLM Judge
        # Note: Judge will use wrapped OpenAI client if available
        judge_config = JudgeConfig(
            judge_model=getattr(self.config, 'judge_model', 'gpt-4o-mini'),
            evaluation_timeout_ms=500.0,
            fallback_to_heuristics=True,
            confidence_threshold=0.7,
            criteria=JudgeCriteria.balanced(),
        )
        self._llm_judge = LLMJudge(
            config=judge_config,
            backend_client=self,
        )

        # Initialize span interceptor for step-level retry
        span_config = SpanInterceptorConfig(
            max_retries=getattr(self.config, 'auto_fix_max_retries', 3),
            evaluate_all_spans=True,
            stop_on_critical=True,
            evaluation_timeout_ms=500.0,
        )
        self._span_interceptor = SpanInterceptor(
            config=span_config,
            judge=self._llm_judge,
            context_aggregator=self._context_aggregator,
        )

        # Initialize remediation loop (starts in RECOMMENDATION mode)
        remediation_config = RemediationConfig(
            mode=OperationalMode.RECOMMENDATION,
            learning_threshold=100,
            min_workflow_confidence=0.8,
            auto_fix_enabled=False,  # Disabled until autonomous mode enabled
            report_to_backend=True,
        )
        self._remediation_loop = RemediationLoop(
            config=remediation_config,
            judge=self._llm_judge,
            context_aggregator=self._context_aggregator,
            span_interceptor=self._span_interceptor,
            backend_client=self,
        )

        logger.info(
            f"Runtime components initialized - Mode: {remediation_config.mode.value}, "
            f"Auto-fix: {'enabled' if remediation_config.auto_fix_enabled else 'disabled'}"
        )
    
    def trace(
        self,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        environment: Optional[str] = None,
        release: Optional[str] = None,
        version: Optional[str] = None,
        release_version: Optional[str] = None,  # Backward compatibility
        input: Optional[Any] = None,
        output: Optional[Any] = None
    ) -> Union[TraceContext, Any]:
        """
        Create a new trace context manager or decorator.
        
        Usage as context manager:
            async with aigie.trace("My Workflow") as trace:
                # Your code here
                pass
        
        Usage as decorator (with parentheses):
            @aigie.trace(name="my_function", metadata={"key": "value"})
            async def my_function():
                pass
        
        Usage as decorator (without parentheses):
            @aigie.trace
            async def my_function():
                pass
        
        Args:
            name: Trace name (required for context manager, optional for decorator)
            metadata: Optional metadata dictionary
            tags: Optional list of tags
            user_id: Optional user identifier for session tracking
            session_id: Optional session identifier for multi-turn conversations
            environment: Optional environment name (e.g., "production", "staging", "development")
            release_version: Optional application version/release identifier
            
        Returns:
            TraceContext manager or decorator
        """
        if not self._initialized:
            raise RuntimeError("Aigie not initialized. Call await aigie.initialize() first.")
        
        from .decorators import TraceDecorator
        
        # Merge session/user tracking into metadata
        enriched_metadata = dict(metadata or {})
        if user_id:
            enriched_metadata["user_id"] = user_id
        if session_id:
            enriched_metadata["session_id"] = session_id
        if environment:
            enriched_metadata["environment"] = environment
        if release:
            enriched_metadata["release"] = release
        if release_version:  # Backward compatibility
            enriched_metadata["release"] = release_version
            enriched_metadata["release_version"] = release_version
        if version:
            enriched_metadata["version"] = version
        if input is not None:
            enriched_metadata["input"] = input
        if output is not None:
            enriched_metadata["output"] = output
        
        # If name is provided and it's a string, use as context manager
        if name is not None and isinstance(name, str):
            return TraceContext(
                client=self.client,
                api_url=self.api_url,
                buffer=self._buffer,
                name=name,
                metadata=enriched_metadata,
                tags=tags or [],
                sample_rate=self.config.sampling_rate
            )
        
        # Otherwise, return a decorator
        return TraceDecorator(
            aigie_client=self,
            name=name if isinstance(name, str) else None,
            metadata=enriched_metadata,
            tags=tags
        )
    
    @property
    def callback(self):
        """
        Get LangChain/LangGraph callback handler.
        
        Usage:
            result = await workflow.ainvoke(
                input,
                config={"callbacks": [aigie.callback]}
            )
        """
        from .callback import AigieCallbackHandler
        return AigieCallbackHandler(aigie=self)
    
    @property
    def prompts(self):
        """
        Get prompt manager.
        
        Usage:
            prompt = await aigie.prompts.create(
                name="customer_support",
                template="You are a helpful assistant. Customer: {customer_name}"
            )
        """
        from .prompts import PromptManager
        if not hasattr(self, '_prompt_manager'):
            self._prompt_manager = PromptManager(self)
        return self._prompt_manager

    @property
    def feedback(self):
        """
        Get feedback collector for human feedback and eval ground truth.

        Usage:
            # Submit human override of LLM judgment
            await aigie.feedback.submit_eval_override(
                judge_run_id="judge-123",
                human_score=0.9,
                human_verdict="pass",
                human_reasoning="The response was actually helpful"
            )

            # Submit trace feedback (thumbs up/down)
            await aigie.feedback.submit_trace_feedback(
                trace_id="trace-abc",
                rating="positive",
                comment="Great response!"
            )
        """
        from .feedback import FeedbackCollector
        if not hasattr(self, '_feedback_collector'):
            self._feedback_collector = FeedbackCollector(self._buffer)
        return self._feedback_collector

    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[Any]:
        """
        Extract W3C trace context from HTTP headers.
        
        Usage:
            context = aigie.extract_trace_context(request.headers)
            if context:
                async with aigie.trace("workflow") as trace:
                    trace.set_trace_context(context)
        
        Args:
            headers: HTTP headers dictionary
            
        Returns:
            TraceContext if found, None otherwise
        """
        from .context import extract_trace_context
        return extract_trace_context(headers)
    
    def create_trace_context(self, parent_context: Optional[Any] = None) -> Any:
        """
        Create a new W3C trace context.
        
        Usage:
            context = aigie.create_trace_context()
            headers = context.to_headers()
            # Add headers to HTTP request
        
        Args:
            parent_context: Optional parent context (creates child context)
            
        Returns:
            TraceContext object
        """
        from .context import TraceContext
        
        if parent_context:
            return parent_context.create_child()
        return TraceContext()
    
    async def remediate(self, trace_id: str, error: Exception) -> Dict[str, Any]:
        """
        Trigger autonomous remediation for an error.
        
        Args:
            trace_id: Trace ID with the error
            error: The exception that occurred
            
        Returns:
            Remediation result
        """
        if not self._initialized:
            await self.initialize()
        
        response = await self.client.post(
            f"{self.api_url}/v1/remediation/autonomous/fix",
            json={
                "trace_id": trace_id,
                "error": {
                    "type": type(error).__name__,
                    "message": str(error)
                }
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def detect_precursors(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect error precursors in the given context.
        
        Args:
            context: Context data to analyze
            
        Returns:
            List of detected precursors
        """
        if not self._initialized:
            await self.initialize()
        
        response = await self.client.post(
            f"{self.api_url}/v1/prevention/detect-precursors",
            json={"context": context}
        )
        response.raise_for_status()
        return response.json().get("precursors", [])
    
    async def apply_preventive_fix(self, trace_id: str, precursors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply preventive fixes based on detected precursors.
        
        Args:
            trace_id: Trace ID
            precursors: List of detected precursors
            
        Returns:
            Fix application result
        """
        if not self._initialized:
            await self.initialize()
        
        response = await self.client.post(
            f"{self.api_url}/v1/prevention/apply-preventive-fix",
            json={
                "trace_id": trace_id,
                "precursors": precursors
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _send_batch(self, events: List[Dict[str, Any]]) -> None:
        """
        Send batch of events to batch ingestion endpoint.
        
        Supports compression with Zstandard if available.
        
        Args:
            events: List of event dictionaries already in correct format from _flush_events
                   Format: {"type": "trace-create", "id": "...", "timestamp": "...", "body": {...}}
        """
        from datetime import datetime
        
        # Events are already in the correct format from _flush_events
        # Just ensure timestamps are strings and validate structure
        batch_events = []
        for event in events:
            # Validate required fields
            if "type" not in event or "id" not in event or "body" not in event:
                logger.warning(f"Skipping invalid event: missing required fields: {event.keys()}")
                continue
            
            # Ensure timestamp is a string
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            elif isinstance(event["timestamp"], datetime):
                event["timestamp"] = event["timestamp"].isoformat()
            
            # Ensure body is a dict
            if not isinstance(event.get("body"), dict):
                logger.warning(f"Skipping event with invalid body type: {type(event.get('body'))}")
                continue
            
            batch_events.append(event)
        
        if not batch_events:
            logger.warning("No valid events to send in batch")
            return
        
        # Prepare request payload
        request_payload = {"batch": batch_events}
        
        # Validate payload can be serialized to JSON
        import json
        try:
            json.dumps(request_payload, default=str)  # Test serialization
        except Exception as e:
            logger.error(f"Failed to serialize batch payload to JSON: {e}")
            return
        
        # Debug: Log first event structure (only in debug mode)
        if logger.isEnabledFor(logging.DEBUG) and batch_events:
            logger.debug(f"Sample event structure: {batch_events[0]}")
        
        # For now, disable compression to avoid parsing issues
        # TODO: Re-enable compression once backend properly handles zstd decompression
        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}
        
        # Check if event loop is available before attempting to send
        try:
            loop = asyncio.get_running_loop()
            if loop.is_closed():
                logger.debug(f"Event loop is closed, skipping batch send ({len(batch_events)} events)")
                return
        except RuntimeError:
            # No event loop running - this is expected during shutdown
            logger.debug(f"No event loop running, skipping batch send ({len(batch_events)} events)")
            return
        
        try:
            # Always send as JSON for now (compression can be re-enabled later)
            response = await self.client.post(
                f"{self.api_url}/v1/ingestion",
                json=request_payload,
                headers=headers,
                timeout=30.0
            )
        except Exception as e:
            # Check if it's an event loop issue - if so, we can't recover
            error_str = str(e).lower()
            if "event loop is closed" in error_str or "event loop" in error_str or "runtimeerror" in error_str:
                # This is expected during application shutdown - log as debug instead of error
                logger.debug(f"Event loop issue, cannot send batch ({len(batch_events)} events): {e}")
                return  # Can't recover from event loop closure
            logger.error(f"Failed to send batch: {e}")
            return
        
        # Handle response - log validation/server errors with details for debugging
        if response.status_code in (400, 422):  # 422 is FastAPI validation error
            error_text = response.text[:1000] if response.text else "No error message"
            status_name = "validation" if response.status_code == 422 else "client"
            logger.warning(f"Batch ingestion {status_name} error ({response.status_code}): {error_text}")
            # Try to parse error details
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    detail = error_json.get("detail", error_json)
                    logger.warning(f"Batch ingestion error details: {detail}")
                else:
                    logger.warning(f"Batch ingestion error response: {error_json}")
            except:
                pass
            return  # Don't process response, just return
        elif response.status_code == 500:
            error_text = response.text[:1000] if response.text else "No error message"
            logger.error(f"Batch ingestion server error (500): {error_text}")
            return  # Don't process response, just return
        
        response.raise_for_status()
        
        # Check for errors in 207 Multi-Status response
        try:
            result = response.json()
            if result.get("errors"):
                # Log errors but don't fail (some events may have succeeded)
                logger.debug(
                    f"Batch ingestion had {len(result.get('errors', []))} errors out of {len(result.get('successes', [])) + len(result.get('errors', []))} total events"
                )
                # Log first few errors for debugging
                for error in result.get("errors", [])[:3]:
                    logger.debug(f"Batch ingestion error: {error}")
            else:
                logger.debug(f"Batch ingestion successful: {len(result.get('successes', []))} events processed")
        except Exception:
            # If response parsing fails, just continue
            logger.debug("Batch ingestion response parsing failed (non-critical)")
    
    async def _flush_events(self, events: List[BufferedEvent]) -> None:
        """
        Flush buffered events to the API.
        
        Tries batch ingestion endpoint first, falls back to individual endpoints.
        """
        if not events:
            return
        
        # Try batch ingestion endpoint first
        try:
            # Convert to batch format matching backend schema
            batch_events = []
            for event in events:
                # Map event type from underscore to hyphen format
                event_type_map = {
                    "trace_create": "trace-create",
                    "trace_update": "trace-update",
                    "span_create": "span-create",
                    "span_update": "span-update",
                }
                event_type = event_type_map.get(event.event_type.value, event.event_type.value)
                
                # Get event ID
                event_id = event.payload.get("id") or event.payload.get("trace_id") or event.payload.get("span_id")
                if not event_id:
                    logger.warning(f"Skipping event without ID: {event.event_type.value}")
                    continue
                
                # Get timestamp from payload or use current time
                timestamp_str = event.payload.get("timestamp") or event.payload.get("start_time") or event.payload.get("created_at")
                if timestamp_str:
                    # If it's already a string, use it; if datetime, convert
                    if isinstance(timestamp_str, datetime):
                        timestamp = timestamp_str.isoformat()
                    else:
                        timestamp = timestamp_str
                else:
                    timestamp = datetime.utcnow().isoformat()
                
                # Prepare body - ensure it matches TraceBody/SpanBody schema
                body = event.payload.copy()
                
                # For trace events, map fields to TraceBody schema
                if "trace" in event_type:
                    # TraceBody expects: id, timestamp, name, input, output, metadata, tags, etc.
                    # Ensure id is in body
                    if "id" not in body:
                        body["id"] = event_id
                    # Convert start_time/created_at to timestamp (as ISO string, Pydantic will parse)
                    if "timestamp" not in body:
                        if "start_time" in body:
                            body["timestamp"] = body.pop("start_time")
                        elif "created_at" in body:
                            body["timestamp"] = body.pop("created_at")
                    # Remove fields not in TraceBody schema
                    body.pop("type", None)  # TraceBody doesn't have type
                    body.pop("status", None)  # TraceBody doesn't have status
                    # Ensure timestamp is a string if it's a datetime
                    if "timestamp" in body and isinstance(body["timestamp"], datetime):
                        body["timestamp"] = body["timestamp"].isoformat()
                
                # For span events, map fields to SpanBody schema
                elif "span" in event_type:
                    # SpanBody expects: id, trace_id, parent_id, name, type, start_time, end_time, input, output, etc.
                    # Ensure id is in body
                    if "id" not in body:
                        body["id"] = event_id
                    # Ensure trace_id is in body (not traceId)
                    if "trace_id" not in body and "traceId" in body:
                        body["trace_id"] = body.pop("traceId")
                    if "parent_id" not in body and "parentId" in body:
                        body["parent_id"] = body.pop("parentId")
                    # Ensure start_time is present (not created_at)
                    if "start_time" not in body and "created_at" in body:
                        body["start_time"] = body.pop("created_at")
                    # Convert endTime to end_time
                    if "end_time" not in body and "endTime" in body:
                        body["end_time"] = body.pop("endTime")
                    # Note: Keep status field for backend (it may extract it for span status)
                    # Remove timestamp as SpanBody uses start_time/end_time
                    body.pop("timestamp", None)  # SpanBody uses start_time/end_time, not timestamp
                    # Ensure start_time/end_time are strings if they're datetimes
                    if "start_time" in body and isinstance(body["start_time"], datetime):
                        body["start_time"] = body["start_time"].isoformat()
                    if "end_time" in body and isinstance(body["end_time"], datetime):
                        body["end_time"] = body["end_time"].isoformat()
                
                # Create event dict matching IngestionEvent schema
                # The type must be exactly "trace-create", "span-create", etc. (literal)
                event_dict = {
                    "type": event_type,  # Must match EventType enum exactly
                    "id": event_id,
                    "timestamp": timestamp,  # ISO string, Pydantic will parse to datetime
                    "body": body  # Must match TraceBody or SpanBody schema
                }
                batch_events.append(event_dict)
            
            if not batch_events:
                logger.warning("No valid events to send in batch")
                return
            
            logger.info(f"Attempting batch ingestion for {len(batch_events)} events via /v1/ingestion")
            await self._send_batch(batch_events)
            logger.info(f"Successfully sent {len(batch_events)} events via batch ingestion endpoint")
            return  # Success, exit early
        except Exception as e:
            # Fallback to individual endpoints
            logger.warning(
                f"Batch ingestion failed for {len(events)} events, falling back to individual endpoints: {type(e).__name__}: {str(e)}"
            )
        
        # Fallback: Group events by type and send individually
        events_by_type: Dict[EventType, List[BufferedEvent]] = {}
        for event in events:
            if event.event_type not in events_by_type:
                events_by_type[event.event_type] = []
            events_by_type[event.event_type].append(event)
        
        # Send batches
        for event_type, type_events in events_by_type.items():
            if event_type == EventType.TRACE_CREATE:
                # Batch create traces
                payloads = [e.payload for e in type_events]
                # For now, send individually (backend can be enhanced for batch)
                for event in type_events:
                    try:
                        response = await self.client.post(
                            f"{self.api_url}/v1/traces",
                            json=event.payload
                        )
                        response.raise_for_status()
                    except Exception as e:
                        # Re-raise to trigger retry
                        raise
            elif event_type == EventType.TRACE_UPDATE:
                # Batch update traces
                for event in type_events:
                    try:
                        # Get trace_id without modifying original payload
                        payload = event.payload.copy()
                        trace_id = payload.pop("id", payload.pop("trace_id", None))
                        if not trace_id:
                            raise ValueError("trace_id not found in payload")
                        response = await self.client.put(
                            f"{self.api_url}/v1/traces/{trace_id}",
                            json=payload
                        )
                        response.raise_for_status()
                    except Exception as e:
                        raise
            elif event_type == EventType.SPAN_CREATE:
                # Batch create spans
                for event in type_events:
                    try:
                        response = await self.client.post(
                            f"{self.api_url}/v1/spans",
                            json=event.payload,
                            headers={"X-API-Key": self.api_key},
                            timeout=5.0
                        )
                        response.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        # Suppress 400/500 errors - likely format or backend issues
                        if e.response.status_code in (400, 500):
                            logger.debug(f"Span creation failed (non-critical): {e.response.status_code} - {e.response.text[:200]}")
                            continue
                        raise
                    except Exception as e:
                        # Suppress connection errors
                        logger.debug(f"Span creation failed (non-critical): {e}")
                        continue
            elif event_type == EventType.SPAN_UPDATE:
                # Batch update spans
                for event in type_events:
                    try:
                        # Get span_id without modifying original payload
                        payload = event.payload.copy()
                        span_id = payload.pop("id", payload.pop("span_id", None))
                        if not span_id:
                            logger.debug("Span update skipped: span_id not found in payload")
                            continue
                        response = await self.client.put(
                            f"{self.api_url}/v1/spans/{span_id}",
                            json=payload,
                            headers={"X-API-Key": self.api_key},
                            timeout=5.0
                        )
                        response.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        # Suppress 400/500 errors - likely format or backend issues
                        if e.response.status_code in (400, 500):
                            logger.debug(f"Span update failed (non-critical): {e.response.status_code} - {e.response.text[:200]}")
                            continue
                        raise
                    except Exception as e:
                        # Suppress connection errors
                        logger.debug(f"Span update failed (non-critical): {e}")
                        continue
    
    async def flush(self) -> None:
        """Manually flush all buffered events."""
        if self._buffer:
            await self._buffer.flush()
    
    async def close(self) -> None:
        """Close the HTTP client and flush remaining events."""
        if self._buffer:
            await self._buffer.stop_background_flusher()

        # Close license validator (stops background tasks, reports final usage)
        if self._license_validator:
            try:
                # Report any pending usage before closing
                await self._license_validator.report_usage()
            except Exception as e:
                logger.debug(f"Failed to report final usage: {e}")
            finally:
                await self._license_validator.close()
                self._license_validator = None

        if self.client:
            await self.client.aclose()
            self._initialized = False
    
    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ==================== Real-time Interception API ====================

    @property
    def interceptor(self) -> Optional["InterceptorChain"]:
        """Get the interceptor chain for direct access."""
        return self._interceptor_chain

    @property
    def rules_engine(self) -> Optional["LocalRulesEngine"]:
        """Get the rules engine for direct access."""
        return self._rules_engine

    @property
    def drift_monitor(self) -> Optional["DriftMonitor"]:
        """Get the drift monitor for direct access."""
        return self._drift_monitor

    @property
    def auto_fix(self) -> Optional["AutoFixApplicator"]:
        """Get the auto-fix applicator for direct access."""
        return self._auto_fix_applicator

    def add_pre_call_hook(
        self,
        hook: Optional["PreCallHook"] = None,
        priority: int = 50,
        name: Optional[str] = None,
    ) -> Callable:
        """
        Add a pre-call hook for real-time interception.

        Can be used as a decorator or called directly:

            # As decorator
            @aigie.add_pre_call_hook(priority=10)
            async def my_hook(ctx: InterceptionContext) -> PreCallResult:
                if "unsafe" in str(ctx.messages):
                    return PreCallResult.block(reason="Unsafe content")
                return PreCallResult.allow()

            # Direct call
            aigie.add_pre_call_hook(my_hook_function, priority=10)

        Args:
            hook: Hook function (if using as direct call)
            priority: Hook priority (lower = runs first)
            name: Optional name for the hook

        Returns:
            Decorator if hook is None, otherwise None
        """
        if self._interceptor_chain is None:
            raise RuntimeError(
                "Interception not initialized. Enable with enable_interception=True in config."
            )

        def decorator(fn: "PreCallHook") -> "PreCallHook":
            self._interceptor_chain.add_pre_hook(fn, priority=priority, name=name)
            return fn

        if hook is not None:
            self._interceptor_chain.add_pre_hook(hook, priority=priority, name=name)
            return hook

        return decorator

    def add_post_call_hook(
        self,
        hook: Optional["PostCallHook"] = None,
        priority: int = 50,
        name: Optional[str] = None,
    ) -> Callable:
        """
        Add a post-call hook for real-time interception.

        Can be used as a decorator or called directly:

            # As decorator
            @aigie.add_post_call_hook(priority=10)
            async def my_hook(ctx: InterceptionContext) -> PostCallResult:
                if ctx.drift_score and ctx.drift_score > 0.8:
                    return PostCallResult.retry(reason="High drift detected")
                return PostCallResult.allow()

            # Direct call
            aigie.add_post_call_hook(my_hook_function, priority=10)

        Args:
            hook: Hook function (if using as direct call)
            priority: Hook priority (lower = runs first)
            name: Optional name for the hook

        Returns:
            Decorator if hook is None, otherwise None
        """
        if self._interceptor_chain is None:
            raise RuntimeError(
                "Interception not initialized. Enable with enable_interception=True in config."
            )

        def decorator(fn: "PostCallHook") -> "PostCallHook":
            self._interceptor_chain.add_post_hook(fn, priority=priority, name=name)
            return fn

        if hook is not None:
            self._interceptor_chain.add_post_hook(hook, priority=priority, name=name)
            return hook

        return decorator

    def add_rule(
        self,
        rule: "Rule",
        priority: Optional[int] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Add a custom rule to the local rules engine.

        Args:
            rule: Rule object implementing the Rule protocol
            priority: Override priority (default: use rule.priority)
            name: Override name (default: use rule.name)

        Example:
            from aigie.rules import CostLimitRule

            aigie.add_rule(CostLimitRule(max_cost=0.50, limit_type="request"))
        """
        if self._rules_engine is None:
            raise RuntimeError(
                "Interception not initialized. Enable with enable_interception=True in config."
            )

        self._rules_engine.add_rule(rule, priority=priority, name=name)

    async def intercept_pre_call(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        estimated_cost: float = 0.0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> "InterceptionContext":
        """
        Run pre-call interception on an LLM call.

        This is called automatically by wrap_openai and other wrappers.
        Can also be called directly for custom integrations.

        Args:
            provider: LLM provider name (e.g., "openai", "anthropic")
            model: Model name
            messages: Chat messages
            trace_id: Optional trace ID for correlation
            span_id: Optional span ID for correlation
            estimated_cost: Estimated cost for this call
            user_id: Optional user identifier
            session_id: Optional session identifier
            **kwargs: Additional request parameters

        Returns:
            InterceptionContext with decision

        Raises:
            InterceptionBlockedError: If the request is blocked
        """
        if self._interceptor_chain is None:
            # Interception not enabled, create pass-through context
            from .interceptor.protocols import InterceptionContext, InterceptionDecision

            ctx = InterceptionContext(
                provider=provider,
                model=model,
                messages=messages,
                trace_id=trace_id,
                span_id=span_id,
                estimated_cost=estimated_cost,
                user_id=user_id,
                session_id=session_id,
                request_kwargs=kwargs,
            )
            ctx.decision = InterceptionDecision.ALLOW
            return ctx

        from .interceptor.protocols import InterceptionContext

        # Create interception context
        ctx = InterceptionContext(
            provider=provider,
            model=model,
            messages=messages,
            trace_id=trace_id,
            span_id=span_id,
            estimated_cost=estimated_cost,
            user_id=user_id,
            session_id=session_id,
            request_kwargs=kwargs,
        )

        # Run pre-call hooks
        result = await self._interceptor_chain.pre_call(ctx)

        # Update context with decision
        ctx.decision = result.decision
        ctx.modified_messages = result.modified_messages
        ctx.modified_kwargs = result.modified_kwargs

        return ctx

    async def intercept_post_call(
        self,
        ctx: "InterceptionContext",
        response: Any,
        error: Optional[Exception] = None,
    ) -> "InterceptionContext":
        """
        Run post-call interception after an LLM call.

        This is called automatically by wrap_openai and other wrappers.
        Can also be called directly for custom integrations.

        Args:
            ctx: The interception context from pre-call
            response: The LLM response (or None if error)
            error: The exception if the call failed

        Returns:
            Updated InterceptionContext with post-call decision

        Raises:
            InterceptionRetryError: If the call should be retried
        """
        if self._interceptor_chain is None:
            # Interception not enabled, just update context
            ctx.response = response
            ctx.error = error
            return ctx

        # Update context with response/error
        ctx.response = response
        ctx.error = error
        if error:
            ctx.error_type = type(error).__name__

        # Extract response content if available
        if response and hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and choice.message:
                ctx.response_content = getattr(choice.message, 'content', None)

        # Run drift detection
        if self._drift_monitor:
            alerts = await self._drift_monitor.check_drift(ctx)
            if alerts:
                # Set drift score based on highest alert
                ctx.drift_score = max(a.score for a in alerts)

        # Run post-call hooks
        result = await self._interceptor_chain.post_call(ctx)

        # Update context with decision and fixes
        ctx.decision = result.decision
        ctx.fixes_applied = result.fixes_applied if hasattr(result, 'fixes_applied') else []

        # If retry requested and auto-fix is enabled, apply fixes via applicator
        if result.should_retry and self._auto_fix_applicator and result.fixes_applied:
            fix_result = await self._auto_fix_applicator.apply_fixes(ctx, result.fixes_applied)
            if fix_result.success:
                ctx.modified_response = fix_result.modified_response
                ctx.retry_kwargs = fix_result.retry_kwargs

        return ctx

    def get_interception_stats(self) -> Dict[str, Any]:
        """
        Get statistics from all interception components.

        Returns:
            Dict with stats from interceptor, rules engine, drift monitor, etc.
        """
        stats = {}

        if self._interceptor_chain:
            stats["interceptor"] = self._interceptor_chain.get_stats()

        if self._rules_engine:
            stats["rules_engine"] = self._rules_engine.get_stats()

        if self._drift_monitor:
            metrics = self._drift_monitor.get_metrics()
            stats["drift_monitor"] = {
                "total_checks": metrics.total_checks,
                "alerts_generated": metrics.alerts_generated,
                "alerts_by_type": metrics.alerts_by_type,
                "avg_drift_score": metrics.avg_drift_score,
            }

        if self._auto_fix_applicator:
            stats["auto_fix"] = self._auto_fix_applicator.get_stats()

        if self._backend_connector:
            stats["backend_connector"] = self._backend_connector.get_stats()

        # Add judge and runtime stats
        if self._llm_judge:
            stats["judge"] = self._llm_judge.get_stats()

        if self._context_aggregator:
            stats["context_aggregator"] = self._context_aggregator.get_stats()

        if self._span_interceptor:
            stats["span_interceptor"] = self._span_interceptor.get_stats()

        if self._remediation_loop:
            stats["remediation_loop"] = self._remediation_loop.get_stats()

        return stats

    # ========== Autonomous Mode Control ==========

    def enable_autonomous_mode(self) -> bool:
        """
        Enable autonomous mode for automatic fixes in runtime.

        Call this when user clicks the "autonomous" button.
        Aigie will now automatically fix detected issues instead
        of just showing what it would do.

        Returns:
            True if autonomous mode was enabled successfully,
            False if not enough learning has occurred.
        """
        if not self._remediation_loop:
            logger.warning("Remediation loop not initialized")
            return False

        enabled = self._remediation_loop.enable_autonomous_mode()
        if enabled:
            logger.info("🤖 Autonomous mode ENABLED - Aigie will now fix issues automatically")
        return enabled

    def disable_autonomous_mode(self) -> None:
        """
        Disable autonomous mode and return to recommendation mode.

        Aigie will continue detecting issues but will only show
        what it would do, not automatically fix.
        """
        if self._remediation_loop:
            self._remediation_loop.disable_autonomous_mode()
            logger.info("👁️ Autonomous mode DISABLED - Returning to recommendation mode")

    def is_autonomous_mode(self) -> bool:
        """Check if autonomous mode is currently enabled."""
        if self._remediation_loop:
            from .runtime import OperationalMode
            return self._remediation_loop.mode == OperationalMode.AUTONOMOUS
        return False

    def is_ready_for_autonomous(self) -> Dict[str, Any]:
        """
        Check if the system is ready for autonomous mode.

        Returns a dict with:
        - ready: bool - Whether autonomous mode can be enabled
        - traces_processed: int - Number of traces analyzed
        - traces_needed: int - Minimum traces needed
        - patterns_learned: int - Workflow patterns identified
        - avg_pattern_confidence: float - Average confidence in patterns
        """
        if self._remediation_loop:
            return self._remediation_loop.is_ready_for_autonomous()
        return {
            "ready": False,
            "traces_processed": 0,
            "traces_needed": 100,
            "patterns_learned": 0,
            "avg_pattern_confidence": 0.0,
        }

    def get_pending_recommendations(self) -> List[Any]:
        """
        Get pending recommendations (what Aigie would fix in autonomous mode).

        These show the customer what fixes would be applied if they
        enable autonomous mode, helping build trust.
        """
        if self._remediation_loop:
            return self._remediation_loop.get_pending_recommendations()
        return []

    def accept_recommendation(self, span_id: str) -> bool:
        """
        Mark a recommendation as accepted (user applied fix manually).

        This helps Aigie learn from manual fixes.
        """
        if self._remediation_loop:
            return self._remediation_loop.accept_recommendation(span_id)
        return False

    def get_workflow_patterns(self) -> List[Any]:
        """
        Get the workflow patterns Aigie has learned.

        Shows the customer what workflows Aigie understands.
        """
        if self._remediation_loop:
            return self._remediation_loop.get_workflow_patterns()
        return []

    def set_judge_llm_client(self, client: Any) -> None:
        """
        Set the LLM client for the judge.

        The judge uses this client to evaluate span outputs.
        Should be a wrapped OpenAI or Anthropic client.
        """
        if self._llm_judge:
            self._llm_judge.set_llm_client(client)
            logger.debug("Judge LLM client set")

    # ========== License Management ==========

    @property
    def license_info(self) -> Optional["LicenseInfo"]:
        """Get the current license information."""
        return self._license_info

    @property
    def license_tier(self) -> Optional[str]:
        """Get the current license tier (starter, pro, enterprise)."""
        return self._license_info.tier if self._license_info else None

    @property
    def license_features(self) -> Dict[str, bool]:
        """Get available features based on license."""
        return self._license_info.features if self._license_info else {}

    def has_feature(self, feature: str) -> bool:
        """
        Check if a feature is available in the current license.

        Args:
            feature: Feature name (e.g., 'realtime', 'drift_detection', 'auto_remediation')

        Returns:
            True if feature is available
        """
        if not self._license_info:
            return True  # No license configured, allow all features
        return self._license_info.features.get(feature, False)

    def is_within_limits(self, metric: str, value: int) -> bool:
        """
        Check if a usage metric is within license limits.

        Args:
            metric: Metric name ('traces', 'seats', 'projects')
            value: Current value to check

        Returns:
            True if within limits
        """
        if not self._license_validator:
            return True  # No license configured, no limits
        return self._license_validator.is_within_limits(metric, value)

    def track_usage(self, traces: int = 0, spans: int = 0, api_calls: int = 0) -> None:
        """
        Track usage for license telemetry.

        This is called automatically by trace/span creation, but can be
        called manually for custom tracking.

        Args:
            traces: Number of traces created
            spans: Number of spans created
            api_calls: Number of API calls made
        """
        if self._license_validator:
            self._license_validator.track_usage(
                traces=traces,
                spans=spans,
                api_calls=api_calls,
            )

    async def validate_license(self, force: bool = False) -> Optional["LicenseInfo"]:
        """
        Manually validate the license.

        Args:
            force: Force validation even if cached

        Returns:
            LicenseInfo if valid, raises exception otherwise
        """
        if self._license_validator:
            self._license_info = await self._license_validator.validate(force=force)
            return self._license_info
        return None

    def get_license_status(self) -> Dict[str, Any]:
        """
        Get comprehensive license status for display.

        Returns:
            Dict with license status information
        """
        if not self._license_info:
            return {
                "configured": False,
                "valid": True,  # No license = no restrictions
                "tier": None,
                "features": {},
                "usage": None,
            }

        usage = None
        if self._license_validator and self._license_validator.usage_summary:
            summary = self._license_validator.usage_summary
            usage = {
                "traces_this_month": summary.traces_this_month,
                "traces_remaining": summary.traces_remaining,
                "spans_this_month": summary.spans_this_month,
                "active_users": summary.active_users,
            }

        return {
            "configured": True,
            "valid": self._license_info.valid,
            "tier": self._license_info.tier,
            "features": self._license_info.features,
            "max_seats": self._license_info.max_seats,
            "max_traces_per_month": self._license_info.max_traces_per_month,
            "max_projects": self._license_info.max_projects,
            "expires_at": self._license_info.expires_at.isoformat() if self._license_info.expires_at else None,
            "is_unlimited": self._license_info.is_unlimited,
            "usage": usage,
        }

    # ========== Self-Hosted Health Checks ==========

    async def check_connection(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Verify connectivity to the Aigie backend.

        Use this to check if the backend is reachable and responding.
        Useful for self-hosted deployments to verify installation.

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dict with connection status:
            - connected: bool - Whether connection succeeded
            - latency_ms: float - Round-trip latency in milliseconds
            - api_url: str - The API URL that was tested
            - error: str - Error message if connection failed
        """
        import time

        result = {
            "connected": False,
            "latency_ms": None,
            "api_url": self.api_url,
            "error": None,
            "server_version": None,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                start = time.monotonic()
                response = await client.get(
                    f"{self.api_url}/v1/health",
                    headers={"X-API-Key": self.api_key} if self.api_key else {},
                )
                latency = (time.monotonic() - start) * 1000

                result["latency_ms"] = round(latency, 2)

                if response.status_code == 200:
                    result["connected"] = True
                    try:
                        health_data = response.json()
                        result["server_version"] = health_data.get("version")
                    except Exception:
                        pass
                else:
                    result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"

        except httpx.ConnectError as e:
            result["error"] = f"Connection failed: {e}"
        except httpx.TimeoutException:
            result["error"] = f"Connection timed out after {timeout}s"
        except Exception as e:
            result["error"] = f"Unexpected error: {type(e).__name__}: {e}"

        return result

    async def get_installation_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status for self-hosted installations.

        Returns a complete health check including:
        - Backend connectivity
        - License status
        - Configuration validation
        - Feature availability

        Returns:
            Dict with installation status
        """
        status = {
            "healthy": True,
            "components": {},
            "warnings": [],
            "errors": [],
        }

        # Check backend connection
        connection = await self.check_connection()
        status["components"]["backend"] = {
            "status": "healthy" if connection["connected"] else "unhealthy",
            "latency_ms": connection["latency_ms"],
            "api_url": connection["api_url"],
            "error": connection["error"],
        }
        if not connection["connected"]:
            status["healthy"] = False
            status["errors"].append(f"Backend unreachable: {connection['error']}")

        # Check configuration
        config_warnings = self.config.validate_self_hosted()
        if config_warnings:
            status["warnings"].extend(config_warnings)
            status["components"]["configuration"] = {
                "status": "warning",
                "warnings": config_warnings,
            }
        else:
            status["components"]["configuration"] = {"status": "healthy"}

        # Check license status
        license_status = self.get_license_status()
        if license_status["configured"]:
            if license_status["valid"]:
                status["components"]["license"] = {
                    "status": "healthy",
                    "tier": license_status["tier"],
                    "features": list(license_status.get("features", {}).keys()),
                }
            else:
                status["healthy"] = False
                status["errors"].append("License validation failed")
                status["components"]["license"] = {"status": "unhealthy"}
        else:
            status["components"]["license"] = {
                "status": "not_configured",
                "message": "No license configured - operating in unlimited mode",
            }

        # Check buffer status
        if self._buffer:
            buffer_stats = {
                "status": "healthy",
                "pending_events": len(self._buffer._buffer) if hasattr(self._buffer, '_buffer') else 0,
            }
            status["components"]["buffer"] = buffer_stats
        else:
            status["components"]["buffer"] = {"status": "disabled"}

        # Check interception status
        if self._interceptor_chain:
            status["components"]["interception"] = {"status": "enabled"}
        else:
            status["components"]["interception"] = {"status": "disabled"}

        return status


def init(
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Config] = None,
    enable_auto_instrument: Optional[bool] = None,
    **kwargs
) -> Aigie:
    """
    Initialize global Aigie instance with auto-instrumentation.
    
    This is the recommended way to initialize Aigie for automatic instrumentation.
    After calling init(), all LangChain, LangGraph, and LLM calls will be automatically traced.
    
    Usage:
        from aigie import init
        
        # Initialize with auto-instrumentation enabled
        init(api_key="your-key", api_url="http://localhost:8000/api")
        
        # Now all workflows are automatically traced
        from langchain.agents import create_agent
        agent = create_agent(...)
        result = await agent.ainvoke({"input": "..."})  # Automatically traced!
    
    Args:
        api_url: Aigie API URL (defaults to AIGIE_API_URL env var)
        api_key: API key for authentication (defaults to AIGIE_API_KEY env var)
        config: Optional Config object (if provided, overrides api_url/api_key)
        enable_auto_instrument: Enable auto-instrumentation (defaults to True unless AIGIE_DISABLE_AUTO_INSTRUMENT is set)
        **kwargs: Additional config options passed to Config
    
    Returns:
        Initialized Aigie instance
    """
    global _global_aigie, _instrumentation_enabled
    
    # Check if auto-instrumentation should be enabled
    if enable_auto_instrument is None:
        # Check environment variable
        disable_env = os.getenv("AIGIE_DISABLE_AUTO_INSTRUMENT", "").lower()
        enable_auto_instrument = disable_env not in ("true", "1", "yes")
    
    # Create config if not provided
    if config is None:
        if api_url or api_key or kwargs:
            # Create config from parameters
            config_kwargs = {"api_url": api_url, "api_key": api_key}
            config_kwargs.update(kwargs)
            config = Config(**{k: v for k, v in config_kwargs.items() if v is not None})
        else:
            # Use default config (reads from env vars)
            config = Config()
    
    # Create global instance
    _global_aigie = Aigie(config=config)
    
    # Initialize synchronously (using asyncio.run for compatibility)
    # Note: This will block if called from async context, but that's acceptable
    # for initialization. Users can also call await aigie.initialize() manually.
    try:
        # Check if we're in an async context
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop and loop.is_running():
            # We're in an async context - create task for background initialization
            # Note: This means auto-instrumentation might enable slightly after init() returns
            # but that's acceptable for async contexts
            asyncio.create_task(_global_aigie.initialize())
        else:
            # No running loop - we can use run_until_complete or run
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    asyncio.run(_global_aigie.initialize())
                else:
                    loop.run_until_complete(_global_aigie.initialize())
            except RuntimeError:
                # No event loop exists, create one
                asyncio.run(_global_aigie.initialize())
    except Exception as e:
        # If initialization fails, log but don't raise (allow lazy init)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Aigie initialization failed: {e}. Will retry on first use.")
    
    # Enable auto-instrumentation if requested
    if enable_auto_instrument:
        _enable_auto_instrumentation()
    
    return _global_aigie


def get_aigie() -> Optional[Aigie]:
    """
    Get the global Aigie instance.
    
    Returns:
        Global Aigie instance if initialized, None otherwise
    """
    return _global_aigie


def _enable_auto_instrumentation() -> None:
    """Enable auto-instrumentation for all supported frameworks."""
    global _instrumentation_enabled
    
    if _instrumentation_enabled:
        return  # Already enabled
    
    # Import and enable auto-instrumentation modules
    try:
        from .auto_instrument import enable_all
        enable_all()
        _instrumentation_enabled = True
    except ImportError as e:
        # Auto-instrumentation modules not available yet
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Auto-instrumentation not available: {e}")


