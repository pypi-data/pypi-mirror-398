"""
LangGraph auto-instrumentation.

Automatically patches LangGraph workflows to create traces and inject handlers.
"""

import functools
import logging
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

_patched_classes: Set[Any] = set()


def patch_langgraph() -> bool:
    """Patch LangGraph classes for auto-instrumentation.

    Returns:
        True if patching was successful (or already patched)
    """
    success = True
    success = _patch_state_graph() and success
    success = _patch_compiled_graph() and success
    return success


def unpatch_langgraph() -> None:
    """Remove LangGraph patches (for testing)."""
    global _patched_classes
    _patched_classes.clear()


def is_langgraph_patched() -> bool:
    """Check if LangGraph has been patched."""
    return len(_patched_classes) > 0


def _patch_state_graph() -> bool:
    """Patch StateGraph.compile() to return auto-instrumented app."""
    try:
        from langgraph.graph import StateGraph

        if StateGraph in _patched_classes:
            return True

        original_compile = StateGraph.compile

        @functools.wraps(original_compile)
        def traced_compile(self, **kwargs):
            """Traced version of compile."""
            app = original_compile(self, **kwargs)

            # Patch the compiled app's invoke methods
            if hasattr(app, 'ainvoke'):
                original_ainvoke = app.ainvoke

                async def traced_ainvoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    from ...client import get_aigie
                    from ...langgraph import LangGraphHandler
                    from ...callback import AigieCallbackHandler
                    from ...auto_instrument.trace import get_or_create_trace

                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        trace = await get_or_create_trace(
                            name="LangGraph Workflow",
                            metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                        )

                        # Create LangChain callback handler for LLM/tool tracking FIRST
                        callback_handler = AigieCallbackHandler(trace=trace)

                        # Create LangGraph handler for node tracking
                        langgraph_handler = LangGraphHandler(
                            trace_name="LangGraph Workflow",
                            metadata={"type": "langgraph"}
                        )
                        langgraph_handler._aigie = aigie
                        langgraph_handler._trace_context = trace
                        langgraph_handler.trace_id = trace.id if trace else None

                        if config is None:
                            config = {}
                        if 'callbacks' not in config:
                            config['callbacks'] = []
                        config['callbacks'].append(langgraph_handler)
                        config['callbacks'].append(callback_handler)

                    return await original_ainvoke(inputs, config=config, **kwargs)

                app.ainvoke = traced_ainvoke

            if hasattr(app, 'invoke'):
                original_invoke = app.invoke

                def traced_invoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    """Traced version of invoke."""
                    from ...client import get_aigie
                    from ...langgraph import LangGraphHandler
                    from ...callback import AigieCallbackHandler
                    from ...auto_instrument.trace import get_or_create_trace_sync

                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        trace = get_or_create_trace_sync(
                            name="LangGraph Workflow",
                            metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                        )

                        if trace:
                            callback_handler = AigieCallbackHandler(trace=trace)

                            langgraph_handler = LangGraphHandler(
                                trace_name="LangGraph Workflow",
                                metadata={"type": "langgraph"}
                            )
                            langgraph_handler._aigie = aigie
                            langgraph_handler._trace_context = trace
                            langgraph_handler.trace_id = trace.id if trace else None

                            if config is None:
                                config = {}
                            if 'callbacks' not in config:
                                config['callbacks'] = []
                            config['callbacks'].append(langgraph_handler)
                            config['callbacks'].append(callback_handler)

                    return original_invoke(inputs, config=config, **kwargs)

                app.invoke = traced_invoke

            return app

        StateGraph.compile = traced_compile
        _patched_classes.add(StateGraph)

        logger.debug("Patched StateGraph.compile for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("LangGraph not installed, skipping StateGraph patch")
        return True  # Not an error if LangGraph not installed
    except Exception as e:
        logger.warning(f"Failed to patch StateGraph: {e}")
        return False


def _patch_compiled_graph() -> bool:
    """Patch CompiledGraph methods directly."""
    try:
        from langgraph.graph.graph import CompiledGraph

        if CompiledGraph in _patched_classes:
            return True

        original_ainvoke = CompiledGraph.ainvoke
        original_invoke = CompiledGraph.invoke

        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.ainvoke."""
            from ...client import get_aigie
            from ...langgraph import LangGraphHandler
            from ...callback import AigieCallbackHandler
            from ...auto_instrument.trace import get_or_create_trace

            aigie = get_aigie()
            if aigie and aigie._initialized:
                trace = await get_or_create_trace(
                    name="LangGraph Workflow",
                    metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                )

                callback_handler = AigieCallbackHandler(trace=trace)

                langgraph_handler = LangGraphHandler(
                    trace_name="LangGraph Workflow",
                    metadata={"type": "langgraph"}
                )
                langgraph_handler._aigie = aigie
                langgraph_handler._trace_context = trace
                langgraph_handler.trace_id = trace.id if trace else None

                if config is None:
                    config = {}
                if 'callbacks' not in config:
                    config['callbacks'] = []
                config['callbacks'].append(langgraph_handler)
                config['callbacks'].append(callback_handler)

            return await original_ainvoke(self, inputs, config=config, **kwargs)

        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.invoke."""
            from ...client import get_aigie
            from ...langgraph import LangGraphHandler
            from ...callback import AigieCallbackHandler
            from ...auto_instrument.trace import get_or_create_trace_sync

            aigie = get_aigie()
            if aigie and aigie._initialized:
                trace = get_or_create_trace_sync(
                    name="LangGraph Workflow",
                    metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                )

                if trace:
                    langgraph_handler = LangGraphHandler(
                        trace_name="LangGraph Workflow",
                        metadata={"type": "langgraph"}
                    )
                    langgraph_handler._aigie = aigie
                    langgraph_handler.trace_id = trace.id if trace else None

                    callback_handler = AigieCallbackHandler(trace=trace)

                    if config is None:
                        config = {}
                    if 'callbacks' not in config:
                        config['callbacks'] = []
                    config['callbacks'].append(langgraph_handler)
                    config['callbacks'].append(callback_handler)

            return original_invoke(self, inputs, config=config, **kwargs)

        CompiledGraph.ainvoke = traced_ainvoke
        CompiledGraph.invoke = traced_invoke
        _patched_classes.add(CompiledGraph)

        logger.debug("Patched CompiledGraph for auto-instrumentation")
        return True

    except ImportError:
        return True
    except Exception as e:
        logger.warning(f"Failed to patch CompiledGraph: {e}")
        return False
