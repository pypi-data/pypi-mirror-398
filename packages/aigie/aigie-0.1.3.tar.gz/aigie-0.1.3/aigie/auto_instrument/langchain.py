"""
LangChain auto-instrumentation.

Automatically patches LangChain classes to inject Aigie callbacks and create traces.
"""

import functools
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_patched_classes = set()


def patch_langchain() -> None:
    """Patch LangChain classes for auto-instrumentation."""
    _patch_agent_executor()
    _patch_create_agent()
    _patch_chain_base()
    _patch_runnable()


def _patch_agent_executor() -> None:
    """Patch AgentExecutor to auto-inject callbacks."""
    try:
        from langchain.agents import AgentExecutor
        
        if AgentExecutor in _patched_classes:
            return
        
        original_ainvoke = AgentExecutor.ainvoke
        original_invoke = AgentExecutor.invoke
        
        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Dict[str, Any], **kwargs) -> Any:
            """Traced version of ainvoke."""
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                # Get agent name safely
                agent_name = "agent"
                agent_class = None
                if hasattr(self, 'agent'):
                    agent = getattr(self, 'agent')
                    # Try to get name from various possible attributes
                    if hasattr(agent, 'name'):
                        agent_name = getattr(agent, 'name', 'agent')
                    elif hasattr(agent, '__class__'):
                        agent_name = agent.__class__.__name__
                        agent_class = f"{agent.__class__.__module__}.{agent.__class__.__name__}"
                    elif isinstance(agent, dict):
                        agent_name = agent.get('name', 'agent')
                
                # Extract tool names from AgentExecutor
                tool_names = []
                if hasattr(self, 'tools'):
                    tools = getattr(self, 'tools', [])
                    if tools:
                        for tool in tools:
                            if hasattr(tool, 'name'):
                                tool_names.append(tool.name)
                            elif isinstance(tool, dict):
                                tool_names.append(tool.get('name', 'unknown_tool'))
                            elif isinstance(tool, str):
                                tool_names.append(tool)
                
                # Extract workflow type from inputs or metadata
                workflow_type = None
                domain = None
                if isinstance(inputs, dict):
                    workflow_type = inputs.get('workflow_type')
                    domain = inputs.get('domain')
                    # Also check nested structures
                    if not workflow_type and 'metadata' in inputs:
                        workflow_type = inputs['metadata'].get('workflow_type')
                    if not domain and 'metadata' in inputs:
                        domain = inputs['metadata'].get('domain')
                
                # Create workflow type identifier
                workflow_type_id = workflow_type
                if not workflow_type_id:
                    # Generate from agent + tools
                    tool_count = len(tool_names)
                    if tool_count > 0:
                        workflow_type_id = f"{agent_name}_{tool_count}tools"
                    else:
                        workflow_type_id = agent_name.lower().replace("agent", "").strip() or "agent_workflow"
                
                # Build enriched metadata
                trace_metadata = {
                    "type": "agent_executor",
                    "inputs": inputs,
                    "agent_type": agent_name,
                    "workflow_type": workflow_type_id
                }
                
                if agent_class:
                    trace_metadata["agent_class"] = agent_class
                if tool_names:
                    trace_metadata["tools_used"] = tool_names
                if workflow_type:
                    trace_metadata["workflow_type"] = workflow_type
                    trace_metadata["original_workflow_type"] = workflow_type
                if domain:
                    trace_metadata["domain"] = domain
                
                # Clear any existing trace context to ensure each workflow gets its own trace
                from ..auto_instrument.trace import clear_current_trace
                clear_current_trace()
                
                # Create descriptive trace name with workflow context
                # Extract query from inputs for better trace naming
                query_snippet = ""
                if isinstance(inputs, dict):
                    query = inputs.get("input") or inputs.get("messages")
                    if query:
                        if isinstance(query, str):
                            query_snippet = query[:50] + "..." if len(query) > 50 else query
                        elif isinstance(query, list) and query:
                            # Extract from message list
                            first_msg = query[0]
                            if hasattr(first_msg, 'content'):
                                query_snippet = first_msg.content[:50] + "..." if len(first_msg.content) > 50 else first_msg.content
                            elif isinstance(first_msg, dict):
                                query_snippet = str(first_msg.get('content', ''))[:50]
                
                # Build trace name with workflow type and query context
                if workflow_type_id and query_snippet:
                    trace_name = f"{workflow_type_id.replace('_', ' ').title()}: {query_snippet}"
                elif workflow_type_id:
                    trace_name = f"{workflow_type_id.replace('_', ' ').title()} Workflow"
                elif query_snippet:
                    trace_name = f"{agent_name}: {query_snippet}"
                else:
                    trace_name = f"Agent: {agent_name}"
                
                # Create new trace for this workflow (don't reuse existing)
                trace = await get_or_create_trace(
                    name=trace_name,
                    metadata=trace_metadata
                )
                
                # Create callback handler
                callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                
                # Inject callback into config
                if 'config' not in kwargs:
                    kwargs['config'] = {}
                if 'callbacks' not in kwargs['config']:
                    kwargs['config']['callbacks'] = []
                kwargs['config']['callbacks'].append(callback)
            
            return await original_ainvoke(self, inputs, **kwargs)
        
        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Dict[str, Any], **kwargs) -> Any:
            """Traced version of invoke."""
            from ..auto_instrument.trace import get_or_create_trace_sync
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                # Get agent name safely
                agent_name = "agent"
                agent_class = None
                if hasattr(self, 'agent'):
                    agent = getattr(self, 'agent')
                    # Try to get name from various possible attributes
                    if hasattr(agent, 'name'):
                        agent_name = getattr(agent, 'name', 'agent')
                    elif hasattr(agent, '__class__'):
                        agent_name = agent.__class__.__name__
                        agent_class = f"{agent.__class__.__module__}.{agent.__class__.__name__}"
                    elif isinstance(agent, dict):
                        agent_name = agent.get('name', 'agent')
                
                # Extract tool names from AgentExecutor
                tool_names = []
                if hasattr(self, 'tools'):
                    tools = getattr(self, 'tools', [])
                    if tools:
                        for tool in tools:
                            if hasattr(tool, 'name'):
                                tool_names.append(tool.name)
                            elif isinstance(tool, dict):
                                tool_names.append(tool.get('name', 'unknown_tool'))
                            elif isinstance(tool, str):
                                tool_names.append(tool)
                
                # Extract workflow type from inputs, kwargs config metadata, or inputs metadata
                workflow_type = None
                domain = None
                
                # Check kwargs config metadata first (passed from app code)
                if 'config' in kwargs and isinstance(kwargs['config'], dict):
                    config_metadata = kwargs['config'].get('metadata', {})
                    if isinstance(config_metadata, dict):
                        workflow_type = config_metadata.get('workflow_type') or config_metadata.get('use_case')
                        domain = config_metadata.get('domain')
                
                # Fallback to inputs
                if isinstance(inputs, dict):
                    if not workflow_type:
                        workflow_type = inputs.get('workflow_type')
                    if not domain:
                        domain = inputs.get('domain')
                    # Also check nested structures
                    if not workflow_type and 'metadata' in inputs:
                        workflow_type = inputs['metadata'].get('workflow_type')
                    if not domain and 'metadata' in inputs:
                        domain = inputs['metadata'].get('domain')
                
                # Create workflow type identifier
                workflow_type_id = workflow_type
                if not workflow_type_id:
                    # Generate from agent + tools
                    tool_count = len(tool_names)
                    if tool_count > 0:
                        workflow_type_id = f"{agent_name}_{tool_count}tools"
                    else:
                        workflow_type_id = agent_name.lower().replace("agent", "").strip() or "agent_workflow"
                
                # Build enriched metadata
                trace_metadata = {
                    "type": "agent_executor",
                    "inputs": inputs,
                    "agent_type": agent_name,
                    "workflow_type": workflow_type_id
                }
                
                if agent_class:
                    trace_metadata["agent_class"] = agent_class
                if tool_names:
                    trace_metadata["tools_used"] = tool_names
                if workflow_type:
                    trace_metadata["workflow_type"] = workflow_type
                    trace_metadata["original_workflow_type"] = workflow_type
                if domain:
                    trace_metadata["domain"] = domain
                
                # Clear any existing trace context to ensure each workflow gets its own trace
                from ..auto_instrument.trace import clear_current_trace
                clear_current_trace()
                
                # Create descriptive trace name with workflow context
                # Extract query from inputs for better trace naming
                query_snippet = ""
                if isinstance(inputs, dict):
                    query = inputs.get("input") or inputs.get("messages")
                    if query:
                        if isinstance(query, str):
                            query_snippet = query[:50] + "..." if len(query) > 50 else query
                        elif isinstance(query, list) and query:
                            # Extract from message list
                            first_msg = query[0]
                            if hasattr(first_msg, 'content'):
                                query_snippet = first_msg.content[:50] + "..." if len(first_msg.content) > 50 else first_msg.content
                            elif isinstance(first_msg, dict):
                                query_snippet = str(first_msg.get('content', ''))[:50]
                
                # Build trace name with workflow type and query context
                if workflow_type_id and query_snippet:
                    trace_name = f"{workflow_type_id.replace('_', ' ').title()}: {query_snippet}"
                elif workflow_type_id:
                    trace_name = f"{workflow_type_id.replace('_', ' ').title()} Workflow"
                elif query_snippet:
                    trace_name = f"{agent_name}: {query_snippet}"
                else:
                    trace_name = f"Agent: {agent_name}"
                
                # Use sync version for sync invoke
                trace = get_or_create_trace_sync(
                    name=trace_name,
                    metadata=trace_metadata
                )
                
                if trace:
                    callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                    if 'config' not in kwargs:
                        kwargs['config'] = {}
                    if 'callbacks' not in kwargs['config']:
                        kwargs['config']['callbacks'] = []
                    kwargs['config']['callbacks'].append(callback)
            
            return original_invoke(self, inputs, **kwargs)
        
        AgentExecutor.ainvoke = traced_ainvoke
        AgentExecutor.invoke = traced_invoke
        _patched_classes.add(AgentExecutor)
        
        logger.debug("Patched AgentExecutor for auto-instrumentation")
        
    except ImportError:
        pass  # LangChain not installed
    except Exception as e:
        logger.warning(f"Failed to patch AgentExecutor: {e}")


def _patch_create_agent() -> None:
    """Patch create_agent function to return auto-instrumented agent."""
    try:
        from langchain.agents import create_agent
        
        if create_agent in _patched_classes:
            return
        
        original_create_agent = create_agent
        
        @functools.wraps(original_create_agent)
        def traced_create_agent(*args, **kwargs):
            """Traced version of create_agent."""
            agent = original_create_agent(*args, **kwargs)
            
            # Patch the agent's invoke methods
            if hasattr(agent, 'ainvoke'):
                original_ainvoke = agent.ainvoke
                
                async def traced_ainvoke(inputs: Dict[str, Any], **kwargs):
                    from ..client import get_aigie
                    from ..callback import AigieCallbackHandler
                    from ..auto_instrument.trace import get_or_create_trace
                    
                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        trace = await get_or_create_trace(
                            name="LangChain Agent",
                            metadata={"type": "agent", "inputs": inputs}
                        )
                        callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                        
                        if 'config' not in kwargs:
                            kwargs['config'] = {}
                        if 'callbacks' not in kwargs['config']:
                            kwargs['config']['callbacks'] = []
                        kwargs['config']['callbacks'].append(callback)
                    
                    return await original_ainvoke(inputs, **kwargs)
                
                agent.ainvoke = traced_ainvoke
            
            return agent
        
        # Replace the function
        import langchain.agents
        langchain.agents.create_agent = traced_create_agent
        _patched_classes.add(create_agent)
        
        logger.debug("Patched create_agent for auto-instrumentation")
        
    except ImportError:
        pass  # LangChain not installed
    except Exception as e:
        logger.warning(f"Failed to patch create_agent: {e}")


def _patch_chain_base() -> None:
    """Patch Chain base class to auto-instrument all chains."""
    try:
        from langchain_core.chains import Chain
        
        if Chain in _patched_classes:
            return
        
        original_ainvoke = Chain.ainvoke
        original_invoke = Chain.invoke
        
        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Dict[str, Any], **kwargs) -> Any:
            """Traced version of Chain.ainvoke."""
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                # Extract chain name from actual chain object (not hardcoded)
                chain_name = getattr(self, 'name', None)
                if not chain_name:
                    # Use class name as fallback
                    chain_name = type(self).__name__
                
                # Get full class path for metadata
                chain_class = f"{type(self).__module__}.{type(self).__name__}"
                
                # Clear any existing trace context to ensure each workflow gets its own trace
                from ..auto_instrument.trace import clear_current_trace
                clear_current_trace()
                
                # Pass chain class info through config metadata so callbacks can access it
                if 'config' not in kwargs:
                    kwargs['config'] = {}
                if 'metadata' not in kwargs['config']:
                    kwargs['config']['metadata'] = {}
                kwargs['config']['metadata']['chain_class'] = chain_class
                kwargs['config']['metadata']['chain_name'] = chain_name
                
                trace = await get_or_create_trace(
                    name=f"Chain: {chain_name}",
                    metadata={"type": "chain", "chain_class": chain_class, "inputs": inputs}
                )
                
                callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                
                if 'callbacks' not in kwargs['config']:
                    kwargs['config']['callbacks'] = []
                kwargs['config']['callbacks'].append(callback)
            
            return await original_ainvoke(self, inputs, **kwargs)
        
        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Dict[str, Any], **kwargs) -> Any:
            """Traced version of Chain.invoke."""
            from ..auto_instrument.trace import get_or_create_trace_sync
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                # Extract chain name from actual chain object (not hardcoded)
                chain_name = getattr(self, 'name', None)
                if not chain_name:
                    # Use class name as fallback
                    chain_name = type(self).__name__
                
                # Get full class path for metadata
                chain_class = f"{type(self).__module__}.{type(self).__name__}"
                
                # Clear any existing trace context to ensure each workflow gets its own trace
                from ..auto_instrument.trace import clear_current_trace
                clear_current_trace()
                
                # Pass chain class info through config metadata so callbacks can access it
                if 'config' not in kwargs:
                    kwargs['config'] = {}
                if 'metadata' not in kwargs['config']:
                    kwargs['config']['metadata'] = {}
                kwargs['config']['metadata']['chain_class'] = chain_class
                kwargs['config']['metadata']['chain_name'] = chain_name
                
                trace = get_or_create_trace_sync(
                    name=f"Chain: {chain_name}",
                    metadata={"type": "chain", "chain_class": chain_class, "inputs": inputs}
                )
                
                if trace:
                    callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                    if 'callbacks' not in kwargs['config']:
                        kwargs['config']['callbacks'] = []
                    kwargs['config']['callbacks'].append(callback)
            
            return original_invoke(self, inputs, **kwargs)
        
        Chain.ainvoke = traced_ainvoke
        Chain.invoke = traced_invoke
        _patched_classes.add(Chain)
        
        logger.debug("Patched Chain base class for auto-instrumentation")
        
    except ImportError:
        pass  # langchain_core not installed
    except Exception as e:
        logger.warning(f"Failed to patch Chain: {e}")


def _patch_runnable() -> None:
    """Patch Runnable base class for broader coverage."""
    try:
        from langchain_core.runnables import Runnable
        
        if Runnable in _patched_classes:
            return
        
        original_ainvoke = Runnable.ainvoke
        original_invoke = Runnable.invoke
        
        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Any, **kwargs) -> Any:
            """Traced version of Runnable.ainvoke."""
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                runnable_name = getattr(self, 'name', type(self).__name__)
                trace = await get_or_create_trace(
                    name=f"Runnable: {runnable_name}",
                    metadata={"type": "runnable", "runnable_class": type(self).__name__}
                )
                
                callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                
                if 'config' not in kwargs:
                    kwargs['config'] = {}
                if 'callbacks' not in kwargs['config']:
                    kwargs['config']['callbacks'] = []
                kwargs['config']['callbacks'].append(callback)
            
            return await original_ainvoke(self, inputs, **kwargs)
        
        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Any, **kwargs) -> Any:
            """Traced version of Runnable.invoke."""
            from ..auto_instrument.trace import get_or_create_trace_sync
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                runnable_name = getattr(self, 'name', type(self).__name__)
                trace = get_or_create_trace_sync(
                    name=f"Runnable: {runnable_name}",
                    metadata={"type": "runnable", "runnable_class": type(self).__name__}
                )
                
                if trace:
                    callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                    if 'config' not in kwargs:
                        kwargs['config'] = {}
                    if 'callbacks' not in kwargs['config']:
                        kwargs['config']['callbacks'] = []
                    kwargs['config']['callbacks'].append(callback)
            
            return original_invoke(self, inputs, **kwargs)
        
        Runnable.ainvoke = traced_ainvoke
        Runnable.invoke = traced_invoke
        _patched_classes.add(Runnable)
        
        logger.debug("Patched Runnable base class for auto-instrumentation")
        
    except ImportError:
        pass  # langchain_core not installed
    except Exception as e:
        logger.warning(f"Failed to patch Runnable: {e}")

