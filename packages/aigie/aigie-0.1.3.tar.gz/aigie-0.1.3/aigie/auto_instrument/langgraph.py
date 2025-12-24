"""
LangGraph auto-instrumentation.

Automatically patches LangGraph workflows to create traces and inject handlers.
"""

import functools
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_patched_classes = set()


def patch_langgraph() -> None:
    """Patch LangGraph classes for auto-instrumentation."""
    _patch_state_graph()
    _patch_compiled_graph()


def _patch_state_graph() -> None:
    """Patch StateGraph.compile() to return auto-instrumented app."""
    try:
        from langgraph.graph import StateGraph
        
        if StateGraph in _patched_classes:
            return
        
        original_compile = StateGraph.compile
        
        @functools.wraps(original_compile)
        def traced_compile(self, **kwargs):
            """Traced version of compile."""
            app = original_compile(self, **kwargs)
            
            # Patch the compiled app's invoke methods
            if hasattr(app, 'ainvoke'):
                original_ainvoke = app.ainvoke
                
                async def traced_ainvoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    from ..client import get_aigie
                    from ..langgraph import LangGraphHandler
                    from ..callback import AigieCallbackHandler
                    from ..auto_instrument.trace import get_or_create_trace
                    
                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        trace = await get_or_create_trace(
                            name="LangGraph Workflow",
                            metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                        )
                        
                        # Create LangChain callback handler for LLM/tool tracking FIRST
                        # This creates the trace and tracks LLM/tool calls
                        callback_handler = AigieCallbackHandler(trace=trace)
                        
                        # Create LangGraph handler for node tracking
                        # Share the same trace context so they use the same trace
                        langgraph_handler = LangGraphHandler(
                            trace_name="LangGraph Workflow",
                            metadata={"type": "langgraph"}
                        )
                        langgraph_handler._aigie = aigie
                        langgraph_handler._trace_context = trace  # Share trace context
                        langgraph_handler.trace_id = trace.id if trace else None
                        
                        # Inject both handlers into config
                        if config is None:
                            config = {}
                        if 'callbacks' not in config:
                            config['callbacks'] = []
                        config['callbacks'].append(langgraph_handler)
                        config['callbacks'].append(callback_handler)  # Add LangChain callback handler
                    
                    return await original_ainvoke(inputs, config=config, **kwargs)
                
                app.ainvoke = traced_ainvoke
            
            if hasattr(app, 'invoke'):
                original_invoke = app.invoke
                
                def traced_invoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    """Traced version of invoke."""
                    from ..client import get_aigie
                    from ..langgraph import LangGraphHandler
                    from ..callback import AigieCallbackHandler
                    from ..auto_instrument.trace import get_or_create_trace_sync
                    
                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        trace = get_or_create_trace_sync(
                            name="LangGraph Workflow",
                            metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                        )
                        
                        if trace:
                            # Create LangChain callback handler for LLM/tool tracking FIRST
                            callback_handler = AigieCallbackHandler(trace=trace)
                            
                            # Create LangGraph handler for node tracking
                            langgraph_handler = LangGraphHandler(
                                trace_name="LangGraph Workflow",
                                metadata={"type": "langgraph"}
                            )
                            langgraph_handler._aigie = aigie
                            langgraph_handler._trace_context = trace  # Share trace context
                            langgraph_handler.trace_id = trace.id if trace else None
                            
                            if config is None:
                                config = {}
                            if 'callbacks' not in config:
                                config['callbacks'] = []
                            config['callbacks'].append(langgraph_handler)
                            config['callbacks'].append(callback_handler)  # Add LangChain callback handler
                    
                    return original_invoke(inputs, config=config, **kwargs)
                
                app.invoke = traced_invoke
            
            return app
        
        StateGraph.compile = traced_compile
        _patched_classes.add(StateGraph)
        
        logger.debug("Patched StateGraph.compile for auto-instrumentation")
        
    except ImportError:
        pass  # LangGraph not installed
    except Exception as e:
        logger.warning(f"Failed to patch StateGraph: {e}")


def _patch_compiled_graph() -> None:
    """Patch CompiledGraph methods directly."""
    try:
        from langgraph.graph.graph import CompiledGraph
        
        if CompiledGraph in _patched_classes:
            return
        
        original_ainvoke = CompiledGraph.ainvoke
        original_invoke = CompiledGraph.invoke
        
        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.ainvoke."""
            from ..client import get_aigie
            from ..langgraph import LangGraphHandler
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace
            
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
                langgraph_handler._trace_context = trace  # Share trace context
                langgraph_handler.trace_id = trace.id if trace else None
                
                if config is None:
                    config = {}
                if 'callbacks' not in config:
                    config['callbacks'] = []
                config['callbacks'].append(langgraph_handler)
                config['callbacks'].append(callback_handler)  # Add LangChain callback handler
            
            return await original_ainvoke(self, inputs, config=config, **kwargs)
        
        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.invoke."""
            from ..client import get_aigie
            from ..langgraph import LangGraphHandler
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace_sync
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                trace = get_or_create_trace_sync(
                    name="LangGraph Workflow",
                    metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                )
                
                if trace:
                    # Create LangGraph handler for node tracking
                    langgraph_handler = LangGraphHandler(
                        trace_name="LangGraph Workflow",
                        metadata={"type": "langgraph"}
                    )
                    langgraph_handler._aigie = aigie
                    langgraph_handler.trace_id = trace.id if trace else None
                    
                    # Create LangChain callback handler for LLM/tool tracking
                    callback_handler = AigieCallbackHandler(trace=trace)
                    
                    if config is None:
                        config = {}
                    if 'callbacks' not in config:
                        config['callbacks'] = []
                    config['callbacks'].append(langgraph_handler)
                    config['callbacks'].append(callback_handler)  # Add LangChain callback handler
            
            return original_invoke(self, inputs, config=config, **kwargs)
        
        CompiledGraph.ainvoke = traced_ainvoke
        CompiledGraph.invoke = traced_invoke
        _patched_classes.add(CompiledGraph)
        
        logger.debug("Patched CompiledGraph for auto-instrumentation")
        
    except ImportError:
        pass  # LangGraph not installed
    except Exception as e:
        logger.warning(f"Failed to patch CompiledGraph: {e}")

