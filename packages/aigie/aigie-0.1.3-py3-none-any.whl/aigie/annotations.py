"""
Human Annotations system for manual labeling, scoring, and feedback.

Features:
- Attach annotations to traces or observations
- Support for different annotation types (score, label, text, thumbs)
- Queue management for annotation tasks
- Bulk annotation support
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Literal, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx


class AnnotationType(str, Enum):
    """Types of annotations."""
    SCORE = "score"           # Numeric score (0-1, 1-5, etc.)
    LABEL = "label"           # Categorical label
    TEXT = "text"             # Free-form text comment
    THUMBS = "thumbs"         # Thumbs up/down
    BOOLEAN = "boolean"       # True/False
    RANKING = "ranking"       # Rank ordering


class AnnotationStatus(str, Enum):
    """Status of annotation tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class AnnotationConfig:
    """Configuration for an annotation type."""
    name: str
    type: AnnotationType
    description: Optional[str] = None
    # For SCORE type
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    # For LABEL type
    labels: Optional[List[str]] = None
    # For RANKING type
    ranking_options: Optional[List[str]] = None
    # General
    required: bool = False
    default_value: Optional[Any] = None


@dataclass
class Annotation:
    """Represents a human annotation."""
    id: str
    trace_id: str
    observation_id: Optional[str] = None
    name: str = ""
    type: AnnotationType = AnnotationType.TEXT
    value: Any = None
    comment: Optional[str] = None
    annotator_id: Optional[str] = None
    annotator_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API."""
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "observation_id": self.observation_id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, AnnotationType) else self.type,
            "value": self.value,
            "comment": self.comment,
            "annotator_id": self.annotator_id,
            "annotator_name": self.annotator_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Annotation":
        """Create from API response."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            trace_id=data.get("trace_id", ""),
            observation_id=data.get("observation_id"),
            name=data.get("name", ""),
            type=AnnotationType(data.get("type", "text")),
            value=data.get("value"),
            comment=data.get("comment"),
            annotator_id=data.get("annotator_id"),
            annotator_name=data.get("annotator_name"),
            created_at=created_at or datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AnnotationTask:
    """A task in the annotation queue."""
    id: str
    trace_id: str
    observation_id: Optional[str] = None
    status: AnnotationStatus = AnnotationStatus.PENDING
    assigned_to: Optional[str] = None
    config: Optional[AnnotationConfig] = None
    trace_data: Optional[Dict[str, Any]] = None
    annotations: List[Annotation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    priority: int = 0  # Higher = more urgent


class AnnotationQueue:
    """
    Manages a queue of items to be annotated.

    Usage:
        queue = AnnotationQueue(aigie)

        # Add items to queue
        await queue.add_trace("trace_id", priority=1)
        await queue.add_traces(["trace_1", "trace_2", "trace_3"])

        # Get next item to annotate
        task = await queue.get_next()

        # Submit annotation
        await queue.submit_annotation(
            task_id=task.id,
            name="quality",
            value=0.9,
            comment="Good response"
        )

        # Mark as complete
        await queue.complete_task(task.id)
    """

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self._local_queue: List[AnnotationTask] = []
        self._configs: Dict[str, AnnotationConfig] = {}

    def configure(self, *configs: AnnotationConfig) -> None:
        """Configure annotation types for this queue."""
        for config in configs:
            self._configs[config.name] = config

    async def add_trace(
        self,
        trace_id: str,
        priority: int = 0,
        assigned_to: Optional[str] = None,
    ) -> AnnotationTask:
        """Add a trace to the annotation queue."""
        from uuid import uuid4

        task = AnnotationTask(
            id=str(uuid4()),
            trace_id=trace_id,
            priority=priority,
            assigned_to=assigned_to,
        )

        # Try to submit to API
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/annotation-queue",
                json={
                    "trace_id": trace_id,
                    "priority": priority,
                    "assigned_to": assigned_to,
                }
            )
            if response.status_code == 200:
                data = response.json()
                task.id = data.get("id", task.id)
        except Exception:
            pass  # Use local queue as fallback

        self._local_queue.append(task)
        self._local_queue.sort(key=lambda t: -t.priority)
        return task

    async def add_traces(
        self,
        trace_ids: List[str],
        priority: int = 0,
    ) -> List[AnnotationTask]:
        """Add multiple traces to the queue."""
        tasks = []
        for trace_id in trace_ids:
            task = await self.add_trace(trace_id, priority)
            tasks.append(task)
        return tasks

    async def get_next(
        self,
        assigned_to: Optional[str] = None,
    ) -> Optional[AnnotationTask]:
        """Get the next item to annotate."""
        # Try API first
        try:
            params = {}
            if assigned_to:
                params["assigned_to"] = assigned_to

            response = await self.client.get(
                f"{self.base_url}/v1/annotation-queue/next",
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    return AnnotationTask(
                        id=data["id"],
                        trace_id=data["trace_id"],
                        observation_id=data.get("observation_id"),
                        status=AnnotationStatus(data.get("status", "pending")),
                        trace_data=data.get("trace_data"),
                    )
        except Exception:
            pass

        # Fallback to local queue
        for task in self._local_queue:
            if task.status == AnnotationStatus.PENDING:
                if assigned_to is None or task.assigned_to == assigned_to:
                    task.status = AnnotationStatus.IN_PROGRESS
                    return task

        return None

    async def get_pending_count(self) -> int:
        """Get count of pending annotation tasks."""
        try:
            response = await self.client.get(
                f"{self.base_url}/v1/annotation-queue/count"
            )
            if response.status_code == 200:
                return response.json().get("count", 0)
        except Exception:
            pass

        return sum(1 for t in self._local_queue if t.status == AnnotationStatus.PENDING)

    async def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        # Update API
        try:
            response = await self.client.patch(
                f"{self.base_url}/v1/annotation-queue/{task_id}",
                json={"status": "completed"}
            )
        except Exception:
            pass

        # Update local
        for task in self._local_queue:
            if task.id == task_id:
                task.status = AnnotationStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                return True

        return False

    async def skip_task(self, task_id: str, reason: Optional[str] = None) -> bool:
        """Skip an annotation task."""
        try:
            response = await self.client.patch(
                f"{self.base_url}/v1/annotation-queue/{task_id}",
                json={"status": "skipped", "skip_reason": reason}
            )
        except Exception:
            pass

        for task in self._local_queue:
            if task.id == task_id:
                task.status = AnnotationStatus.SKIPPED
                return True

        return False


class AnnotationsAPI:
    """
    API for managing annotations on traces and observations.

    Usage:
        # Create annotation
        await aigie.annotations.create(
            trace_id="trace_123",
            name="accuracy",
            type=AnnotationType.SCORE,
            value=0.95,
            comment="Excellent response"
        )

        # Thumbs up/down
        await aigie.annotations.thumbs_up("trace_123")
        await aigie.annotations.thumbs_down("trace_123", comment="Off topic")

        # Label annotation
        await aigie.annotations.label(
            trace_id="trace_123",
            name="category",
            value="support",
            labels=["support", "sales", "technical"]
        )

        # Get annotations for trace
        annotations = await aigie.annotations.list(trace_id="trace_123")

        # Annotation queue
        queue = aigie.annotations.queue
        await queue.add_trace("trace_123")
        task = await queue.get_next()
    """

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.queue = AnnotationQueue(client, base_url)

    async def create(
        self,
        trace_id: str,
        name: str,
        type: AnnotationType = AnnotationType.TEXT,
        value: Any = None,
        observation_id: Optional[str] = None,
        comment: Optional[str] = None,
        annotator_id: Optional[str] = None,
        annotator_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Annotation:
        """
        Create a new annotation.

        Args:
            trace_id: The trace to annotate
            name: Annotation name (e.g., "accuracy", "helpfulness")
            type: Type of annotation
            value: Annotation value
            observation_id: Optional specific observation to annotate
            comment: Optional comment
            annotator_id: ID of the annotator
            annotator_name: Name of the annotator
            metadata: Additional metadata

        Returns:
            Created Annotation object
        """
        from uuid import uuid4

        annotation = Annotation(
            id=str(uuid4()),
            trace_id=trace_id,
            observation_id=observation_id,
            name=name,
            type=type,
            value=value,
            comment=comment,
            annotator_id=annotator_id,
            annotator_name=annotator_name,
            metadata=metadata or {},
        )

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/annotations",
                json=annotation.to_dict()
            )
            if response.status_code in (200, 201):
                data = response.json()
                annotation.id = data.get("id", annotation.id)
        except Exception:
            pass  # Annotation created locally

        return annotation

    async def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        min_value: float = 0.0,
        max_value: float = 1.0,
        observation_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Annotation:
        """Create a score annotation."""
        # Validate range
        if not (min_value <= value <= max_value):
            raise ValueError(f"Value {value} must be between {min_value} and {max_value}")

        return await self.create(
            trace_id=trace_id,
            name=name,
            type=AnnotationType.SCORE,
            value=value,
            observation_id=observation_id,
            comment=comment,
            metadata={"min_value": min_value, "max_value": max_value},
        )

    async def label(
        self,
        trace_id: str,
        name: str,
        value: str,
        labels: Optional[List[str]] = None,
        observation_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Annotation:
        """Create a label annotation."""
        if labels and value not in labels:
            raise ValueError(f"Value '{value}' not in allowed labels: {labels}")

        return await self.create(
            trace_id=trace_id,
            name=name,
            type=AnnotationType.LABEL,
            value=value,
            observation_id=observation_id,
            comment=comment,
            metadata={"labels": labels} if labels else {},
        )

    async def thumbs_up(
        self,
        trace_id: str,
        observation_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Annotation:
        """Create a thumbs up annotation."""
        return await self.create(
            trace_id=trace_id,
            name="thumbs",
            type=AnnotationType.THUMBS,
            value=True,
            observation_id=observation_id,
            comment=comment,
        )

    async def thumbs_down(
        self,
        trace_id: str,
        observation_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Annotation:
        """Create a thumbs down annotation."""
        return await self.create(
            trace_id=trace_id,
            name="thumbs",
            type=AnnotationType.THUMBS,
            value=False,
            observation_id=observation_id,
            comment=comment,
        )

    async def comment(
        self,
        trace_id: str,
        text: str,
        observation_id: Optional[str] = None,
    ) -> Annotation:
        """Create a text comment annotation."""
        return await self.create(
            trace_id=trace_id,
            name="comment",
            type=AnnotationType.TEXT,
            value=text,
            observation_id=observation_id,
        )

    async def list(
        self,
        trace_id: Optional[str] = None,
        observation_id: Optional[str] = None,
        name: Optional[str] = None,
        type: Optional[AnnotationType] = None,
        annotator_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Annotation]:
        """
        List annotations with optional filtering.

        Args:
            trace_id: Filter by trace
            observation_id: Filter by observation
            name: Filter by annotation name
            type: Filter by annotation type
            annotator_id: Filter by annotator
            limit: Maximum results

        Returns:
            List of Annotation objects
        """
        params = {"limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        if observation_id:
            params["observation_id"] = observation_id
        if name:
            params["name"] = name
        if type:
            params["type"] = type.value
        if annotator_id:
            params["annotator_id"] = annotator_id

        try:
            response = await self.client.get(
                f"{self.base_url}/v1/annotations",
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                return [Annotation.from_dict(a) for a in data.get("data", data.get("annotations", []))]
        except Exception:
            pass

        return []

    async def get(self, annotation_id: str) -> Optional[Annotation]:
        """Get a single annotation by ID."""
        try:
            response = await self.client.get(
                f"{self.base_url}/v1/annotations/{annotation_id}"
            )
            if response.status_code == 200:
                return Annotation.from_dict(response.json())
        except Exception:
            pass

        return None

    async def update(
        self,
        annotation_id: str,
        value: Optional[Any] = None,
        comment: Optional[str] = None,
    ) -> Optional[Annotation]:
        """Update an existing annotation."""
        payload = {}
        if value is not None:
            payload["value"] = value
        if comment is not None:
            payload["comment"] = comment

        try:
            response = await self.client.patch(
                f"{self.base_url}/v1/annotations/{annotation_id}",
                json=payload
            )
            if response.status_code == 200:
                return Annotation.from_dict(response.json())
        except Exception:
            pass

        return None

    async def delete(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        try:
            response = await self.client.delete(
                f"{self.base_url}/v1/annotations/{annotation_id}"
            )
            return response.status_code in (200, 204)
        except Exception:
            return False

    async def bulk_create(
        self,
        annotations: List[Dict[str, Any]],
    ) -> List[Annotation]:
        """
        Create multiple annotations at once.

        Args:
            annotations: List of annotation dicts with keys:
                - trace_id (required)
                - name (required)
                - type
                - value
                - comment
                - observation_id

        Returns:
            List of created Annotation objects
        """
        results = []
        for ann_data in annotations:
            annotation = await self.create(
                trace_id=ann_data["trace_id"],
                name=ann_data["name"],
                type=AnnotationType(ann_data.get("type", "text")),
                value=ann_data.get("value"),
                observation_id=ann_data.get("observation_id"),
                comment=ann_data.get("comment"),
            )
            results.append(annotation)
        return results
