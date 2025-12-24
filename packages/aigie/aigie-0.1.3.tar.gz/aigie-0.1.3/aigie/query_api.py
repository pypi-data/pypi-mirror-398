"""
Query API for programmatic trace and span retrieval.

This module provides a Pythonic interface for querying traces, spans,
and observations from the Aigie API.

Features:
- List and filter traces
- Get trace details
- Query observations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import httpx


class SortOrder(str, Enum):
    """Sort order for query results."""
    ASC = "asc"
    DESC = "desc"


class ObservationType(str, Enum):
    """Types of observations."""
    SPAN = "span"
    GENERATION = "generation"
    EVENT = "event"


@dataclass
class TraceFilter:
    """Filter options for trace queries."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[List[str]] = None
    environment: Optional[str] = None
    release: Optional[str] = None
    from_timestamp: Optional[datetime] = None
    to_timestamp: Optional[datetime] = None
    has_error: Optional[bool] = None
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_params(self) -> Dict[str, Any]:
        """Convert filter to API query parameters."""
        params = {}
        if self.user_id:
            params["user_id"] = self.user_id
        if self.session_id:
            params["session_id"] = self.session_id
        if self.name:
            params["name"] = self.name
        if self.tags:
            params["tags"] = ",".join(self.tags)
        if self.environment:
            params["environment"] = self.environment
        if self.release:
            params["release"] = self.release
        if self.from_timestamp:
            params["from_timestamp"] = self.from_timestamp.isoformat()
        if self.to_timestamp:
            params["to_timestamp"] = self.to_timestamp.isoformat()
        if self.has_error is not None:
            params["has_error"] = str(self.has_error).lower()
        if self.min_duration_ms is not None:
            params["min_duration_ms"] = self.min_duration_ms
        if self.max_duration_ms is not None:
            params["max_duration_ms"] = self.max_duration_ms
        return params


@dataclass
class Trace:
    """Represents a trace from the API."""
    id: str
    name: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None
    duration_ms: Optional[float] = None
    total_cost: Optional[float] = None
    total_tokens: Optional[int] = None
    observations_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trace":
        """Create Trace from API response dict."""
        timestamp = data.get("timestamp") or data.get("created_at")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            timestamp=timestamp,
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            input=data.get("input"),
            output=data.get("output"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            status=data.get("status"),
            duration_ms=data.get("duration_ms"),
            total_cost=data.get("total_cost"),
            total_tokens=data.get("total_tokens"),
            observations_count=data.get("observations_count", 0),
        )


@dataclass
class Observation:
    """Represents an observation (span/generation/event) from the API."""
    id: str
    trace_id: str
    type: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    parent_id: Optional[str] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    level: Optional[str] = None
    status: Optional[str] = None
    duration_ms: Optional[float] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    cost: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Observation":
        """Create Observation from API response dict."""
        start_time = data.get("start_time") or data.get("created_at")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

        end_time = data.get("end_time")
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            trace_id=data.get("trace_id", ""),
            type=data.get("type", "span"),
            name=data.get("name", ""),
            start_time=start_time,
            end_time=end_time,
            parent_id=data.get("parent_id"),
            input=data.get("input"),
            output=data.get("output"),
            metadata=data.get("metadata", {}),
            level=data.get("level"),
            status=data.get("status"),
            duration_ms=data.get("duration_ms"),
            model=data.get("model"),
            usage=data.get("usage"),
            cost=data.get("cost"),
        )


@dataclass
class PaginatedResponse:
    """Paginated response from the API."""
    data: List[Any]
    total: int
    page: int
    limit: int
    has_more: bool

    @property
    def pages(self) -> int:
        """Calculate total number of pages."""
        if self.limit <= 0:
            return 0
        return (self.total + self.limit - 1) // self.limit


class TraceAPI:
    """API client for trace operations."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def list(
        self,
        limit: int = 50,
        page: int = 1,
        order_by: str = "timestamp",
        order: SortOrder = SortOrder.DESC,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        filter: Optional[TraceFilter] = None,
    ) -> PaginatedResponse:
        """
        List traces with optional filtering and pagination.

        Args:
            limit: Maximum number of traces to return (max 100)
            page: Page number (1-indexed)
            order_by: Field to order by
            order: Sort order (asc/desc)
            user_id: Filter by user ID
            session_id: Filter by session ID
            name: Filter by trace name (partial match)
            tags: Filter by tags (all must match)
            from_timestamp: Start of time range
            to_timestamp: End of time range
            filter: TraceFilter object for advanced filtering

        Returns:
            PaginatedResponse containing Trace objects
        """
        params = {
            "limit": min(limit, 100),
            "page": page,
            "order_by": order_by,
            "order": order.value,
        }

        # Apply individual filters
        if user_id:
            params["user_id"] = user_id
        if session_id:
            params["session_id"] = session_id
        if name:
            params["name"] = name
        if tags:
            params["tags"] = ",".join(tags)
        if from_timestamp:
            params["from_timestamp"] = from_timestamp.isoformat()
        if to_timestamp:
            params["to_timestamp"] = to_timestamp.isoformat()

        # Apply filter object if provided
        if filter:
            params.update(filter.to_params())

        response = await self.client.get(
            f"{self.base_url}/v1/traces",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        traces = [Trace.from_dict(t) for t in data.get("data", data.get("traces", []))]
        return PaginatedResponse(
            data=traces,
            total=data.get("total", len(traces)),
            page=page,
            limit=limit,
            has_more=data.get("has_more", len(traces) >= limit),
        )

    async def get(self, trace_id: str) -> Trace:
        """
        Get a single trace by ID.

        Args:
            trace_id: The trace ID

        Returns:
            Trace object
        """
        response = await self.client.get(f"{self.base_url}/v1/traces/{trace_id}")
        response.raise_for_status()
        return Trace.from_dict(response.json())

    async def get_with_observations(self, trace_id: str) -> Dict[str, Any]:
        """
        Get a trace with all its observations.

        Args:
            trace_id: The trace ID

        Returns:
            Dict containing trace and observations
        """
        trace = await self.get(trace_id)
        observations = await self._get_observations_for_trace(trace_id)
        return {
            "trace": trace,
            "observations": observations,
        }

    async def _get_observations_for_trace(self, trace_id: str) -> List[Observation]:
        """Get all observations for a trace."""
        response = await self.client.get(
            f"{self.base_url}/v1/traces/{trace_id}/observations"
        )
        response.raise_for_status()
        data = response.json()
        return [Observation.from_dict(o) for o in data.get("observations", data.get("data", []))]

    async def delete(self, trace_id: str) -> bool:
        """
        Delete a trace.

        Args:
            trace_id: The trace ID

        Returns:
            True if deleted successfully
        """
        response = await self.client.delete(f"{self.base_url}/v1/traces/{trace_id}")
        return response.status_code in (200, 204)


class ObservationsAPI:
    """API client for observation operations."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def get_many(
        self,
        trace_id: Optional[str] = None,
        type: Optional[ObservationType] = None,
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: int = 100,
        page: int = 1,
        order: SortOrder = SortOrder.DESC,
    ) -> PaginatedResponse:
        """
        Get multiple observations with filtering.

        Args:
            trace_id: Filter by trace ID
            type: Filter by observation type
            name: Filter by name (partial match)
            parent_id: Filter by parent observation ID
            limit: Maximum results (max 100)
            page: Page number
            order: Sort order

        Returns:
            PaginatedResponse containing Observation objects
        """
        params = {
            "limit": min(limit, 100),
            "page": page,
            "order": order.value,
        }

        if trace_id:
            params["trace_id"] = trace_id
        if type:
            params["type"] = type.value
        if name:
            params["name"] = name
        if parent_id:
            params["parent_id"] = parent_id

        response = await self.client.get(
            f"{self.base_url}/v1/observations",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        observations = [Observation.from_dict(o) for o in data.get("data", data.get("observations", []))]
        return PaginatedResponse(
            data=observations,
            total=data.get("total", len(observations)),
            page=page,
            limit=limit,
            has_more=data.get("has_more", len(observations) >= limit),
        )

    async def get(self, observation_id: str) -> Observation:
        """
        Get a single observation by ID.

        Args:
            observation_id: The observation ID

        Returns:
            Observation object
        """
        response = await self.client.get(
            f"{self.base_url}/v1/observations/{observation_id}"
        )
        response.raise_for_status()
        return Observation.from_dict(response.json())


class SessionsAPI:
    """API client for session operations."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def list(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
    ) -> PaginatedResponse:
        """
        List sessions.

        Args:
            user_id: Filter by user ID
            limit: Maximum results
            page: Page number

        Returns:
            PaginatedResponse containing session data
        """
        params = {"limit": limit, "page": page}
        if user_id:
            params["user_id"] = user_id

        response = await self.client.get(
            f"{self.base_url}/v1/sessions",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        return PaginatedResponse(
            data=data.get("data", data.get("sessions", [])),
            total=data.get("total", 0),
            page=page,
            limit=limit,
            has_more=data.get("has_more", False),
        )

    async def get(self, session_id: str) -> Dict[str, Any]:
        """Get a session with its traces."""
        response = await self.client.get(
            f"{self.base_url}/v1/sessions/{session_id}"
        )
        response.raise_for_status()
        return response.json()


class ScoresAPI:
    """API client for scores/feedback operations."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def create(
        self,
        trace_id: str,
        name: str,
        value: Union[float, int, bool, str],
        observation_id: Optional[str] = None,
        comment: Optional[str] = None,
        data_type: Literal["NUMERIC", "CATEGORICAL", "BOOLEAN"] = "NUMERIC",
    ) -> Dict[str, Any]:
        """
        Create a score/feedback for a trace or observation.

        Args:
            trace_id: The trace ID
            name: Score name (e.g., "accuracy", "helpfulness")
            value: Score value
            observation_id: Optional observation ID to score
            comment: Optional comment
            data_type: Type of score data

        Returns:
            Created score data
        """
        payload = {
            "trace_id": trace_id,
            "name": name,
            "value": value,
            "data_type": data_type,
        }
        if observation_id:
            payload["observation_id"] = observation_id
        if comment:
            payload["comment"] = comment

        response = await self.client.post(
            f"{self.base_url}/v1/scores",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def list(
        self,
        trace_id: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List scores with optional filtering."""
        params = {"limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        if name:
            params["name"] = name

        response = await self.client.get(
            f"{self.base_url}/v1/scores",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", data.get("scores", []))


class QueryAPI:
    """
    Main Query API class providing access to all query operations.

    Usage:
        aigie = Aigie()
        await aigie.initialize()

        # List traces
        traces = await aigie.api.trace.list(
            limit=100,
            user_id="user_123",
            tags=["production"]
        )

        # Get single trace
        trace = await aigie.api.trace.get("trace_id")

        # Get observations
        observations = await aigie.api.observations.get_many(
            trace_id="trace_id",
            type=ObservationType.GENERATION
        )

        # Create score/feedback
        await aigie.api.scores.create(
            trace_id="trace_id",
            name="accuracy",
            value=0.95
        )
    """

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.trace = TraceAPI(client, base_url)
        self.observations = ObservationsAPI(client, base_url)
        self.sessions = SessionsAPI(client, base_url)
        self.scores = ScoresAPI(client, base_url)

    # Convenience methods
    async def get_recent_traces(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Trace]:
        """Get traces from the last N hours."""
        from_time = datetime.utcnow() - timedelta(hours=hours)
        result = await self.trace.list(
            limit=limit,
            from_timestamp=from_time,
            order=SortOrder.DESC,
        )
        return result.data

    async def get_user_traces(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[Trace]:
        """Get all traces for a user."""
        result = await self.trace.list(
            limit=limit,
            user_id=user_id,
            order=SortOrder.DESC,
        )
        return result.data

    async def get_session_traces(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[Trace]:
        """Get all traces for a session."""
        result = await self.trace.list(
            limit=limit,
            session_id=session_id,
            order=SortOrder.ASC,  # Chronological order for sessions
        )
        return result.data

    async def get_error_traces(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Trace]:
        """Get traces with errors from the last N hours."""
        from_time = datetime.utcnow() - timedelta(hours=hours)
        filter = TraceFilter(
            from_timestamp=from_time,
            has_error=True,
        )
        result = await self.trace.list(
            limit=limit,
            filter=filter,
            order=SortOrder.DESC,
        )
        return result.data

    async def search_traces(
        self,
        query: str,
        limit: int = 50,
    ) -> List[Trace]:
        """Search traces by name."""
        result = await self.trace.list(
            limit=limit,
            name=query,
        )
        return result.data
