"""
DSPy Handler for Aigie integration.

Provides event-driven tracing for DSPy module executions,
predictions, and optimizations.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DSPyHandler:
    """Handler for DSPy tracing integration.

    This handler provides lifecycle methods for tracing DSPy programs,
    including modules, predictions, retrievers, and optimizers.

    Example:
        handler = DSPyHandler(trace_name="DSPy Program")
        handler.set_trace_context(trace)

        # Track module execution
        module_id = await handler.handle_module_start(
            module_name="GenerateAnswer",
            module_type="predict",
            signature="question -> answer",
        )

        # Track prediction
        pred_id = await handler.handle_prediction_start(
            model="gpt-4o",
            input_fields={"question": "What is AI?"},
            parent_span_id=module_id,
        )

        await handler.handle_prediction_end(pred_id, output_fields, tokens)
        await handler.handle_module_end(module_id, result)
    """

    def __init__(
        self,
        trace_name: str = "DSPy Program",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Initialize the handler.

        Args:
            trace_name: Name for the trace
            metadata: Additional metadata to attach
            tags: Tags for filtering
            user_id: User identifier
            session_id: Session identifier
        """
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id

        # State tracking
        self.trace_id: Optional[str] = None
        self.span_map: Dict[str, Dict[str, Any]] = {}
        self._current_span_id: Optional[str] = None
        self._trace_context: Any = None
        self._aigie: Any = None

        # Statistics
        self.total_tokens = 0
        self.total_cost = 0.0
        self.module_count = 0
        self.prediction_count = 0
        self.retrieval_count = 0

    def set_trace_context(self, trace: Any) -> None:
        """Set the trace context for this handler."""
        self._trace_context = trace
        if hasattr(trace, 'id'):
            self.trace_id = trace.id

    async def handle_module_start(
        self,
        module_name: str,
        module_type: str = "module",
        signature: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle module execution start event.

        Args:
            module_name: Name of the module
            module_type: Type (predict, cot, react, retriever, etc.)
            signature: Module signature
            inputs: Input arguments
            parent_span_id: Parent span ID

        Returns:
            Module span ID
        """
        module_id = str(uuid.uuid4())
        self.module_count += 1

        span_data = {
            "name": f"dspy:{module_name}",
            "type": self._map_module_type(module_type),
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "module_name": module_name,
                "module_type": module_type,
                "signature": signature,
            },
        }

        if inputs:
            span_data["input"] = self._safe_str(inputs)

        self.span_map[module_id] = span_data
        self._current_span_id = module_id

        logger.debug(f"Started module trace: {module_name}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=module_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type=span_data["type"],
                    input=span_data.get("input"),
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating module span: {e}")

        return module_id

    async def handle_module_end(
        self,
        module_id: str,
        output: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle module execution end event.

        Args:
            module_id: Module span ID
            output: Module output (Prediction object)
            error: Error message if failed
        """
        if module_id not in self.span_map:
            return

        span_data = self.span_map[module_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        if output is not None:
            span_data["output"] = self._serialize_prediction(output)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        # Restore parent span as current
        self._current_span_id = span_data.get("parent_span_id")

        logger.debug(f"Ended module trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=module_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating module span: {e}")

    async def handle_prediction_start(
        self,
        model: Optional[str] = None,
        input_fields: Optional[Dict[str, Any]] = None,
        signature: Optional[str] = None,
        demonstrations: Optional[List[Dict[str, Any]]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle LLM prediction start event.

        Args:
            model: Model name
            input_fields: Input field values
            signature: Prediction signature
            demonstrations: Few-shot examples
            parent_span_id: Parent span ID

        Returns:
            Prediction span ID
        """
        pred_id = str(uuid.uuid4())
        self.prediction_count += 1

        span_data = {
            "name": f"llm:{model or 'unknown'}",
            "type": "llm",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "model": model,
                "signature": signature,
                "demonstration_count": len(demonstrations) if demonstrations else 0,
            },
        }

        if input_fields:
            span_data["input"] = self._safe_str(input_fields)

        self.span_map[pred_id] = span_data

        logger.debug(f"Started prediction trace: {model}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=pred_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="llm",
                    input=span_data.get("input"),
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating prediction span: {e}")

        return pred_id

    async def handle_prediction_end(
        self,
        pred_id: str,
        output_fields: Optional[Dict[str, Any]] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        """Handle LLM prediction end event.

        Args:
            pred_id: Prediction span ID
            output_fields: Output field values
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Cost of the prediction
            error: Error message if failed
        """
        if pred_id not in self.span_map:
            return

        span_data = self.span_map[pred_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        # Update totals
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += cost

        span_data["metadata"].update({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
        })

        if output_fields:
            span_data["output"] = self._safe_str(output_fields)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        logger.debug(f"Ended prediction trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=pred_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                    usage={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "cost": cost,
                    },
                )
            except Exception as e:
                logger.debug(f"Error updating prediction span: {e}")

    async def handle_retrieval_start(
        self,
        retriever_name: str,
        query: Optional[str] = None,
        k: int = 5,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle retrieval start event.

        Args:
            retriever_name: Name of the retriever
            query: Query string
            k: Number of results to retrieve
            parent_span_id: Parent span ID

        Returns:
            Retrieval span ID
        """
        retrieval_id = str(uuid.uuid4())
        self.retrieval_count += 1

        span_data = {
            "name": f"retrieve:{retriever_name}",
            "type": "tool",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "retriever_name": retriever_name,
                "k": k,
            },
        }

        if query:
            span_data["input"] = query[:500]

        self.span_map[retrieval_id] = span_data

        logger.debug(f"Started retrieval trace: {retriever_name}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=retrieval_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="tool",
                    input=span_data.get("input"),
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating retrieval span: {e}")

        return retrieval_id

    async def handle_retrieval_end(
        self,
        retrieval_id: str,
        passages: Optional[List[Any]] = None,
        scores: Optional[List[float]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle retrieval end event.

        Args:
            retrieval_id: Retrieval span ID
            passages: Retrieved passages
            scores: Relevance scores
            error: Error message if failed
        """
        if retrieval_id not in self.span_map:
            return

        span_data = self.span_map[retrieval_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        span_data["metadata"]["num_results"] = len(passages) if passages else 0

        if scores:
            span_data["metadata"]["avg_score"] = sum(scores) / len(scores) if scores else 0
            span_data["metadata"]["max_score"] = max(scores) if scores else 0

        if passages:
            # Summarize passages
            span_data["output"] = f"Retrieved {len(passages)} passages"
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        logger.debug(f"Ended retrieval trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=retrieval_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating retrieval span: {e}")

    async def handle_reasoning_step(
        self,
        step_type: str,
        step_number: int,
        thought: Optional[str] = None,
        action: Optional[str] = None,
        observation: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle a reasoning step (CoT, ReAct).

        Args:
            step_type: Type of reasoning step
            step_number: Step number in the chain
            thought: Reasoning thought
            action: Action taken
            observation: Observation from action
            parent_span_id: Parent span ID

        Returns:
            Step span ID
        """
        step_id = str(uuid.uuid4())

        span_data = {
            "name": f"reasoning:{step_type}:step_{step_number}",
            "type": "chain",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "step_type": step_type,
                "step_number": step_number,
            },
        }

        if thought:
            span_data["metadata"]["thought"] = thought[:500]
        if action:
            span_data["metadata"]["action"] = action
        if observation:
            span_data["metadata"]["observation"] = observation[:500]

        self.span_map[step_id] = span_data

        logger.debug(f"Recorded reasoning step: {step_type} #{step_number}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=step_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="chain",
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating reasoning step span: {e}")

        return step_id

    async def handle_optimization_start(
        self,
        optimizer_name: str,
        metric_name: Optional[str] = None,
        num_candidates: int = 0,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle optimization/compilation start event.

        Args:
            optimizer_name: Name of the optimizer
            metric_name: Metric being optimized
            num_candidates: Number of candidates to evaluate
            parent_span_id: Parent span ID

        Returns:
            Optimization span ID
        """
        opt_id = str(uuid.uuid4())

        span_data = {
            "name": f"optimize:{optimizer_name}",
            "type": "chain",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "optimizer_name": optimizer_name,
                "metric_name": metric_name,
                "num_candidates": num_candidates,
            },
        }

        self.span_map[opt_id] = span_data
        self._current_span_id = opt_id

        logger.debug(f"Started optimization trace: {optimizer_name}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=opt_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="chain",
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating optimization span: {e}")

        return opt_id

    async def handle_optimization_end(
        self,
        opt_id: str,
        best_score: Optional[float] = None,
        iterations: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """Handle optimization/compilation end event.

        Args:
            opt_id: Optimization span ID
            best_score: Best metric score achieved
            iterations: Number of iterations run
            error: Error message if failed
        """
        if opt_id not in self.span_map:
            return

        span_data = self.span_map[opt_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        span_data["metadata"].update({
            "best_score": best_score,
            "iterations": iterations,
        })

        if best_score is not None:
            span_data["output"] = f"Best score: {best_score:.4f}"
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        # Restore parent span as current
        self._current_span_id = span_data.get("parent_span_id")

        logger.debug(f"Ended optimization trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=opt_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating optimization span: {e}")

    def _map_module_type(self, module_type: str) -> str:
        """Map DSPy module type to span type.

        Args:
            module_type: DSPy module type

        Returns:
            Aigie span type
        """
        type_mapping = {
            "predict": "llm",
            "cot": "chain",
            "chain_of_thought": "chain",
            "react": "agent",
            "retriever": "tool",
            "retrieve": "tool",
            "module": "chain",
            "program": "chain",
        }
        return type_mapping.get(module_type.lower(), "chain")

    def _safe_str(self, value: Any, max_length: int = 2000) -> str:
        """Safely convert value to string with length limit."""
        try:
            if value is None:
                return ""
            s = str(value)
            if len(s) > max_length:
                return s[:max_length] + "..."
            return s
        except Exception:
            return "<error converting to string>"

    def _serialize_prediction(self, prediction: Any) -> str:
        """Serialize a DSPy Prediction object."""
        try:
            if hasattr(prediction, '__dict__'):
                fields = {k: str(v)[:200] for k, v in prediction.__dict__.items()
                         if not k.startswith('_')}
                return str(fields)
            return str(prediction)[:500]
        except Exception:
            return "<error serializing prediction>"

    def get_statistics(self) -> Dict[str, Any]:
        """Get current tracing statistics."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "module_count": self.module_count,
            "prediction_count": self.prediction_count,
            "retrieval_count": self.retrieval_count,
            "span_count": len(self.span_map),
        }
