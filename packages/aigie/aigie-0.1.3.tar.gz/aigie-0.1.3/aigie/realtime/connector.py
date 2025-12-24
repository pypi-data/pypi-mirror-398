"""
BackendConnector - WebSocket connection for real-time backend consultation.

Provides bidirectional communication with the Aigie backend for:
- Real-time interception decisions
- Leveraging historical data and patterns
- Receiving proactive fixes and recommendations
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Optional, Dict, Any, Callable, Awaitable, List, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from ..interceptor.protocols import (
        InterceptionContext,
        PreCallResult,
        PostCallResult,
        FixAction,
    )

logger = logging.getLogger("aigie.realtime")


class ConnectionState(Enum):
    """WebSocket connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConsultationRequest:
    """Request for backend consultation."""

    request_id: str
    """Unique request ID for correlation."""

    consultation_type: str
    """Type: 'pre_call', 'post_call', 'drift_check', 'fix_request'."""

    context: Dict[str, Any]
    """Serialized interception context."""

    urgency: str = "normal"
    """Urgency level: 'low', 'normal', 'high', 'critical'."""

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConsultationResponse:
    """Response from backend consultation."""

    request_id: str
    """Correlated request ID."""

    decision: str
    """Decision: 'allow', 'block', 'modify', 'retry'."""

    reason: Optional[str] = None
    """Reason for the decision."""

    fixes: List[Dict[str, Any]] = field(default_factory=list)
    """List of fix actions to apply."""

    modified_request: Optional[Dict[str, Any]] = None
    """Modified request parameters."""

    modified_response: Optional[Dict[str, Any]] = None
    """Modified response content."""

    confidence: float = 0.0
    """Confidence score for this decision."""

    latency_ms: float = 0.0
    """Backend processing latency."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata from backend."""


class BackendConnector:
    """
    WebSocket connector for real-time backend communication.

    Features:
    - Automatic connection management with reconnection
    - Request/response correlation
    - Subscription to backend push events
    - Graceful degradation on connection issues
    - Performance tracking
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        auto_reconnect: bool = True,
        reconnect_interval: float = 5.0,
        max_reconnect_attempts: int = 10,
        ping_interval: float = 30.0,
        request_timeout: float = 0.5,  # 500ms default
    ):
        """
        Initialize the backend connector.

        Args:
            api_url: Base API URL (will be converted to WebSocket URL)
            api_key: API key for authentication
            auto_reconnect: Whether to automatically reconnect on disconnect
            reconnect_interval: Base interval between reconnection attempts
            max_reconnect_attempts: Maximum reconnection attempts
            ping_interval: Interval for keepalive pings
            request_timeout: Default timeout for consultation requests
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = ws_url.rstrip("/api").rstrip("/")
        self._ws_url = f"{ws_url}/ws"

        self._api_key = api_key
        self._auto_reconnect = auto_reconnect
        self._reconnect_interval = reconnect_interval
        self._max_reconnect_attempts = max_reconnect_attempts
        self._ping_interval = ping_interval
        self._request_timeout = request_timeout

        self._state = ConnectionState.DISCONNECTED
        self._websocket = None
        self._reconnect_attempts = 0

        # Request/response tracking
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # Background tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Callbacks for push events
        self._fix_callbacks: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._alert_callbacks: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []

        # Statistics
        self._stats = {
            "consultations": 0,
            "successful_responses": 0,
            "timeouts": 0,
            "errors": 0,
            "reconnections": 0,
            "total_latency_ms": 0.0,
        }

    @property
    def is_connected(self) -> bool:
        """Check if connected to backend."""
        return self._state == ConnectionState.CONNECTED and self._websocket is not None

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to backend.

        Returns:
            True if connected successfully, False otherwise
        """
        if self._state == ConnectionState.CONNECTED:
            return True

        self._state = ConnectionState.CONNECTING
        logger.info(f"Connecting to backend: {self._ws_url}")

        try:
            import websockets

            headers = {
                "X-API-Key": self._api_key,
                "X-Client-Type": "sdk",
                "X-Client-Version": "2.0.0",
            }

            self._websocket = await asyncio.wait_for(
                websockets.connect(
                    self._ws_url,
                    extra_headers=headers,
                    ping_interval=self._ping_interval,
                    ping_timeout=10,
                ),
                timeout=10.0,
            )

            self._state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            logger.info("Connected to backend successfully")

            # Start background tasks
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._ping_task = asyncio.create_task(self._ping_loop())

            # Subscribe to relevant event types
            await self._subscribe(["remediation", "prevention", "fixes"])

            return True

        except ImportError:
            logger.warning("websockets package not installed, backend realtime disabled")
            self._state = ConnectionState.FAILED
            return False

        except Exception as e:
            logger.error(f"Failed to connect to backend: {e}")
            self._state = ConnectionState.FAILED

            if self._auto_reconnect:
                asyncio.create_task(self._reconnect())

            return False

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._state = ConnectionState.DISCONNECTED

        # Cancel background tasks
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        # Cancel pending requests
        for future in self._pending_requests.values():
            future.cancel()
        self._pending_requests.clear()

        logger.info("Disconnected from backend")

    async def consult_pre_call(
        self,
        ctx: "InterceptionContext",
        timeout: Optional[float] = None,
    ) -> Optional["PreCallResult"]:
        """
        Consult backend for pre-call decision.

        Args:
            ctx: Interception context
            timeout: Request timeout (default: self._request_timeout)

        Returns:
            PreCallResult if successful, None on timeout/error
        """
        from ..interceptor.protocols import PreCallResult, InterceptionDecision

        if not self.is_connected:
            return None

        request = ConsultationRequest(
            request_id=str(uuid.uuid4()),
            consultation_type="pre_call",
            context=self._serialize_context(ctx),
        )

        response = await self._send_consultation(request, timeout or self._request_timeout)

        if response is None:
            return None

        # Convert response to PreCallResult
        decision_map = {
            "allow": InterceptionDecision.ALLOW,
            "block": InterceptionDecision.BLOCK,
            "modify": InterceptionDecision.MODIFY,
        }

        decision = decision_map.get(response.decision, InterceptionDecision.ALLOW)

        if decision == InterceptionDecision.BLOCK:
            return PreCallResult.block(
                reason=response.reason or "Blocked by backend",
                hook_name="backend",
                latency_ms=response.latency_ms,
            )

        if decision == InterceptionDecision.MODIFY and response.modified_request:
            return PreCallResult.modify(
                messages=response.modified_request.get("messages"),
                kwargs=response.modified_request.get("kwargs"),
                reason=response.reason,
                hook_name="backend",
                latency_ms=response.latency_ms,
            )

        return PreCallResult.allow(hook_name="backend", latency_ms=response.latency_ms)

    async def consult_post_call(
        self,
        ctx: "InterceptionContext",
        timeout: Optional[float] = None,
    ) -> Optional["PostCallResult"]:
        """
        Consult backend for post-call decision and fixes.

        Args:
            ctx: Interception context with response
            timeout: Request timeout

        Returns:
            PostCallResult if successful, None on timeout/error
        """
        from ..interceptor.protocols import PostCallResult, InterceptionDecision, FixAction, FixActionType

        if not self.is_connected:
            return None

        request = ConsultationRequest(
            request_id=str(uuid.uuid4()),
            consultation_type="post_call",
            context=self._serialize_context(ctx),
            urgency="high" if ctx.error else "normal",
        )

        response = await self._send_consultation(request, timeout or self._request_timeout)

        if response is None:
            return None

        # Convert fixes
        fixes = []
        for fix_data in response.fixes:
            action_type = FixActionType.MODIFY_RESPONSE
            if fix_data.get("action_type") == "retry":
                action_type = FixActionType.RETRY
            elif fix_data.get("action_type") == "fallback":
                action_type = FixActionType.FALLBACK

            fixes.append(
                FixAction(
                    action_type=action_type,
                    parameters=fix_data.get("parameters", {}),
                    confidence=fix_data.get("confidence", 0.8),
                    source="backend",
                    reason=fix_data.get("reason"),
                )
            )

        # Check if retry is needed
        if response.decision == "retry":
            return PostCallResult.retry(
                reason=response.reason or "Backend requested retry",
                retry_kwargs=response.modified_request,
                hook_name="backend",
                latency_ms=response.latency_ms,
            )

        # Return modification result
        if response.modified_response or fixes:
            return PostCallResult.modify(
                response=response.modified_response,
                content=response.modified_response.get("content") if response.modified_response else None,
                reason=response.reason,
                fixes=fixes,
                hook_name="backend",
                latency_ms=response.latency_ms,
            )

        return PostCallResult.allow(hook_name="backend", latency_ms=response.latency_ms)

    def on_fix_push(
        self, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Register callback for backend-pushed fixes."""
        self._fix_callbacks.append(callback)

    def on_alert(
        self, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Register callback for backend alerts."""
        self._alert_callbacks.append(callback)

    async def _send_consultation(
        self,
        request: ConsultationRequest,
        timeout: float,
    ) -> Optional[ConsultationResponse]:
        """Send consultation request and wait for response."""
        if not self._websocket:
            return None

        self._stats["consultations"] += 1
        start_time = time.perf_counter()

        try:
            # Create future for response
            future = asyncio.get_event_loop().create_future()
            self._pending_requests[request.request_id] = future

            # Send request
            message = {
                "type": "consultation",
                "request_id": request.request_id,
                "consultation_type": request.consultation_type,
                "context": request.context,
                "urgency": request.urgency,
                "timestamp": request.timestamp.isoformat(),
            }

            await self._websocket.send(json.dumps(message))

            # Wait for response
            response_data = await asyncio.wait_for(future, timeout=timeout)

            latency = (time.perf_counter() - start_time) * 1000
            self._stats["successful_responses"] += 1
            self._stats["total_latency_ms"] += latency

            return ConsultationResponse(
                request_id=request.request_id,
                decision=response_data.get("decision", "allow"),
                reason=response_data.get("reason"),
                fixes=response_data.get("fixes", []),
                modified_request=response_data.get("modified_request"),
                modified_response=response_data.get("modified_response"),
                confidence=response_data.get("confidence", 0.0),
                latency_ms=latency,
                metadata=response_data.get("metadata", {}),
            )

        except asyncio.TimeoutError:
            self._stats["timeouts"] += 1
            logger.debug(f"Consultation request timed out after {timeout}s")
            return None

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Consultation request failed: {e}")
            return None

        finally:
            self._pending_requests.pop(request.request_id, None)

    async def _receive_loop(self) -> None:
        """Background task to receive messages from backend."""
        while self._state == ConnectionState.CONNECTED and self._websocket:
            try:
                message = await self._websocket.recv()
                data = json.loads(message)

                msg_type = data.get("type")

                if msg_type == "consultation_response":
                    # Handle consultation response
                    request_id = data.get("request_id")
                    if request_id in self._pending_requests:
                        future = self._pending_requests[request_id]
                        if not future.done():
                            future.set_result(data)

                elif msg_type == "fix_push":
                    # Handle pushed fix
                    for callback in self._fix_callbacks:
                        asyncio.create_task(callback(data))

                elif msg_type == "alert":
                    # Handle alert
                    for callback in self._alert_callbacks:
                        asyncio.create_task(callback(data))

                elif msg_type == "pong":
                    # Ping response, ignore
                    pass

            except Exception as e:
                if self._state == ConnectionState.CONNECTED:
                    logger.error(f"Receive error: {e}")
                    await self._handle_disconnect()
                break

    async def _ping_loop(self) -> None:
        """Background task for keepalive pings."""
        while self._state == ConnectionState.CONNECTED and self._websocket:
            try:
                await asyncio.sleep(self._ping_interval)
                if self._websocket:
                    await self._websocket.send(json.dumps({"type": "ping"}))
            except Exception:
                break

    async def _subscribe(self, event_types: List[str]) -> None:
        """Subscribe to backend event types."""
        if self._websocket:
            await self._websocket.send(
                json.dumps({
                    "type": "subscribe",
                    "event_types": event_types,
                })
            )

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnection."""
        self._state = ConnectionState.DISCONNECTED
        if self._auto_reconnect:
            asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect to backend."""
        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._state = ConnectionState.RECONNECTING
            self._reconnect_attempts += 1
            self._stats["reconnections"] += 1

            wait_time = self._reconnect_interval * (2 ** (self._reconnect_attempts - 1))
            logger.info(f"Reconnecting in {wait_time:.1f}s (attempt {self._reconnect_attempts})")

            await asyncio.sleep(wait_time)

            if await self.connect():
                return

        logger.error("Max reconnection attempts reached")
        self._state = ConnectionState.FAILED

    def _serialize_context(self, ctx: "InterceptionContext") -> Dict[str, Any]:
        """Serialize interception context for transmission."""
        return {
            "provider": ctx.provider,
            "model": ctx.model,
            "messages": ctx.messages[-5:] if ctx.messages else [],  # Last 5 messages
            "trace_id": ctx.trace_id,
            "span_id": ctx.span_id,
            "estimated_cost": ctx.estimated_cost,
            "accumulated_cost": ctx.accumulated_cost,
            "drift_score": ctx.drift_score,
            "context_hash": ctx.context_hash,
            "error": str(ctx.error) if ctx.error else None,
            "error_type": ctx.error_type,
            "user_id": ctx.user_id,
            "session_id": ctx.session_id,
            "response_content": ctx.response_content[:1000] if ctx.response_content else None,
            "actual_cost": ctx.actual_cost,
            "response_time_ms": ctx.response_time_ms,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics."""
        return {
            **self._stats,
            "state": self._state.value,
            "pending_requests": len(self._pending_requests),
            "avg_latency_ms": (
                self._stats["total_latency_ms"]
                / max(self._stats["successful_responses"], 1)
            ),
        }
