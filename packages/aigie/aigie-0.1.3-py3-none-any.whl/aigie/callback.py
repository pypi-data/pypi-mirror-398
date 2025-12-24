"""
LangChain/LangGraph Callback Handler for Aigie.
"""

import asyncio
from typing import Any, Dict, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from .client import Aigie
from .trace import TraceContext


class AigieCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for automatic trace/span creation.
    
    Usage:
        aigie = Aigie()
        await aigie.initialize()
        
        # Pass trace context to callback
        async with aigie.trace("My Workflow") as trace:
            callback = AigieCallbackHandler(trace=trace)
            result = await chain.ainvoke(
                input,
                config={"callbacks": [callback]}
            )
    """
    
    def __init__(self, aigie: Optional[Aigie] = None, trace: Optional[TraceContext] = None):
        """
        Initialize callback handler.
        
        Args:
            aigie: Aigie client instance (optional if trace provided)
            trace: Active trace context (preferred - avoids async issues)
        """
        super().__init__()
        self.aigie = aigie
        self.trace = trace
        self.span_stack = []
        self._span_contexts = {}  # Map run_id to span context
        self._pending_trace_name = None
        self._pending_trace_metadata = None
        self._root_run_id = None  # Track root chain run_id for trace completion
        
        # Execution path tracking for workflow execution data
        self._execution_paths: Dict[str, List[str]] = {}  # trace_id -> [span_name, ...]
        self._execution_timing: Dict[str, Dict[str, Dict[str, Any]]] = {}  # trace_id -> {span_name: {start_time, end_time, duration_ms}}
        self._execution_status: Dict[str, Dict[str, str]] = {}  # trace_id -> {span_name: status}
        self._execution_errors: Dict[str, Dict[str, str]] = {}  # trace_id -> {span_name: error_message}
        self._edge_conditions: Dict[str, List[Dict[str, Any]]] = {}  # trace_id -> [{step, condition, result}]
        self._agent_iterations: Dict[str, Dict[str, int]] = {}  # trace_id -> {agent_name: iteration_count}
        self._span_start_times: Dict[str, Dict[str, str]] = {}  # trace_id -> {span_name: iso_timestamp}
        self._retry_info: Dict[str, List[Dict[str, Any]]] = {}  # trace_id -> [{span_name, attempt, reason}]
        self._state_transitions: Dict[str, List[Dict[str, Any]]] = {}  # trace_id -> [{from_state, to_state, trigger}]
        self._nested_workflows: Dict[str, List[Dict[str, Any]]] = {}  # trace_id -> [{workflow_name, trace_id}]
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chain starts."""
        # Extract LangGraph node information from tags and metadata
        langgraph_node = None
        langgraph_step = None

        # Check metadata for LangGraph node info
        if metadata and isinstance(metadata, dict):
            langgraph_node = metadata.get('langgraph_node') or metadata.get('node') or metadata.get('graph_node')
            langgraph_step = metadata.get('langgraph_step') or metadata.get('step')

        # Check tags for LangGraph patterns
        if tags and isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str):
                    if tag.startswith('graph:') or tag.startswith('langgraph:'):
                        parts = tag.split(':')
                        if len(parts) >= 3 and parts[1] == 'step':
                            langgraph_node = langgraph_node or parts[2]
                    elif tag.startswith('seq:step:'):
                        try:
                            langgraph_step = langgraph_step or int(tag.split(':')[2])
                        except (ValueError, IndexError):
                            pass
                    elif tag.startswith('node:'):
                        langgraph_node = langgraph_node or tag.split(':', 1)[1]

        # Extract workflow metadata from LangChain config if available
        workflow_metadata = {}
        if metadata and isinstance(metadata, dict):
            workflow_type = metadata.get('workflow_type') or metadata.get('use_case')
            domain = metadata.get('domain')
            if workflow_type:
                workflow_metadata['workflow_type'] = workflow_type
            if domain:
                workflow_metadata['domain'] = domain

        # Store workflow metadata for later use
        if workflow_metadata:
            self._pending_trace_metadata = workflow_metadata
        
        # Extract chain name from LangChain's serialized dict (no hardcoding - pure extraction)
        def _get_chain_name(serialized: Optional[Dict[str, Any]]) -> str:
            # If serialized is None, we can't extract - return generic name
            if not serialized:
                return "chain_step"
            
            # Method 1: Extract from serialized["name"] (LangChain's primary identifier)
            name = serialized.get("name")
            if name and name not in ["chain", "Chain", "chain_step", ""]:
                return name
            
            # Method 2: Extract from serialized["id"] - LangChain's class path identifier
            # Format can be: ["langchain_core", "prompts", "chat", "ChatPromptTemplate"]
            # or: ["langchain", "chains", "llm", "LLMChain"]
            chain_id = serialized.get("id")
            if isinstance(chain_id, list) and chain_id:
                # Try each element in the id array (LangChain stores class path as array)
                for part in reversed(chain_id):  # Start from most specific (last element)
                    if isinstance(part, str):
                        # Extract class name from fully qualified path
                        if "." in part:
                            # Handle "langchain.chains.llm.LLMChain" format
                            parts = part.split(".")
                            class_name = parts[-1]
                        else:
                            # Handle just "LLMChain" format
                            class_name = part
                        
                        # Return the class name if it's meaningful
                        if class_name and class_name not in ["chain", "Chain", "chain_step", "", "chains", "prompts"]:
                            return class_name
                
                # Fallback: use first element if nothing else worked
                if chain_id[0]:
                    return str(chain_id[0])
            elif isinstance(chain_id, str):
                # Handle string format: "langchain.chains.llm.LLMChain"
                if "." in chain_id:
                    parts = chain_id.split(".")
                    class_name = parts[-1]
                    if class_name and class_name not in ["chain", "Chain", "chain_step"]:
                        return class_name
                elif chain_id not in ["chain", "Chain", "chain_step"]:
                    return chain_id
            
            # Method 3: Try to get chain object from kwargs (if LangChain passes it)
            if kwargs:
                chain_obj = kwargs.get("chain") or kwargs.get("chain_instance") or kwargs.get("chain_obj")
                if chain_obj:
                    # Extract class name from actual chain object
                    if hasattr(chain_obj, '__class__'):
                        class_name = chain_obj.__class__.__name__
                        if class_name and class_name not in ["Chain", "chain_step"]:
                            return class_name
                    # Or get name attribute if available
                    if hasattr(chain_obj, 'name'):
                        obj_name = chain_obj.name
                        if obj_name and obj_name not in ["chain", "Chain", "chain_step"]:
                            return obj_name
            
            # Method 4: Check metadata for chain_class (set by our patched Chain methods)
            if metadata and isinstance(metadata, dict):
                chain_class = metadata.get('chain_class')
                if chain_class:
                    # Extract class name from full path if needed
                    if "." in chain_class:
                        class_name = chain_class.split(".")[-1]
                    else:
                        class_name = chain_class
                    if class_name and class_name not in ["Chain", "chain_step"]:
                        return class_name
            
            # Method 5: Check serialized for _type or other identifying fields
            if "_type" in serialized:
                type_val = serialized["_type"]
                if type_val and type_val not in ["chain", "Chain", "chain_step"]:
                    return type_val
            
            # If we can't extract anything meaningful, return generic name
            return "chain_step"
        
        # If no trace provided, try to get one from auto-instrumentation
        if not self.trace:
            from .auto_instrument.trace import get_current_trace
            self.trace = get_current_trace()
            
            # If still no trace and we have aigie, try to create one synchronously
            if not self.trace and self.aigie and self.aigie._initialized:
                try:
                    from .auto_instrument.trace import get_or_create_trace_sync
                    chain_name = _get_chain_name(serialized)
                    # Try to create trace synchronously
                    trace = get_or_create_trace_sync(
                        name=chain_name,
                        metadata={"type": "chain", "inputs": inputs}
                    )
                    if trace:
                        self.trace = trace
                except Exception as e:
                    # If sync creation fails, mark for async creation later
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Could not create trace synchronously: {e}")
                    pass
        
        if not self.trace:
            # Still no trace, can't create spans
            return
        
        # Create span for this chain step
        chain_name = _get_chain_name(serialized)
        
        # Extract additional chain information for metadata
        chain_class = None
        chain_type = "chain"  # Default type

        if serialized:
            chain_id = serialized.get("id")
            if isinstance(chain_id, list) and chain_id:
                # Extract full class path
                chain_class = ".".join(str(p) for p in chain_id)
                # Extract class name
                if chain_id:
                    last_part = chain_id[-1]
                    if isinstance(last_part, str) and "." in last_part:
                        chain_class = last_part
                    elif isinstance(last_part, str):
                        chain_class = last_part
            elif isinstance(chain_id, str):
                chain_class = chain_id
            
            # Try to infer chain type from name/class
            chain_name_lower = chain_name.lower()
            chain_class_lower = (chain_class or "").lower()

            # Detect workflow types (LangGraph)
            if "stategraph" in chain_class_lower or "langgraph" in chain_class_lower or \
               "workflow" in chain_name_lower or "graph" in chain_name_lower:
                chain_type = "workflow"
            # Detect agent types
            elif "agent" in chain_name_lower or "agentexecutor" in chain_class_lower or \
                 "react" in chain_class_lower or "openai" in chain_class_lower and "agent" in chain_class_lower:
                chain_type = "agent"
            elif "prompt" in chain_name_lower or "template" in chain_name_lower:
                chain_type = "prompt"
            elif "llm" in chain_name_lower:
                chain_type = "llm"
            elif "sequential" in chain_name_lower:
                chain_type = "sequential"
            elif "router" in chain_name_lower:
                chain_type = "router"
            else:
                chain_type = "chain"
        
        # Use langgraph_node in span name if available for better workflow visualization
        if langgraph_node:
            span_name = f"{langgraph_node} ({chain_name})"
            # If we have a langgraph node, this is part of a workflow
            if chain_type == "chain":
                chain_type = "workflow"
        else:
            span_name = chain_name

        # Get parent span if exists (for proper hierarchy)
        parent_span_id = None
        if parent_run_id and parent_run_id in self._span_contexts:
            parent_span = self._span_contexts[parent_run_id]["span"]
            if hasattr(parent_span, 'id'):
                parent_span_id = parent_span.id

        span = self.trace.span(
            name=span_name,
            type=chain_type,  # Use detected type (workflow, agent, chain, etc.)
            parent=parent_span_id
        )

        # Set enriched metadata including LangGraph info
        if hasattr(span, 'set_metadata'):
            span_metadata = {}
            if chain_class:
                span_metadata['chain_class'] = chain_class
            if chain_type:
                span_metadata['chain_type'] = chain_type
            # Add LangGraph metadata for workflow definition extraction
            if langgraph_node:
                span_metadata['langgraph_node'] = langgraph_node
            if langgraph_step is not None:
                span_metadata['langgraph_step'] = langgraph_step
            if span_metadata:
                span.set_metadata(span_metadata)

        # Track root chain for trace completion
        if parent_run_id is None:
            self._root_run_id = run_id

        # Store span context for this run (including LangGraph info for on_chain_end)
        self._span_contexts[run_id] = {
            "span": span,
            "parent_run_id": parent_run_id,
            "inputs": inputs,
            "entered": False,  # Track if span has been entered
            "entry_failed": False,  # Track if entry failed
            "entry_task": None,  # Store entry task reference if async
            "langgraph_node": langgraph_node,
            "langgraph_step": langgraph_step
        }
        
        # Track execution path for workflow execution data
        self._track_span_start(span, "chain", chain_name)
        
        # Track edge conditions/routing decisions from metadata
        if metadata and isinstance(metadata, dict):
            condition = metadata.get('condition') or metadata.get('edge_condition') or metadata.get('routing_decision')
            if condition:
                self._track_edge_condition(chain_name, condition, metadata.get('condition_result'))
            
            # Track state transitions if present in metadata
            from_state = metadata.get('from_state') or metadata.get('previous_state')
            to_state = metadata.get('to_state') or metadata.get('current_state') or metadata.get('next_state')
            if from_state and to_state:
                self._track_state_transition(from_state, to_state, chain_name, metadata.get('transition_trigger'))
            
            # Track nested workflows if present
            nested_trace_id = metadata.get('nested_trace_id') or metadata.get('sub_trace_id')
            nested_workflow_name = metadata.get('nested_workflow') or metadata.get('sub_workflow')
            if nested_trace_id or nested_workflow_name:
                self._track_nested_workflow(nested_workflow_name or chain_name, nested_trace_id)
        
        # Schedule async span entry (spans must be entered to be persisted)
        self._schedule_span_entry(span, run_id, inputs)
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a chain ends."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            if hasattr(span, 'set_output'):
                span.set_output(outputs)

            # Check if output contains error status (for caught exceptions)
            detected_error = None
            if isinstance(outputs, dict):
                output_status = outputs.get("status")
                if output_status == "error":
                    error_type = outputs.get("error_type", "Error")
                    error_message = outputs.get("error", outputs.get("error_message", "Unknown error"))
                    detected_error = Exception(f"{error_type}: {error_message}")

            # Ensure LangGraph metadata is included in the final span update
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)

                # Add LangGraph metadata from span context
                langgraph_node = span_context.get("langgraph_node")
                langgraph_step = span_context.get("langgraph_step")
                if langgraph_node:
                    enriched_metadata['langgraph_node'] = langgraph_node
                if langgraph_step is not None:
                    enriched_metadata['langgraph_step'] = langgraph_step

                # Add error info to metadata if error detected
                if detected_error:
                    enriched_metadata['error'] = str(detected_error)
                    enriched_metadata['error_type'] = type(detected_error).__name__
                    enriched_metadata['status'] = 'error'
                    enriched_metadata['level'] = 'ERROR'
                    enriched_metadata['status_message'] = str(detected_error)

                span.set_metadata(enriched_metadata)

            # Set agent_type for dashboard grouping
            if hasattr(span, 'set_agent_type'):
                # Use langgraph_node if available, otherwise detect from span type or name
                chain_type = span_context.get("chain_type", "chain")
                langgraph_node = span_context.get("langgraph_node")
                span_name = getattr(span, 'name', '') or ''

                if langgraph_node:
                    span.set_agent_type(langgraph_node)
                elif chain_type == "workflow":
                    span.set_agent_type("workflow")
                elif chain_type == "agent":
                    span.set_agent_type("agent")
                elif "research" in span_name.lower():
                    span.set_agent_type("research_agent")
                elif "search" in span_name.lower():
                    span.set_agent_type("search_agent")
                elif "summarize" in span_name.lower() or "compress" in span_name.lower():
                    span.set_agent_type("summarization_agent")
                else:
                    span.set_agent_type(chain_type)

            # Track execution path end (with detected error if any)
            self._track_span_end(span, "chain", detected_error)

            # Schedule async span exit (completes the span)
            self._schedule_span_exit(span, run_id, detected_error)

            # If this is the root chain, complete the trace and clear context
            if run_id == self._root_run_id:
                self._schedule_trace_completion(detected_error)
                # Clear trace context so next workflow gets a new trace
                from .auto_instrument.trace import clear_current_trace
                clear_current_trace()

            # Clean up
            del self._span_contexts[run_id]
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: list,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM starts."""
        if not self.trace:
            return

        # Extract LangGraph node information from tags and metadata
        langgraph_node = None
        langgraph_step = None
        langgraph_path = None

        # Check metadata first (LangGraph passes node info here)
        if metadata and isinstance(metadata, dict):
            langgraph_node = metadata.get('langgraph_node') or metadata.get('node') or metadata.get('graph_node')
            langgraph_step = metadata.get('langgraph_step') or metadata.get('step')
            langgraph_path = metadata.get('langgraph_path') or metadata.get('path')
            # Also check for checkpoint info
            if not langgraph_node:
                langgraph_node = metadata.get('checkpoint_id') or metadata.get('thread_id')

        # Check tags for LangGraph patterns (e.g., "graph:step:search", "seq:step:1")
        if tags and isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str):
                    # Pattern: "graph:step:<node_name>" or similar
                    if tag.startswith('graph:') or tag.startswith('langgraph:'):
                        parts = tag.split(':')
                        if len(parts) >= 3 and parts[1] == 'step':
                            langgraph_node = langgraph_node or parts[2]
                    # Pattern: "seq:step:<number>"
                    elif tag.startswith('seq:step:'):
                        try:
                            langgraph_step = langgraph_step or int(tag.split(':')[2])
                        except (ValueError, IndexError):
                            pass
                    # Pattern: "node:<name>"
                    elif tag.startswith('node:'):
                        langgraph_node = langgraph_node or tag.split(':', 1)[1]

        # Get parent span if exists
        parent_span_id = None
        if parent_run_id and parent_run_id in self._span_contexts:
            parent_span = self._span_contexts[parent_run_id]["span"]
            if hasattr(parent_span, 'id'):
                parent_span_id = parent_span.id

        # Safely extract model name from serialized (which might be None)
        model_id = None  # Initialize model_id first
        actual_model = None  # The actual model identifier (e.g., "gemini-2.5-flash")

        if not serialized:
            model_name = "LLM Call"
        else:
            name = serialized.get("name")
            if name:
                model_name = name
                # Try to get model_id from serialized even if we have name
                llm_id = serialized.get("id")
                if isinstance(llm_id, list) and llm_id:
                    model_id = ".".join(str(x) for x in llm_id)
                elif llm_id:
                    model_id = str(llm_id)
            else:
                llm_id = serialized.get("id")
                if isinstance(llm_id, list) and llm_id:
                    model_name = llm_id[-1] if len(llm_id) > 1 else llm_id[0]
                    model_id = ".".join(str(x) for x in llm_id)
                elif llm_id:
                    model_name = str(llm_id)
                    model_id = str(llm_id)
                else:
                    model_name = "LLM Call"

            # Try to get actual model from serialized kwargs (for LangChain LLMs)
            serialized_kwargs = serialized.get("kwargs", {})
            if serialized_kwargs:
                # Google Generative AI uses "model"
                actual_model = serialized_kwargs.get("model")
                # OpenAI uses "model_name" or "model"
                if not actual_model:
                    actual_model = serialized_kwargs.get("model_name")
                # Anthropic uses "model"
                if not actual_model:
                    actual_model = serialized_kwargs.get("model")

        # Also check invocation_params for model (some LangChain versions pass it here)
        invocation_params = kwargs.get('invocation_params', {})
        if not actual_model and invocation_params:
            actual_model = invocation_params.get("model") or invocation_params.get("model_name")

        # If we found an actual model, use it for cost calculations instead of class name
        # But keep model_name for display purposes if it's meaningful
        if actual_model:
            # If model_name is just a class name (e.g., "ChatGoogleGenerativeAI"), use actual_model
            if model_name and ("Chat" in model_name or "LLM" in model_name or model_name == "LLM Call"):
                model_name = actual_model
            # Store actual_model for cost calculations
            model_id = actual_model
        
        # Extract prompt content from prompts list
        prompt_contents = []
        system_prompt = None
        if prompts:
            for prompt in prompts:
                if isinstance(prompt, str):
                    prompt_contents.append({"content": prompt, "role": "user"})
                elif hasattr(prompt, 'content'):
                    # LangChain message object
                    role = getattr(prompt, 'type', 'user')
                    if hasattr(prompt, 'content'):
                        content = prompt.content
                        # Separate system prompts
                        if role == 'system' or (isinstance(role, str) and role.lower() == 'system'):
                            system_prompt = content
                        else:
                            prompt_contents.append({
                                "role": role,
                                "content": content
                            })
                elif isinstance(prompt, dict):
                    role = prompt.get("role", "user")
                    content = prompt.get("content", str(prompt))
                    # Separate system prompts
                    if role == 'system' or (isinstance(role, str) and role.lower() == 'system'):
                        system_prompt = content
                    else:
                        prompt_contents.append({
                            "role": role,
                            "content": content
                        })
        
        # Extract LLM parameters from kwargs (LangChain passes invocation_params)
        # Note: invocation_params was already extracted above for model name detection
        llm_params = {}
        if invocation_params:
            # Extract common LLM parameters
            llm_params = {
                "temperature": invocation_params.get("temperature"),
                "top_p": invocation_params.get("top_p"),
                "top_k": invocation_params.get("top_k"),
                "max_tokens": invocation_params.get("max_tokens") or invocation_params.get("max_tokens_to_sample"),
                "frequency_penalty": invocation_params.get("frequency_penalty"),
                "presence_penalty": invocation_params.get("presence_penalty"),
                "stop": invocation_params.get("stop") or invocation_params.get("stop_sequences"),
                "logprobs": invocation_params.get("logprobs"),
                "logit_bias": invocation_params.get("logit_bias"),
            }
            # Remove None values
            llm_params = {k: v for k, v in llm_params.items() if v is not None}
        
        # Also check kwargs directly for parameters (some LangChain versions pass them here)
        if not llm_params:
            llm_params = {
                "temperature": kwargs.get("temperature"),
                "top_p": kwargs.get("top_p"),
                "top_k": kwargs.get("top_k"),
                "max_tokens": kwargs.get("max_tokens") or kwargs.get("max_tokens_to_sample"),
                "frequency_penalty": kwargs.get("frequency_penalty"),
                "presence_penalty": kwargs.get("presence_penalty"),
                "stop": kwargs.get("stop") or kwargs.get("stop_sequences"),
            }
            llm_params = {k: v for k, v in llm_params.items() if v is not None}
        
        # Build structured LLM input data
        llm_input_data = {
            "model": model_name,
            "prompts": prompt_contents if prompt_contents else prompts,
            "prompt_count": len(prompts) if prompts else 0
        }
        if model_id:
            llm_input_data["model_id"] = model_id
        if system_prompt:
            llm_input_data["system_prompt"] = system_prompt
        if llm_params:
            llm_input_data["parameters"] = llm_params

        # Add LangGraph metadata to input data for workflow definition extraction
        if langgraph_node:
            llm_input_data["langgraph_node"] = langgraph_node
        if langgraph_step is not None:
            llm_input_data["langgraph_step"] = langgraph_step
        if langgraph_path:
            llm_input_data["langgraph_path"] = langgraph_path

        # Use langgraph_node in span name if available for better workflow visualization
        # Model name is stored in metadata, no need to duplicate in span name
        if langgraph_node:
            span_name = langgraph_node
        else:
            span_name = f"LLM: {model_name}"

        # Create span for LLM call
        span = self.trace.span(
            name=span_name,
            type="llm",
            parent=parent_span_id
        )

        # Store span context with LLM parameters for later use
        self._span_contexts[run_id] = {
            "span": span,
            "parent_run_id": parent_run_id,
            "prompts": prompts,
            "model_name": model_name,
            "model_id": model_id,
            "llm_params": llm_params,
            "system_prompt": system_prompt,
            "entered": False,
            "completion_start_time": None,  # Will be set when first token received
            "langgraph_node": langgraph_node,
            "langgraph_step": langgraph_step,
        }

        # Track execution path for workflow execution data
        self._track_span_start(span, "llm", span_name)
        
        # Track agent iterations if this is an agent LLM call
        if parent_run_id and parent_run_id in self._span_contexts:
            parent_span = self._span_contexts[parent_run_id]["span"]
            if hasattr(parent_span, 'span_type') and parent_span.span_type == 'agent':
                agent_name = parent_span.name if hasattr(parent_span, 'name') else "Agent"
                self._track_agent_iteration(agent_name)
        
        # Schedule async span entry with structured input
        self._schedule_span_entry(span, run_id, llm_input_data)
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM ends."""
        import logging
        logger = logging.getLogger(__name__)

        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]

            # Extract token usage from LLM response
            token_usage_data = None
            # Get model_name from span_context (stored in on_llm_start) as fallback
            model_name = span_context.get("model_name")
            estimated_cost = 0.0
            
            # Try to get raw response from kwargs (some LLMs pass it here)
            raw_response_obj = kwargs.get("response") or kwargs.get("raw_response")
            if raw_response_obj:
                # Try to extract usage from raw response
                if hasattr(raw_response_obj, 'usage'):
                    usage_obj = raw_response_obj.usage
                    if usage_obj:
                        token_usage_data = {
                            "prompt_tokens": getattr(usage_obj, 'prompt_tokens', 0),
                            "completion_tokens": getattr(usage_obj, 'completion_tokens', 0),
                            "total_tokens": getattr(usage_obj, 'total_tokens', 0)
                        }
                elif isinstance(raw_response_obj, dict) and "usage" in raw_response_obj:
                    token_usage_data = raw_response_obj["usage"]
            
            # Try multiple locations for token usage
            
            if hasattr(response, 'llm_output') and response.llm_output:
                # Debug: log the entire llm_output to see what's available
                logger.debug(f"LLM output keys: {list(response.llm_output.keys()) if isinstance(response.llm_output, dict) else 'not a dict'}")
                logger.debug(f"LLM output: {response.llm_output}")
                
                # Try standard token_usage field
                token_usage_data = response.llm_output.get("token_usage")
                # Only update model_name if we got a non-empty one from llm_output
                llm_output_model = response.llm_output.get("model_name")
                if llm_output_model:
                    model_name = llm_output_model
                
                # Try alternative locations for token usage
                if not token_usage_data:
                    token_usage_data = response.llm_output.get("usage")
                
                # Extract from nested structures
                if not token_usage_data and "metadata" in response.llm_output:
                    token_usage_data = response.llm_output["metadata"].get("token_usage")
                
                # Try to extract from response_metadata
                if not token_usage_data and "response_metadata" in response.llm_output:
                    response_metadata = response.llm_output["response_metadata"]
                    if isinstance(response_metadata, dict):
                        token_usage_data = response_metadata.get("token_usage") or response_metadata.get("usage")
                
                # Try to get raw response object if available (some LLMs store it)
                if not token_usage_data and "raw" in response.llm_output:
                    raw_response = response.llm_output["raw"]
                    # Try to extract from raw response object
                    if hasattr(raw_response, 'usage'):
                        usage_obj = raw_response.usage
                        if usage_obj:
                            token_usage_data = {
                                "prompt_tokens": getattr(usage_obj, 'prompt_tokens', 0),
                                "completion_tokens": getattr(usage_obj, 'completion_tokens', 0),
                                "total_tokens": getattr(usage_obj, 'total_tokens', 0)
                            }
                    elif isinstance(raw_response, dict) and "usage" in raw_response:
                        usage_dict = raw_response["usage"]
                        if isinstance(usage_dict, dict):
                            token_usage_data = usage_dict
                        elif hasattr(usage_dict, 'prompt_tokens'):
                            token_usage_data = {
                                "prompt_tokens": getattr(usage_dict, 'prompt_tokens', 0),
                                "completion_tokens": getattr(usage_dict, 'completion_tokens', 0),
                                "total_tokens": getattr(usage_dict, 'total_tokens', 0)
                            }
            
            # Fallback: Try to extract from response object directly (for some providers)
            if not token_usage_data and hasattr(response, 'response_metadata'):
                response_metadata = response.response_metadata
                if isinstance(response_metadata, dict):
                    token_usage_data = response_metadata.get("token_usage") or response_metadata.get("usage")
            
            # Fallback: Try to extract from generations (some providers store it there)
            if not token_usage_data and hasattr(response, 'generations') and response.generations:
                for gen_list in response.generations:
                    if gen_list:
                        for gen in gen_list:
                            # Check generation_info first
                            if hasattr(gen, 'generation_info') and gen.generation_info:
                                token_usage_data = gen.generation_info.get("token_usage") or gen.generation_info.get("usage")
                                if token_usage_data:
                                    break

                            # Check message.usage_metadata (Gemini returns tokens here!)
                            if hasattr(gen, 'message') and hasattr(gen.message, 'usage_metadata'):
                                usage_meta = gen.message.usage_metadata
                                if usage_meta:
                                    # Handle dict format
                                    if isinstance(usage_meta, dict):
                                        token_usage_data = {
                                            "prompt_tokens": usage_meta.get("input_tokens", 0),
                                            "completion_tokens": usage_meta.get("output_tokens", 0),
                                            "total_tokens": usage_meta.get("total_tokens", 0)
                                        }
                                    # Handle object format
                                    elif hasattr(usage_meta, 'input_tokens'):
                                        token_usage_data = {
                                            "prompt_tokens": getattr(usage_meta, 'input_tokens', 0),
                                            "completion_tokens": getattr(usage_meta, 'output_tokens', 0),
                                            "total_tokens": getattr(usage_meta, 'total_tokens', 0)
                                        }
                                    if token_usage_data:
                                        logger.debug(f"Extracted token usage from message.usage_metadata: {token_usage_data}")
                                        break
                        if token_usage_data:
                            break
            
            # Ensure token_usage_data is a dict
            if token_usage_data and not isinstance(token_usage_data, dict):
                # If it's a Usage object, convert to dict
                if hasattr(token_usage_data, '__dict__'):
                    token_usage_data = token_usage_data.__dict__
                elif hasattr(token_usage_data, 'prompt_tokens'):
                    token_usage_data = {
                        "prompt_tokens": getattr(token_usage_data, 'prompt_tokens', 0),
                        "completion_tokens": getattr(token_usage_data, 'completion_tokens', 0),
                        "total_tokens": getattr(token_usage_data, 'total_tokens', 0)
                    }
                else:
                    token_usage_data = {}
            
            if not token_usage_data:
                token_usage_data = {}
            
            # Calculate cost if we have token usage
            input_cost = 0.0
            output_cost = 0.0
            pricing_tier = None
            
            # Check if we actually have token usage data (not just empty dict)
            has_token_usage = (
                token_usage_data and 
                isinstance(token_usage_data, dict) and
                (token_usage_data.get("prompt_tokens") or 
                 token_usage_data.get("input_tokens") or
                 token_usage_data.get("completion_tokens") or
                 token_usage_data.get("output_tokens") or
                 token_usage_data.get("total_tokens"))
            )
            
            if has_token_usage:
                    try:
                        from .cost_tracking import extract_usage_from_response, calculate_cost, get_model_pricing
                        # Extract token counts
                        input_tokens = token_usage_data.get("prompt_tokens") or token_usage_data.get("input_tokens", 0)
                        output_tokens = token_usage_data.get("completion_tokens") or token_usage_data.get("output_tokens", 0)
                        total_tokens = token_usage_data.get("total_tokens", input_tokens + output_tokens)
                        
                        # Create usage dict for cost calculation
                        usage_dict = {
                            "prompt_tokens": input_tokens,
                            "completion_tokens": output_tokens,
                            "total_tokens": total_tokens
                        }
                        
                        # Calculate cost with breakdown
                        if model_name:
                            # Try to get pricing info for tier
                            pricing_info = get_model_pricing(model_name)
                            if pricing_info:
                                pricing_tier = f"{pricing_info.provider}:{model_name}"
                            
                            # Calculate cost breakdown
                            from .cost_tracking import UsageMetadata
                            usage_metadata = UsageMetadata(
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                total_tokens=total_tokens,
                                model=model_name
                            )
                            cost_breakdown = calculate_cost(usage_metadata, model_name)
                            if cost_breakdown:
                                estimated_cost = float(cost_breakdown.total_cost)
                                input_cost = float(cost_breakdown.input_cost)
                                output_cost = float(cost_breakdown.output_cost)
                    except Exception as e:
                        logger.warning(f"Failed to calculate cost for LLM span: {e}", exc_info=True)
            
            # Debug logging to help diagnose token extraction issues
            if not has_token_usage:
                logger.debug(
                    f"No token usage found in LLM response for span {span.name if hasattr(span, 'name') else 'unknown'}. "
                    f"llm_output keys: {list(response.llm_output.keys()) if (hasattr(response, 'llm_output') and response.llm_output and isinstance(response.llm_output, dict)) else 'N/A'}. "
                    f"Attempting token estimation..."
                )
                # Estimate tokens from prompt and response content
                # Average: ~4 characters per token for English text
                try:
                    prompt_text = ""
                    if run_id in self._span_contexts:
                        input_data = span_context.get("input_data", {})
                        if isinstance(input_data, dict):
                            # Try to get prompt from various locations
                            prompt_text = str(input_data.get("prompt", ""))
                            if not prompt_text and "messages" in input_data:
                                prompt_text = str(input_data.get("messages", ""))
                            if not prompt_text and "prompts" in input_data:
                                prompt_text = str(input_data.get("prompts", ""))
                        elif isinstance(input_data, str):
                            prompt_text = input_data

                    # Get response text from generations
                    response_text = ""
                    if hasattr(response, 'generations') and response.generations:
                        for gen_list in response.generations:
                            for gen in gen_list:
                                if hasattr(gen, 'text'):
                                    response_text += gen.text
                                elif hasattr(gen, 'message') and hasattr(gen.message, 'content'):
                                    response_text += str(gen.message.content)

                    # Estimate tokens (average 4 chars per token)
                    estimated_prompt_tokens = len(prompt_text) // 4 if prompt_text else 0
                    estimated_completion_tokens = len(response_text) // 4 if response_text else 0
                    estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens

                    if estimated_total_tokens > 0:
                        token_usage_data = {
                            "prompt_tokens": estimated_prompt_tokens,
                            "completion_tokens": estimated_completion_tokens,
                            "total_tokens": estimated_total_tokens,
                            "estimated": True  # Mark as estimated
                        }
                        has_token_usage = True
                        logger.debug(f"Estimated tokens for span: prompt={estimated_prompt_tokens}, completion={estimated_completion_tokens}")
                except Exception as e:
                    logger.debug(f"Failed to estimate tokens: {e}")
            else:
                logger.debug(f"Found token usage for span {span.name if hasattr(span, 'name') else 'unknown'}: prompt={token_usage_data.get('prompt_tokens', 0)}, completion={token_usage_data.get('completion_tokens', 0)}, total={token_usage_data.get('total_tokens', 0)}")
            
            # Extract response content from generations
            response_contents = []
            tool_calls = []
            finish_reasons = []
            model_name_from_context = span_context.get("model_name", "LLM")
            
            if hasattr(response, 'generations') and response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        finish_reason = None
                        if hasattr(gen, 'text'):
                            response_contents.append({
                                "content": gen.text,
                                "type": "text"
                            })
                            # Try to get finish reason from generation
                            if hasattr(gen, 'generation_info') and isinstance(gen.generation_info, dict):
                                finish_reason = gen.generation_info.get('finish_reason') or gen.generation_info.get('finishReason')
                        elif hasattr(gen, 'message'):
                            msg = gen.message
                            if hasattr(msg, 'content'):
                                resp_obj = {
                                    "content": msg.content,
                                    "type": getattr(msg, 'type', 'ai')
                                }
                                # Extract tool calls if present
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    resp_obj["tool_calls"] = msg.tool_calls
                                    tool_calls.extend(msg.tool_calls)
                                    finish_reason = "tool_calls"
                                # Extract finish reason if available
                                if hasattr(msg, 'response_metadata') and isinstance(msg.response_metadata, dict):
                                    finish_reason = msg.response_metadata.get('finish_reason') or msg.response_metadata.get('finishReason')
                                response_contents.append(resp_obj)
                        elif isinstance(gen, dict):
                            response_contents.append({
                                "content": gen.get('text', str(gen)),
                                "type": "text"
                            })
                            finish_reason = gen.get('finish_reason') or gen.get('finishReason')
                        else:
                            response_contents.append({
                                "content": str(gen),
                                "type": "unknown"
                            })
                        
                        if finish_reason:
                            finish_reasons.append(finish_reason)
            
            # Extract response metadata from llm_output
            response_metadata = {}
            request_id = None
            response_id = None
            model_version = None
            system_fingerprint = None
            completion_start_time = None
            
            if hasattr(response, 'llm_output') and response.llm_output:
                # Extract request_id and model_version from llm_output metadata
                if isinstance(response.llm_output, dict):
                    metadata = response.llm_output.get("metadata", {})
                    if isinstance(metadata, dict):
                        request_id = metadata.get("request_id") or metadata.get("id") or metadata.get("requestId")
                        model_version = metadata.get("model_version") or metadata.get("modelVersion") or metadata.get("model")
                        # Extract system fingerprint (OpenAI)
                        system_fingerprint = metadata.get("system_fingerprint")
                        if system_fingerprint:
                            response_metadata["system_fingerprint"] = system_fingerprint
                        # Extract response ID (Anthropic)
                        response_id = metadata.get("response_id") or metadata.get("id")
                        if response_id:
                            response_metadata["response_id"] = response_id
                        # Extract completion start time (when LLM started generating)
                        completion_start_time = metadata.get("completion_start_time") or metadata.get("completionStartTime")
                
                # Also check top-level llm_output for these fields
                if not request_id:
                    request_id = response.llm_output.get("request_id") or response.llm_output.get("id")
                if not model_version:
                    model_version = response.llm_output.get("model_version") or response.llm_output.get("model")
                if not system_fingerprint:
                    system_fingerprint = response.llm_output.get("system_fingerprint")
                if not response_id:
                    response_id = response.llm_output.get("response_id")
                if not completion_start_time:
                    completion_start_time = response.llm_output.get("completion_start_time") or response.llm_output.get("completionStartTime")
            
            # Also check response object directly (for direct API calls)
            if hasattr(response, 'system_fingerprint') and not system_fingerprint:
                system_fingerprint = response.system_fingerprint
                response_metadata["system_fingerprint"] = system_fingerprint
            if hasattr(response, 'id') and not response_id:
                # For Anthropic, response.id is the response_id
                if model_name and 'claude' in model_name.lower():
                    response_id = response.id
                    response_metadata["response_id"] = response_id
            
            # Build structured output data
            output_data = {
                "model": model_name or model_name_from_context,
                "response": response_contents[0]["content"] if response_contents else None,
                "responses": response_contents,
                "generations_count": len(response.generations) if hasattr(response, 'generations') else 0,
                "status": "success"
            }
            
            # Add response metadata
            if finish_reasons:
                output_data["finish_reasons"] = finish_reasons
                output_data["finish_reason"] = finish_reasons[0]  # Primary finish reason
            if request_id:
                output_data["request_id"] = request_id
            if model_version:
                output_data["model_version"] = model_version
            if response_metadata:
                output_data["response_metadata"] = response_metadata
            
            if has_token_usage:
                output_data["token_usage"] = token_usage_data
                # Calculate token totals
                if isinstance(token_usage_data, dict):
                    total_tokens = token_usage_data.get('total_tokens') or (
                        (token_usage_data.get('prompt_tokens') or 0) + 
                        (token_usage_data.get('completion_tokens') or 0)
                    )
                    output_data["total_tokens"] = total_tokens
                    output_data["prompt_tokens"] = token_usage_data.get('prompt_tokens')
                    output_data["completion_tokens"] = token_usage_data.get('completion_tokens')
            
            if estimated_cost > 0:
                output_data["estimated_cost"] = estimated_cost
            if input_cost > 0:
                output_data["input_cost"] = input_cost
            if output_cost > 0:
                output_data["output_cost"] = output_cost
            if completion_start_time:
                output_data["completion_start_time"] = completion_start_time
            
            if tool_calls:
                output_data["tool_calls"] = tool_calls
            
            if hasattr(span, 'set_output'):
                span.set_output(output_data)
            
            # Extract token counts for direct field storage
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            if has_token_usage:
                prompt_tokens = token_usage_data.get("prompt_tokens") or token_usage_data.get("input_tokens", 0) or 0
                completion_tokens = token_usage_data.get("completion_tokens") or token_usage_data.get("output_tokens", 0) or 0
                total_tokens = token_usage_data.get("total_tokens") or (prompt_tokens + completion_tokens)
            
            # Store comprehensive metadata in span for aggregation and analysis
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)
                
                # Token usage (also store in metadata for backward compatibility)
                if has_token_usage:
                    enriched_metadata['token_usage'] = {
                        'prompt_tokens': prompt_tokens,  # Backend expects prompt_tokens, not input_tokens
                        'completion_tokens': completion_tokens,  # Backend expects completion_tokens, not output_tokens
                        'input_tokens': prompt_tokens,  # Keep for backward compatibility
                        'output_tokens': completion_tokens,  # Keep for backward compatibility
                        'total_tokens': total_tokens,
                        'estimated_cost': estimated_cost,
                        'input_cost': input_cost,
                        'output_cost': output_cost
                    }
                
                # Store token counts as direct fields in metadata (will be extracted to direct columns by backend)
                # Always store these fields, even if 0, so backend can see them
                enriched_metadata['prompt_tokens'] = prompt_tokens
                enriched_metadata['completion_tokens'] = completion_tokens
                enriched_metadata['total_tokens'] = total_tokens
                enriched_metadata['input_cost'] = input_cost
                enriched_metadata['output_cost'] = output_cost
                enriched_metadata['total_cost'] = estimated_cost
                
                # Model information (store as direct fields)
                if model_name:
                    enriched_metadata['model'] = model_name
                    enriched_metadata['model_name'] = model_name  # Backward compatibility
                # Get model_id from span context (stored in on_llm_start)
                model_id = span_context.get("model_id")
                if model_id:
                    enriched_metadata['model_id'] = model_id
                if model_version:
                    enriched_metadata['model_version'] = model_version
                if pricing_tier:
                    enriched_metadata['pricing_tier'] = pricing_tier
                
                # LLM parameters (store as model_parameters)
                llm_params = span_context.get("llm_params", {})
                if llm_params:
                    enriched_metadata['model_parameters'] = llm_params
                    enriched_metadata['llm_parameters'] = llm_params  # Backward compatibility
                
                # System prompt
                system_prompt = span_context.get("system_prompt")
                if system_prompt:
                    enriched_metadata['system_prompt'] = system_prompt
                
                # Response metadata
                if finish_reasons:
                    enriched_metadata['finish_reason'] = finish_reasons[0]
                if request_id:
                    enriched_metadata['request_id'] = request_id
                if response_id:
                    enriched_metadata['response_id'] = response_id
                if system_fingerprint:
                    enriched_metadata['system_fingerprint'] = system_fingerprint
                if completion_start_time:
                    enriched_metadata['completion_start_time'] = completion_start_time
                    # Also store in span context for later use
                    span_context['completion_start_time'] = completion_start_time
                if response_metadata:
                    enriched_metadata.update(response_metadata)

                # Retry count tracking
                if self.trace and hasattr(self.trace, 'id') and self.trace.id:
                    trace_id = self.trace.id
                    span_name = span_context.get("model_name") or "LLM"
                    if trace_id in self._retry_info:
                        retries_for_span = [r for r in self._retry_info[trace_id] if r.get('span_name') == span_name]
                        retry_count = len(retries_for_span)
                        if retry_count > 0:
                            enriched_metadata['retry_count'] = retry_count

                # Add LangGraph metadata for workflow definition extraction
                langgraph_node = span_context.get("langgraph_node")
                langgraph_step = span_context.get("langgraph_step")
                if langgraph_node:
                    enriched_metadata['langgraph_node'] = langgraph_node
                if langgraph_step is not None:
                    enriched_metadata['langgraph_step'] = langgraph_step

                span.set_metadata(enriched_metadata)

            # Set direct fields on span object (will be included in __aexit__ update)
            # This is more reliable than separate API calls
            if hasattr(span, 'set_model') and (model_name or model_name_from_context):
                span.set_model(model_name or model_name_from_context)

            if hasattr(span, 'set_usage') and has_token_usage:
                span.set_usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    total_cost=estimated_cost
                )

            # Set model parameters (temperature, top_p, etc.)
            if hasattr(span, 'set_model_parameters'):
                model_params = span_context.get('invocation_params', {})
                if model_params:
                    # Extract common model parameters
                    params_to_send = {}
                    for key in ['temperature', 'top_p', 'top_k', 'max_tokens', 'max_output_tokens',
                                'stop', 'stop_sequences', 'presence_penalty', 'frequency_penalty']:
                        if key in model_params:
                            params_to_send[key] = model_params[key]
                    if params_to_send:
                        span.set_model_parameters(params_to_send)

            # Set agent_type for dashboard grouping
            if hasattr(span, 'set_agent_type'):
                span.set_agent_type("llm")

            # Track execution path end
            self._track_span_end(span, "llm", None)
            
            # Schedule async span exit
            self._schedule_span_exit(span, run_id, None)
            
            # Clean up
            del self._span_contexts[run_id]
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts.

        Extracts tool information from LangChain's serialized dict. The serialized
        dict contains all the information LangChain has about the tool, including:
        - name: Tool name
        - id: Tool class path (array or string)
        - description: Tool description
        - func/function: Function object for function-based tools
        """
        if not self.trace:
            return
        
        # Get parent span if exists
        # Try to get parent span ID, but also store parent_run_id for later resolution
        parent_span_id = None
        if parent_run_id and parent_run_id in self._span_contexts:
            parent_span = self._span_contexts[parent_run_id]["span"]
            if hasattr(parent_span, 'id') and parent_span.id:
                parent_span_id = parent_span.id
            # If parent span doesn't have ID yet, we'll resolve it when parent span is entered
            # Store parent_run_id in span context for later resolution
        
        # Extract comprehensive tool information from LangChain's serialized dict
        if not serialized:
            tool_name = "Tool"
            tool_description = None
            tool_id = None
            tool_class = None
            tool_type = None
            func_name = None
            tool_version = None
            tool_return_type = None
            tool_args_schema = None
        else:
            # Extract tool name (primary identifier)
            tool_name = serialized.get("name", "Tool")
            
            # Extract tool ID (can be array like ["langchain", "tools", "tool", "Tool"] or string)
            tool_id = serialized.get("id")
            tool_class = None
            if tool_id:
                if isinstance(tool_id, list) and tool_id:
                    # Extract class name from class path (e.g., ["langchain", "tools", "tool", "Tool"] -> "Tool")
                    tool_class = ".".join(str(x) for x in tool_id)
                    # Extract class name from path
                    if tool_id:
                        last_part = tool_id[-1]
                        if isinstance(last_part, str):
                            # Handle cases like "langchain.tools.tool.Tool" or just "Tool"
                            if "." in last_part:
                                tool_class = last_part
                                tool_name_from_class = last_part.split(".")[-1]
                            else:
                                tool_class = ".".join(str(x) for x in tool_id)
                                tool_name_from_class = str(last_part)
                            # Use class name if name is generic
                            if tool_name == "Tool" or not tool_name:
                                tool_name = tool_name_from_class
                elif isinstance(tool_id, str):
                    tool_class = tool_id
                    # Extract class name from string path
                    if "." in tool_id:
                        tool_name_from_class = tool_id.split(".")[-1]
                        if tool_name == "Tool" or not tool_name:
                            tool_name = tool_name_from_class
            
            # Extract tool description
            tool_description = serialized.get("description")
            
            # Determine tool type from class/id
            tool_type = None
            if tool_class:
                tool_class_lower = tool_class.lower()
                if "function" in tool_class_lower or "func" in tool_class_lower:
                    tool_type = "function"
                elif "structured" in tool_class_lower:
                    tool_type = "structured_tool"
                elif "tool" in tool_class_lower:
                    tool_type = "tool"
                else:
                    tool_type = "custom"
            
            # Extract function name if available (for function-based tools)
            # LangChain stores the actual function object in serialized["func"] or serialized["function"]
            func_name = None
            func_obj = serialized.get("func") or serialized.get("function")
            if func_obj:
                if hasattr(func_obj, '__name__'):
                    # Extract function name from function object (e.g., search_database, calculate_total)
                    func_name = func_obj.__name__
                elif isinstance(func_obj, str):
                    func_name = func_obj
                elif callable(func_obj):
                    # Try to get name from callable
                    func_name = getattr(func_obj, '__name__', None) or getattr(func_obj, '__qualname__', None)
            
            # Also check kwargs for tool object (some LangChain versions pass it directly)
            if not func_name and kwargs:
                tool_obj = kwargs.get("tool") or kwargs.get("tool_instance")
                if tool_obj:
                    # Try to get function from tool object
                    if hasattr(tool_obj, 'func'):
                        func_obj_from_tool = tool_obj.func
                        if hasattr(func_obj_from_tool, '__name__'):
                            func_name = func_obj_from_tool.__name__
                    # Or get name directly from tool
                    elif hasattr(tool_obj, 'name'):
                        if not tool_name or tool_name == "Tool":
                            tool_name = tool_obj.name
            
            # Extract additional metadata
            tool_version = serialized.get("version")
            tool_return_type = serialized.get("return_type")
            tool_args_schema = serialized.get("args_schema")
        
        # Parse tool input - try to parse as JSON if it looks like JSON
        parsed_input = input_str
        try:
            import json
            # Try to parse as JSON
            if isinstance(input_str, str) and (input_str.strip().startswith('{') or input_str.strip().startswith('[')):
                parsed_input = json.loads(input_str)
        except (json.JSONDecodeError, ValueError):
            # If parsing fails, keep as string but try to extract structured data
            parsed_input = input_str
        
        # Build comprehensive tool input data structure
        tool_input_data = {
            "tool_name": tool_name,
            "input": parsed_input
        }
        
        # Add all extracted tool metadata
        if tool_description:
            tool_input_data["description"] = tool_description
        if tool_id:
            tool_input_data["tool_id"] = tool_id
        if tool_class:
            tool_input_data["tool_class"] = tool_class
        if tool_type:
            tool_input_data["tool_type"] = tool_type
        if func_name:
            tool_input_data["function_name"] = func_name
        if tool_version:
            tool_input_data["tool_version"] = tool_version
        if tool_return_type:
            tool_input_data["return_type"] = tool_return_type
        
        # Extract tool arguments if input is a dict
        if isinstance(parsed_input, dict):
            tool_input_data["parameters"] = parsed_input
        elif isinstance(parsed_input, str):
            tool_input_data["raw_input"] = parsed_input
        
        # Store full serialized config for reference
        tool_input_data["serialized"] = serialized
        
        # Create span with tool name extracted from LangChain serialized data
        # Use function name if available, otherwise use tool name
        span_display_name = func_name if func_name else tool_name
        span = self.trace.span(
            name=f"Tool: {span_display_name}",
            type="tool",
            parent=parent_span_id
        )
        
        # Store comprehensive span context
        # Store span context with start time for execution time calculation
        import time
        from datetime import datetime
        start_time = datetime.utcnow()
        
        self._span_contexts[run_id] = {
            "span": span,
            "parent_run_id": parent_run_id,
            "parent_span_id": parent_span_id,  # Store for later use
            "input": input_str,
            "tool_name": tool_name,
            "function_name": func_name,
            "tool_class": tool_class,
            "tool_type": tool_type,
            "start_time": start_time,
            "entered": False
        }
        
        # If parent span doesn't have ID yet, try to resolve it when parent is entered
        if parent_run_id and not parent_span_id and parent_run_id in self._span_contexts:
            # Store reference to this span so parent can update it when it gets an ID
            parent_context = self._span_contexts[parent_run_id]
            if "child_spans" not in parent_context:
                parent_context["child_spans"] = []
            parent_context["child_spans"].append(run_id)
        
        # Set metadata on span for better tracking
        if hasattr(span, 'set_metadata'):
            span_metadata = {
                "tool_name": tool_name,
                "tool_type": tool_type or "tool"
            }
            if func_name:
                span_metadata["function_name"] = func_name
            if tool_class:
                span_metadata["tool_class"] = tool_class
            if tool_description:
                span_metadata["description"] = tool_description
            span.set_metadata(span_metadata)
        
        # Track execution path for workflow execution data
        self._track_span_start(span, "tool", f"Tool: {span_display_name}")
        
        # Schedule async span entry with structured input
        self._schedule_span_entry(span, run_id, tool_input_data)
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a tool ends."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            tool_name = span_context.get("tool_name", "Tool")
            
            # Parse tool output - try to parse as JSON if it looks like JSON
            parsed_output = output
            try:
                import json
                if isinstance(output, str) and (output.strip().startswith('{') or output.strip().startswith('[')):
                    parsed_output = json.loads(output)
            except (json.JSONDecodeError, ValueError):
                parsed_output = output
            
            # Calculate execution time if we have start time
            execution_time_ms = None
            if run_id in self._span_contexts:
                start_time = span_context.get("start_time")
                if start_time:
                    import time
                    from datetime import datetime
                    if isinstance(start_time, datetime):
                        execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    elif isinstance(start_time, float):
                        execution_time_ms = (time.time() - start_time) * 1000
            
            # Build structured output data
            tool_output_data = {
                "tool_name": tool_name,
                "output": parsed_output,
                "status": "success"
            }
            
            # If output is a dict, include it as structured data
            if isinstance(parsed_output, dict):
                tool_output_data["result"] = parsed_output
            elif isinstance(parsed_output, str):
                tool_output_data["raw_output"] = parsed_output
            
            if execution_time_ms is not None:
                tool_output_data["execution_time_ms"] = execution_time_ms
            
            if hasattr(span, 'set_output'):
                span.set_output(tool_output_data)
            
            # Store enhanced metadata
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)
                enriched_metadata['tool'] = {
                    'tool_name': tool_name,
                    'tool_type': span_context.get("tool_type", "tool"),
                }
                if span_context.get("tool_class"):
                    enriched_metadata['tool']['tool_class'] = span_context["tool_class"]
                if span_context.get("function_name"):
                    enriched_metadata['tool']['function_name'] = span_context["function_name"]
                if execution_time_ms is not None:
                    enriched_metadata['tool']['execution_time_ms'] = execution_time_ms
                span.set_metadata(enriched_metadata)

            # Set agent_type for dashboard grouping
            if hasattr(span, 'set_agent_type'):
                span.set_agent_type("tool")

            # Set latency for tools
            if hasattr(span, 'set_latency') and execution_time_ms is not None:
                span.set_latency(execution_time_ms / 1000)  # Convert to seconds

            # Track execution path end
            self._track_span_end(span, "tool", None)

            # Schedule async span exit
            self._schedule_span_exit(span, run_id, None)

            # Clean up
            del self._span_contexts[run_id]

    def on_chain_error(
        self,
        error: Exception,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a chain errors."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            if hasattr(span, 'set_output'):
                span.set_output({
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "status": "error"
                })

            # Set level and statusMessage for error using span methods
            if hasattr(span, 'set_level'):
                span.set_level("ERROR", str(error))

            # Also store in metadata for backward compatibility
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)
                enriched_metadata['level'] = 'ERROR'
                enriched_metadata['status_message'] = str(error)
                enriched_metadata['error_type'] = type(error).__name__
                span.set_metadata(enriched_metadata)

            # Track execution path end with error
            self._track_span_end(span, "chain", error)

            # Schedule async span exit with error
            self._schedule_span_exit(span, run_id, error)

            # If this is the root chain, complete the trace with error
            if run_id == self._root_run_id:
                self._schedule_trace_completion(error)

            del self._span_contexts[run_id]
    
    def on_llm_error(
        self,
        error: Exception,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM errors."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            if hasattr(span, 'set_output'):
                span.set_output({
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "status": "error"
                })

            # Set level and statusMessage for error using span methods
            if hasattr(span, 'set_level'):
                span.set_level("ERROR", str(error))

            # Also store in metadata for backward compatibility
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)
                enriched_metadata['level'] = 'ERROR'
                enriched_metadata['status_message'] = str(error)
                enriched_metadata['error_type'] = type(error).__name__
                span.set_metadata(enriched_metadata)

            # Track execution path end with error
            self._track_span_end(span, "llm", error)

            # Schedule async span exit with error
            self._schedule_span_exit(span, run_id, error)

            del self._span_contexts[run_id]
    
    def on_tool_error(
        self,
        error: Exception,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a tool errors."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            if hasattr(span, 'set_output'):
                span.set_output({
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "status": "error"
                })

            # Set level and statusMessage for error using span methods
            if hasattr(span, 'set_level'):
                span.set_level("ERROR", str(error))

            # Also store in metadata for backward compatibility
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)
                enriched_metadata['level'] = 'ERROR'
                enriched_metadata['status_message'] = str(error)
                enriched_metadata['error_type'] = type(error).__name__
                span.set_metadata(enriched_metadata)

            # Track execution path end with error
            self._track_span_end(span, "tool", error)

            # Schedule async span exit with error
            self._schedule_span_exit(span, run_id, error)

            del self._span_contexts[run_id]
    
    def on_retriever_start(
        self,
        serialized: Dict[str, Any],
        query: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever starts (LangChain retrieval)."""
        if not self.trace:
            return
        
        # Get parent span if exists
        parent_span_id = None
        if parent_run_id and parent_run_id in self._span_contexts:
            parent_span = self._span_contexts[parent_run_id]["span"]
            if hasattr(parent_span, 'id'):
                parent_span_id = parent_span.id
        
        # Extract retriever information
        retriever_name = "Retriever"
        retriever_type = "retriever"
        if serialized:
            retriever_name = serialized.get("name", "Retriever")
            retriever_id = serialized.get("id")
            if isinstance(retriever_id, list) and retriever_id:
                retriever_name = retriever_id[-1] if retriever_id else "Retriever"
                # Determine retriever type from class path
                if "vectorstore" in str(retriever_id).lower():
                    retriever_type = "vectorstore"
                elif "embedding" in str(retriever_id).lower():
                    retriever_type = "embedding"
        
        # Build retrieval input data
        retrieval_input = {
            "query": query,
            "retriever_name": retriever_name,
            "retriever_type": retriever_type
        }
        
        # Extract additional parameters
        if kwargs:
            top_k = kwargs.get("k") or kwargs.get("top_k")
            if top_k:
                retrieval_input["top_k"] = top_k
        
        # Create span for retrieval
        span = self.trace.span(
            name=f"Retriever: {retriever_name}",
            type="retriever",
            parent=parent_span_id
        )
        
        # Store span context
        self._span_contexts[run_id] = {
            "span": span,
            "parent_run_id": parent_run_id,
            "query": query,
            "retriever_name": retriever_name,
            "start_time": None,  # Will be set on entry
            "entered": False
        }
        
        # Track execution path for workflow execution data
        self._track_span_start(span, "retriever", f"Retriever: {retriever_name}")
        
        # Schedule async span entry
        self._schedule_span_entry(span, run_id, retrieval_input)
    
    def on_retriever_end(
        self,
        documents: list,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever ends."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            
            # Extract retrieved documents with metadata
            retrieved_docs = []
            for doc in documents:
                doc_data = {
                    "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                }
                # Extract metadata
                if hasattr(doc, 'metadata') and doc.metadata:
                    doc_data["metadata"] = doc.metadata
                    # Extract similarity score if available
                    if isinstance(doc.metadata, dict):
                        score = doc.metadata.get("score") or doc.metadata.get("similarity_score") or doc.metadata.get("relevance_score")
                        if score is not None:
                            doc_data["score"] = float(score)
                elif isinstance(doc, dict):
                    doc_data["content"] = doc.get("page_content") or doc.get("content") or str(doc)
                    doc_data["metadata"] = doc.get("metadata", {})
                    if "score" in doc:
                        doc_data["score"] = float(doc["score"])
                
                retrieved_docs.append(doc_data)
            
            # Build structured output data
            output_data = {
                "retrieved_documents": retrieved_docs,
                "document_count": len(retrieved_docs),
                "status": "success"
            }
            
            # Extract query embedding info if available
            if kwargs and "query_embedding" in kwargs:
                output_data["query_embedding_dim"] = len(kwargs["query_embedding"]) if isinstance(kwargs["query_embedding"], list) else None
            
            if hasattr(span, 'set_output'):
                span.set_output(output_data)
            
            # Store in metadata for analysis
            if hasattr(span, 'set_metadata'):
                current_metadata = getattr(span, '_metadata', {})
                enriched_metadata = dict(current_metadata)
                enriched_metadata['retrieval'] = {
                    'document_count': len(retrieved_docs),
                    'retriever_name': span_context.get("retriever_name", "Retriever"),
                }
                # Store average similarity score if available
                scores = [doc.get("score") for doc in retrieved_docs if doc.get("score") is not None]
                if scores:
                    enriched_metadata['retrieval']['avg_score'] = sum(scores) / len(scores)
                    enriched_metadata['retrieval']['min_score'] = min(scores)
                    enriched_metadata['retrieval']['max_score'] = max(scores)
                span.set_metadata(enriched_metadata)
            
            # Schedule async span exit
            self._schedule_span_exit(span, run_id, None)
            
            # Clean up
            del self._span_contexts[run_id]
    
    def on_retriever_error(
        self,
        error: Exception,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever errors."""
        if run_id in self._span_contexts:
            span_context = self._span_contexts[run_id]
            span = span_context["span"]
            if hasattr(span, 'set_output'):
                span.set_output({
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "status": "error"
                })
            
            # Schedule async span exit with error
            self._schedule_span_exit(span, run_id, error)
            
            del self._span_contexts[run_id]
    
    def _track_span_start(self, span: Any, span_type: str, span_name: str) -> None:
        """Track span start for execution path tracking."""
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            return
        
        trace_id = self.trace.id
        from datetime import datetime
        
        # Initialize tracking structures for this trace if needed
        if trace_id not in self._execution_paths:
            self._execution_paths[trace_id] = []
            self._execution_timing[trace_id] = {}
            self._execution_status[trace_id] = {}
            self._execution_errors[trace_id] = {}
            self._edge_conditions[trace_id] = []
            self._agent_iterations[trace_id] = {}
            self._span_start_times[trace_id] = {}
            self._retry_info[trace_id] = []
            self._state_transitions[trace_id] = []
            self._nested_workflows[trace_id] = []
        
        # Track agent, chain, tool, llm, and retriever spans in execution path
        if span_type in ['agent', 'chain', 'tool', 'llm', 'retriever']:
            if span_name and span_name not in self._execution_paths[trace_id]:
                self._execution_paths[trace_id].append(span_name)
            
            # Record start time - use actual span start time if available, otherwise use current time
            if span_name:
                start_time = datetime.utcnow().isoformat()
                # Try to get actual span start time if span has been entered
                # Note: We'll update this when span is actually entered with real timestamp
                self._span_start_times[trace_id][span_name] = start_time
                
                self._execution_timing[trace_id][span_name] = {
                    'start_time': start_time,
                    'end_time': None,
                    'duration_ms': 0
                }
                self._execution_status[trace_id][span_name] = 'running'
    
    def _track_span_end(self, span: Any, span_type: str, error: Optional[Exception] = None) -> None:
        """Track span end for execution path tracking."""
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            return
        
        trace_id = self.trace.id
        if trace_id not in self._execution_paths:
            return
        
        # Get span name
        span_name = None
        if hasattr(span, 'name'):
            span_name = span.name
        elif hasattr(span, '_name'):
            span_name = span._name
        
        if not span_name:
            return
        
        # Track agent, chain, tool, llm, and retriever spans
        if span_type in ['agent', 'chain', 'tool', 'llm', 'retriever'] and span_name in self._execution_timing.get(trace_id, {}):
            from datetime import datetime
            
            # Get actual end time - try to get from span if available, otherwise use current time
            end_time = datetime.utcnow().isoformat()
            # Note: We'll update this when span actually exits with real timestamp
            
            # Record end time and calculate duration
            timing = self._execution_timing[trace_id][span_name]
            timing['end_time'] = end_time
            
            if timing.get('start_time'):
                try:
                    start_dt = datetime.fromisoformat(timing['start_time'].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
                    timing['duration_ms'] = duration_ms
                except Exception:
                    pass
            
            # Update status
            if error:
                self._execution_status[trace_id][span_name] = 'failed'
                self._execution_errors[trace_id][span_name] = str(error)
                
                # Track retry information if this is a retry
                # Check if this span was retried by looking at metadata or previous attempts
                if trace_id in self._retry_info:
                    # Check if this span name appears in retry info (indicating a previous retry)
                    existing_retries = [r for r in self._retry_info[trace_id] if r.get('span_name') == span_name]
                    attempt_number = len(existing_retries) + 1
                    if attempt_number > 1:
                        from datetime import datetime
                        self._retry_info[trace_id].append({
                            'span_name': span_name,
                            'attempt': attempt_number,
                            'reason': str(error),
                            'timestamp': datetime.utcnow().isoformat()
                        })
            else:
                self._execution_status[trace_id][span_name] = 'completed'
    
    def _track_edge_condition(self, step_name: str, condition: Any, result: Any = None) -> None:
        """Track edge condition/routing decision."""
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            return
        
        trace_id = self.trace.id
        if trace_id not in self._edge_conditions:
            self._edge_conditions[trace_id] = []
        
        self._edge_conditions[trace_id].append({
            'step': step_name,
            'condition': str(condition),
            'result': str(result) if result is not None else None
        })
    
    def _track_agent_iteration(self, agent_name: str) -> None:
        """Track agent iteration count."""
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            return
        
        trace_id = self.trace.id
        if trace_id not in self._agent_iterations:
            self._agent_iterations[trace_id] = {}
        
        if agent_name not in self._agent_iterations[trace_id]:
            self._agent_iterations[trace_id][agent_name] = 0
        
        self._agent_iterations[trace_id][agent_name] += 1
    
    def _track_state_transition(self, from_state: str, to_state: str, trigger: Optional[str] = None, transition_trigger: Optional[str] = None) -> None:
        """Track state transition in stateful workflows."""
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            return
        
        trace_id = self.trace.id
        if trace_id not in self._state_transitions:
            self._state_transitions[trace_id] = []
        
        from datetime import datetime
        self._state_transitions[trace_id].append({
            'from_state': str(from_state),
            'to_state': str(to_state),
            'trigger': str(transition_trigger or trigger or 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def _track_nested_workflow(self, workflow_name: str, nested_trace_id: Optional[str] = None) -> None:
        """Track nested workflow execution."""
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            return
        
        trace_id = self.trace.id
        if trace_id not in self._nested_workflows:
            self._nested_workflows[trace_id] = []
        
        from datetime import datetime
        self._nested_workflows[trace_id].append({
            'workflow_name': workflow_name,
            'nested_trace_id': nested_trace_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_execution_data(self) -> Optional[Dict[str, Any]]:
        """Get execution data for the current trace."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.trace or not hasattr(self.trace, 'id') or not self.trace.id:
            logger.debug("No trace available for execution data")
            return None
        
        trace_id = self.trace.id
        if trace_id not in self._execution_paths:
            logger.debug(f"No execution paths tracked for trace {trace_id}")
            return None
        
        try:
            execution_data = {
                'execution_path': self._execution_paths.get(trace_id, []),
                'execution_timing': self._execution_timing.get(trace_id, {}),
                'execution_status': self._execution_status.get(trace_id, {}),
                'execution_errors': self._execution_errors.get(trace_id, {})
            }
            
            # Validate execution data
            if not execution_data['execution_path']:
                logger.debug(f"Empty execution path for trace {trace_id}")
                # Still return data even if empty - let backend decide
            
            # Add edge conditions if available
            if trace_id in self._edge_conditions and self._edge_conditions[trace_id]:
                execution_data['edge_conditions'] = self._edge_conditions[trace_id]
            
            # Add agent iterations if available
            if trace_id in self._agent_iterations and self._agent_iterations[trace_id]:
                execution_data['agent_iterations'] = self._agent_iterations[trace_id]
            
            # Add retry information if available
            if trace_id in self._retry_info and self._retry_info[trace_id]:
                execution_data['retry_info'] = self._retry_info[trace_id]
            
            # Add state transitions if available
            if trace_id in self._state_transitions and self._state_transitions[trace_id]:
                execution_data['state_transitions'] = self._state_transitions[trace_id]
            
            # Add nested workflows if available
            if trace_id in self._nested_workflows and self._nested_workflows[trace_id]:
                execution_data['nested_workflows'] = self._nested_workflows[trace_id]
            
            # Validate timing data consistency
            for span_name in execution_data['execution_path']:
                if span_name in execution_data['execution_timing']:
                    timing = execution_data['execution_timing'][span_name]
                    if 'start_time' not in timing:
                        logger.warning(f"Missing start_time for span {span_name} in trace {trace_id}")
                    # end_time may be missing if span is still running
            
            logger.debug(f"Retrieved execution data for trace {trace_id}: {len(execution_data.get('execution_path', []))} steps")
            return execution_data
            
        except Exception as e:
            logger.error(f"Error getting execution data for trace {trace_id}: {e}", exc_info=True)
            # Return minimal data on error
            return {
                'execution_path': self._execution_paths.get(trace_id, []),
                'execution_timing': {},
                'execution_status': {},
                'execution_errors': {}
            }
    
    def _schedule_span_entry(self, span: Any, run_id: str, input_data: Dict[str, Any]) -> None:
        """Schedule async span entry from sync callback."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Try to get running event loop
            loop = asyncio.get_running_loop()
            # Schedule span entry as a task and store it for potential waiting
            task = loop.create_task(self._enter_span(span, run_id, input_data))
            # Store task reference so we can check if it completed
            if run_id in self._span_contexts:
                self._span_contexts[run_id]["entry_task"] = task
        except RuntimeError:
            # No event loop running, create one
            # This is a fallback - ideally we should have a running loop
            try:
                asyncio.run(self._enter_span(span, run_id, input_data))
            except RuntimeError:
                # Event loop already running in another thread, use thread-safe approach
                import threading
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(self._enter_span(span, run_id, input_data))
                        new_loop.close()
                    except Exception as e:
                        logger.error(f"Failed to enter span {run_id} in thread: {e}", exc_info=True)
                        # Mark span as failed so we don't try to exit it
                        if run_id in self._span_contexts:
                            self._span_contexts[run_id]["entry_failed"] = True
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
        except Exception as e:
            logger.error(f"Failed to schedule span entry for {run_id}: {e}", exc_info=True)
            # Mark span as failed so we don't try to exit it
            if run_id in self._span_contexts:
                self._span_contexts[run_id]["entry_failed"] = True
    
    async def _enter_span(self, span: Any, run_id: str, input_data: Dict[str, Any]) -> None:
        """Enter span asynchronously and set input."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Set input BEFORE entering span so it's included in creation payload
            if hasattr(span, 'set_input') and input_data:
                span.set_input(input_data)
            elif not input_data:
                # If no input data, at least set empty dict to ensure span has some data
                if hasattr(span, 'set_input'):
                    span.set_input({})
            
            # Enter the span (this creates it in the backend with input data)
            await span.__aenter__()
            
            # Verify span was created successfully (has an ID)
            if not hasattr(span, 'id') or not span.id:
                raise RuntimeError(f"Span entry failed - no ID assigned for run_id {run_id}")
            
            # Mark as entered
            if run_id in self._span_contexts:
                self._span_contexts[run_id]["entered"] = True
                self._span_contexts[run_id]["entry_failed"] = False
                # Store actual entry time
                from datetime import datetime
                self._span_contexts[run_id]["actual_start_time"] = datetime.utcnow().isoformat()
                
                # Update child spans that were waiting for this parent's ID
                if "child_spans" in self._span_contexts[run_id]:
                    parent_span_id = span.id
                    for child_run_id in self._span_contexts[run_id]["child_spans"]:
                        if child_run_id in self._span_contexts:
                            child_context = self._span_contexts[child_run_id]
                            child_span = child_context.get("span")
                            if child_span and hasattr(child_span, 'parent_id'):
                                # Update parent_id on child span
                                child_span.parent_id = parent_span_id
                                # Update in context
                                child_context["parent_span_id"] = parent_span_id
                                # If child span is already entered, send an update to backend
                                if child_context.get("entered") and hasattr(child_span, 'id') and child_span.id:
                                    try:
                                        # Send update to set parent_id
                                        if hasattr(self.trace, 'client') and hasattr(self.trace, 'api_url'):
                                            await self.trace.client.put(
                                                f"{self.trace.api_url}/v1/spans/{child_span.id}",
                                                json={"parent_id": parent_span_id},
                                                timeout=5.0
                                            )
                                    except Exception as e:
                                        logger.warning(f"Failed to update parent_id for child span {child_span.id}: {e}")
            
            # Update execution timing with actual span entry time
            if hasattr(span, 'name') and self.trace and hasattr(self.trace, 'id') and self.trace.id:
                trace_id = self.trace.id
                span_name = span.name
                if trace_id in self._execution_timing and span_name in self._execution_timing[trace_id]:
                    from datetime import datetime
                    actual_start = datetime.utcnow().isoformat()
                    self._execution_timing[trace_id][span_name]['start_time'] = actual_start
                    if trace_id in self._span_start_times:
                        self._span_start_times[trace_id][span_name] = actual_start
            
            # Update input immediately after creation to ensure it's persisted
            if hasattr(span, 'update_input') and input_data and span.id:
                try:
                    await span.update_input(input_data)
                except Exception as update_error:
                    # If update fails, log but don't fail - input was already in creation payload
                    logger.debug(f"Input update failed for span {span.id}, but creation succeeded: {update_error}")
        except Exception as e:
            logger.error(f"Failed to enter span {run_id}: {e}", exc_info=True)
            # Mark span as failed so we don't try to exit it
            if run_id in self._span_contexts:
                self._span_contexts[run_id]["entered"] = False
                self._span_contexts[run_id]["entry_failed"] = True
    
    def _schedule_span_field_update(self, span: Any, update_data: Dict[str, Any]) -> None:
        """Schedule async span field update from sync callback."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._update_span_fields(span, update_data))
        except RuntimeError:
            try:
                asyncio.run(self._update_span_fields(span, update_data))
            except RuntimeError:
                import threading
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(self._update_span_fields(span, update_data))
                        new_loop.close()
                    except Exception as e:
                        logger.error(f"Failed to update span fields in thread: {e}", exc_info=True)
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
        except Exception as e:
            logger.error(f"Failed to schedule span field update: {e}", exc_info=True)
    
    async def _update_span_fields(self, span: Any, update_data: Dict[str, Any]) -> None:
        """Update span fields asynchronously."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if not hasattr(span, 'id') or not span.id:
                logger.warning("Span has no ID, cannot update fields")
                return
            
            # Get API client from trace
            if not self.trace or not hasattr(self.trace, 'client'):
                logger.warning("No trace or client available for span field update")
                return
            
            # Update span via API
            response = await self.trace.client.put(
                f"{self.trace.api_url}/v1/spans/{span.id}",
                json=update_data,
                timeout=5.0
            )
            response.raise_for_status()
        except Exception as e:
            logger.debug(f"Failed to update span fields: {e}")
            # Don't raise - this is a best-effort update
    
    def _schedule_span_exit(self, span: Any, run_id: str, error: Optional[Exception] = None) -> None:
        """Schedule async span exit from sync callback."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if span entry failed - if so, don't try to exit
        if run_id in self._span_contexts:
            if self._span_contexts[run_id].get("entry_failed"):
                logger.warning(f"Skipping exit for span {run_id} - entry failed")
                return
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._exit_span(span, run_id, error))
        except RuntimeError:
            try:
                asyncio.run(self._exit_span(span, run_id, error))
            except RuntimeError:
                import threading
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(self._exit_span(span, run_id, error))
                        new_loop.close()
                    except Exception as e:
                        logger.error(f"Failed to exit span {run_id} in thread: {e}", exc_info=True)
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
        except Exception as e:
            logger.error(f"Failed to schedule span exit for {run_id}: {e}", exc_info=True)
    
    async def _exit_span(self, span: Any, run_id: str, error: Optional[Exception] = None) -> None:
        """Exit span asynchronously (completes the span)."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Wait for entry task to complete if it exists
            if run_id in self._span_contexts:
                entry_task = self._span_contexts[run_id].get("entry_task")
                if entry_task and not entry_task.done():
                    try:
                        await asyncio.wait_for(entry_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Span entry task timed out for {run_id}")
                    except Exception as entry_error:
                        logger.warning(f"Span entry task failed for {run_id}: {entry_error}")
                        # If entry failed, don't try to exit
                        return
            
            # Double-check entry status
            if run_id in self._span_contexts:
                if self._span_contexts[run_id].get("entry_failed"):
                    logger.warning(f"Skipping exit for span {run_id} - entry failed")
                    return
                
                if not self._span_contexts[run_id].get("entered"):
                    logger.warning(f"Span {run_id} was never entered, attempting entry now...")
                    # Try to enter it now with empty input if we have no data
                    try:
                        await span.__aenter__()
                        self._span_contexts[run_id]["entered"] = True
                    except Exception as entry_error:
                        logger.error(f"Failed to enter span {run_id} during exit: {entry_error}")
                        return
            
            # Verify span has an ID before trying to exit
            if not hasattr(span, 'id') or not span.id:
                logger.warning(f"Span {run_id} has no ID, cannot exit")
                return
            
            # Update execution timing with actual span exit time before exiting
            if hasattr(span, 'name') and self.trace and hasattr(self.trace, 'id') and self.trace.id:
                trace_id = self.trace.id
                span_name = span.name
                if trace_id in self._execution_timing and span_name in self._execution_timing[trace_id]:
                    from datetime import datetime
                    actual_end = datetime.utcnow().isoformat()
                    timing = self._execution_timing[trace_id][span_name]
                    timing['end_time'] = actual_end
                    
                    # Recalculate duration with actual timestamps
                    if timing.get('start_time'):
                        try:
                            start_dt = datetime.fromisoformat(timing['start_time'].replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(actual_end.replace('Z', '+00:00'))
                            duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
                            timing['duration_ms'] = duration_ms
                        except Exception:
                            pass
            
            # Exit the span (this updates it in the backend with end_time, input, output)
            await span.__aexit__(type(error) if error else None, error, None)
        except Exception as e:
            logger.error(f"Failed to exit span {run_id}: {e}", exc_info=True)
    
    def _schedule_trace_completion(self, error: Optional[Exception] = None) -> None:
        """Schedule async trace completion from sync callback."""
        if not self.trace:
            return
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._complete_trace(error))
        except RuntimeError:
            try:
                asyncio.run(self._complete_trace(error))
            except RuntimeError:
                import threading
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(self._complete_trace(error))
                        new_loop.close()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to complete trace: {e}")
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
    
    async def _complete_trace(self, error: Optional[Exception] = None) -> None:
        """Complete the trace asynchronously."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if self.trace:
                # Get execution data from callback handler and pass to trace
                execution_data = self.get_execution_data()
                if execution_data:
                    self.trace.set_callback_execution_data(execution_data)
                    logger.debug(f"Set execution data for trace {self.trace.id if hasattr(self.trace, 'id') else 'unknown'}")
                else:
                    logger.debug(f"No execution data available for trace completion")
                
                # Exit the trace (this sets end_time and finalizes status)
                await self.trace.__aexit__(
                    type(error) if error else None,
                    error,
                    None
                )
                logger.debug(f"Trace completion finished")
        except Exception as e:
            logger.error(f"Failed to complete trace: {e}", exc_info=True)
            # Try to ensure trace is marked as failed even if completion fails
            try:
                if self.trace and hasattr(self.trace, 'complete'):
                    await self.trace.complete(status="failure", error=e)
            except Exception:
                pass


