"""
LLM client auto-instrumentation.

Automatically patches OpenAI, Anthropic, and Gemini clients to create spans
and track token usage, costs, and latency.
"""

import functools
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_patched_modules = set()


def patch_all_llms() -> None:
    """Patch all available LLM clients."""
    _patch_openai()
    _patch_anthropic()
    _patch_gemini()
    _patch_langchain_llms()


def _patch_openai() -> None:
    """Patch OpenAI client for auto-instrumentation."""
    try:
        import openai
        
        if 'openai' in _patched_modules:
            return
        
        # Patch OpenAI client class
        if hasattr(openai, 'OpenAI'):
            _patch_openai_client(openai.OpenAI)
        
        # Patch AsyncOpenAI
        if hasattr(openai, 'AsyncOpenAI'):
            _patch_openai_client(openai.AsyncOpenAI, is_async=True)
        
        _patched_modules.add('openai')
        logger.debug("Patched OpenAI client for auto-instrumentation")
        
    except ImportError:
        pass  # OpenAI not installed
    except Exception as e:
        logger.warning(f"Failed to patch OpenAI: {e}")


def _patch_openai_client(client_class: Any, is_async: bool = False) -> None:
    """Patch OpenAI client by wrapping instances after creation."""
    original_init = client_class.__init__
    original_getattribute = getattr(client_class, '__getattribute__', object.__getattribute__)
    
    @functools.wraps(original_init)
    def traced_init(self, *args, **kwargs):
        """Init that creates wrapper and stores it."""
        original_init(self, *args, **kwargs)
        
        from ..client import get_aigie
        from ..wrappers import wrap_openai
        
        aigie = get_aigie()
        if aigie and aigie._initialized:
            # Create wrapper and store reference
            wrapped = wrap_openai(self, aigie_client=aigie)
            # Store wrapper on instance using object.__setattr__ to avoid recursion
            object.__setattr__(self, '_aigie_wrapper', wrapped)
    
    client_class.__init__ = traced_init
    
    # Patch __getattribute__ to intercept 'chat' access
    def traced_getattribute(self, name):
        # Special handling for 'chat' when we have a wrapper
        if name == 'chat':
            # Check if wrapper exists (using object.__getattribute__ to avoid recursion)
            try:
                wrapper = object.__getattribute__(self, '_aigie_wrapper')
                if wrapper:
                    return wrapper.chat
            except AttributeError:
                # No wrapper yet, fall through to original behavior
                pass
        
        # For all other attributes, use original behavior
        # But avoid accessing _aigie_wrapper through normal path to prevent recursion
        if name == '_aigie_wrapper':
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                return None
        
        return original_getattribute(self, name)
    
    client_class.__getattribute__ = traced_getattribute


def _patch_anthropic() -> None:
    """Patch Anthropic client for auto-instrumentation."""
    try:
        import anthropic
        
        if 'anthropic' in _patched_modules:
            return
        
        # Patch Anthropic client
        if hasattr(anthropic, 'Anthropic'):
            _patch_anthropic_client(anthropic.Anthropic)
        
        # Patch AsyncAnthropic
        if hasattr(anthropic, 'AsyncAnthropic'):
            _patch_anthropic_client(anthropic.AsyncAnthropic, is_async=True)
        
        _patched_modules.add('anthropic')
        logger.debug("Patched Anthropic client for auto-instrumentation")
        
    except ImportError:
        pass  # Anthropic not installed
    except Exception as e:
        logger.warning(f"Failed to patch Anthropic: {e}")


def _patch_anthropic_client(client_class: Any, is_async: bool = False) -> None:
    """Patch Anthropic client by wrapping instances after creation."""
    original_init = client_class.__init__
    
    @functools.wraps(original_init)
    def traced_init(self, *args, **kwargs):
        """Init that creates wrapper and stores it."""
        original_init(self, *args, **kwargs)
        
        from ..client import get_aigie
        from ..wrappers import wrap_anthropic
        
        aigie = get_aigie()
        if aigie and aigie._initialized:
            wrapped = wrap_anthropic(self, aigie_client=aigie)
            object.__setattr__(self, '_aigie_wrapper', wrapped)
    
    client_class.__init__ = traced_init
    
    # Patch __getattribute__ to intercept 'messages' access
    original_getattribute = getattr(client_class, '__getattribute__', object.__getattribute__)
    
    def traced_getattribute(self, name):
        # Special handling for 'messages' when we have a wrapper
        if name == 'messages':
            try:
                wrapper = object.__getattribute__(self, '_aigie_wrapper')
                if wrapper:
                    return wrapper.messages
            except AttributeError:
                # No wrapper yet, fall through to original behavior
                pass
        
        # Avoid recursion for _aigie_wrapper
        if name == '_aigie_wrapper':
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                return None
        
        return original_getattribute(self, name)
    
    client_class.__getattribute__ = traced_getattribute


def _patch_gemini() -> None:
    """Patch Google Gemini client for auto-instrumentation."""
    try:
        import google.generativeai as genai
        
        if 'gemini' in _patched_modules:
            return
        
        # Patch generate_content method directly
        if hasattr(genai, 'GenerativeModel'):
            original_generate_content = genai.GenerativeModel.generate_content
            
            @functools.wraps(original_generate_content)
            def traced_generate_content(self, *args, **kwargs):
                """Traced version of generate_content."""
                from ..client import get_aigie
                from ..wrappers import wrap_gemini
                
                aigie = get_aigie()
                if aigie and aigie._initialized:
                    wrapped = wrap_gemini(self, aigie_client=aigie)
                    return wrapped.generate_content(*args, **kwargs)
                
                # No aigie, call original
                return original_generate_content(self, *args, **kwargs)
            
            genai.GenerativeModel.generate_content = traced_generate_content
        
        _patched_modules.add('gemini')
        logger.debug("Patched Gemini client for auto-instrumentation")
        
    except ImportError:
        pass  # Gemini not installed
    except Exception as e:
        logger.warning(f"Failed to patch Gemini: {e}")


def _trace_llm_call(
    provider: str,
    original_func: Any,
    *args,
    **kwargs
) -> Any:
    """
    Trace an LLM call by creating a span and tracking metrics.
    
    Args:
        provider: LLM provider name ('openai', 'anthropic', 'gemini')
        original_func: Original LLM function to call
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        LLM response
    """
    from ..client import get_aigie
    from ..auto_instrument.trace import get_or_create_trace
    from ..cost_tracking import extract_and_calculate_cost
    import time
    
    import asyncio
    
    aigie = get_aigie()
    if not aigie or not aigie._initialized:
        # No instrumentation, call original function
        if asyncio.iscoroutinefunction(original_func):
            return asyncio.run(original_func(*args, **kwargs))
        return original_func(*args, **kwargs)
    
    # Get or create trace (handle both sync and async)
    if asyncio.iscoroutinefunction(original_func):
        # Async function - use async trace creation
        async def _async_trace():
            trace = await get_or_create_trace(
                name=f"LLM Call: {provider}",
                metadata={"provider": provider, "type": "llm"}
            )
            
            if not trace:
                return await original_func(*args, **kwargs)
            
            model = kwargs.get('model') or kwargs.get('model_name') or 'unknown'
            
            async with trace.span(f"LLM: {provider} - {model}", type="llm") as span:
                return await _execute_llm_call(span, original_func, provider, model, *args, **kwargs)
        
        return asyncio.run(_async_trace())
    else:
        # Sync function - use sync trace creation
        trace = asyncio.run(get_or_create_trace(
            name=f"LLM Call: {provider}",
            metadata={"provider": provider, "type": "llm"}
        ))
        
        if not trace:
            return original_func(*args, **kwargs)
        
        model = kwargs.get('model') or kwargs.get('model_name') or 'unknown'
        
        # For sync, we need to handle span differently
        span_ctx = trace.span(f"LLM: {provider} - {model}", type="llm")
        return _execute_llm_call_sync(span_ctx, original_func, provider, model, *args, **kwargs)


async def _execute_llm_call(
    span: Any,
    original_func: Any,
    provider: str,
    model: str,
    *args,
    **kwargs
) -> Any:
    # Extract LLM parameters
    llm_params = {
        "temperature": kwargs.get("temperature"),
        "top_p": kwargs.get("top_p"),
        "top_k": kwargs.get("top_k"),
        "max_tokens": kwargs.get("max_tokens") or kwargs.get("max_tokens_to_sample"),
        "frequency_penalty": kwargs.get("frequency_penalty"),
        "presence_penalty": kwargs.get("presence_penalty"),
        "stop": kwargs.get("stop") or kwargs.get("stop_sequences"),
        "logprobs": kwargs.get("logprobs"),
        "logit_bias": kwargs.get("logit_bias"),
    }
    llm_params = {k: v for k, v in llm_params.items() if v is not None}
    
    # Extract messages and separate system prompts
    messages = kwargs.get("messages", [])
    system_prompt = None
    user_messages = []
    if messages:
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    system_prompt = content
                else:
                    user_messages.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                if msg.role == "system":
                    system_prompt = msg.content
                else:
                    user_messages.append({"role": msg.role, "content": msg.content})
    
    # Build input data
    input_data = {
        "provider": provider,
        "model": model,
    }
    if llm_params:
        input_data["parameters"] = llm_params
    if system_prompt:
        input_data["system_prompt"] = system_prompt
    if user_messages:
        input_data["messages"] = user_messages
    else:
        # Fallback to truncated kwargs if no messages
        input_data["kwargs"] = {k: str(v)[:200] for k, v in kwargs.items() if k not in ['api_key', 'temperature', 'top_p', 'max_tokens']}
    
    span.set_input(input_data)
    
    import time
    start_time = time.time()
    
    try:
        # Call original function (it's async)
        response = await original_func(*args, **kwargs)
        
        latency = time.time() - start_time
        
        # Extract token usage and cost
        usage = None
        cost_data = None
        
        if hasattr(response, 'usage'):
            usage = response.usage
        elif isinstance(response, dict) and 'usage' in response:
            usage = response['usage']
        
        if usage:
            from ..cost_tracking import extract_and_calculate_cost
            cost_data = extract_and_calculate_cost(model=model, usage=usage)
        
        # Extract response metadata
        finish_reason = None
        request_id = None
        model_version = model
        response_metadata = {}
        
        if hasattr(response, 'choices') and response.choices:
            # OpenAI format
            choice = response.choices[0]
            content = choice.message.content if hasattr(choice.message, 'content') else None
            finish_reason = getattr(choice, 'finish_reason', None)
            # Extract request_id and system_fingerprint
            if hasattr(response, 'id'):
                request_id = response.id
            if hasattr(response, 'system_fingerprint'):
                response_metadata['system_fingerprint'] = response.system_fingerprint
            if hasattr(response, 'model'):
                model_version = response.model
        elif hasattr(response, 'content'):
            # Anthropic/Gemini format
            content = response.content
            if hasattr(response, 'stop_reason'):
                finish_reason = response.stop_reason
            if hasattr(response, 'id'):
                request_id = response.id
            if hasattr(response, 'model'):
                model_version = response.model
        elif isinstance(response, dict):
            content = response.get('content', str(response))[:500]
            finish_reason = response.get('finish_reason') or response.get('stop_reason')
            request_id = response.get('id') or response.get('request_id')
            model_version = response.get('model', model)
        else:
            content = str(response)[:500]
        
        # Set output
        output = {
            "latency": latency,
            "model": model,
            "provider": provider
        }
        
        if usage:
            output["usage"] = usage
        if cost_data:
            output["cost"] = cost_data.get("total_cost", 0)
        if content:
            output["content"] = content[:500]  # Truncate
        if finish_reason:
            output["finish_reason"] = finish_reason
        if request_id:
            output["request_id"] = request_id
        if model_version != model:
            output["model_version"] = model_version
        if response_metadata:
            output["response_metadata"] = response_metadata
        
        span.set_output(output)
        
        # Store in metadata for aggregation
        if hasattr(span, 'set_metadata'):
            current_metadata = getattr(span, '_metadata', {})
            enriched_metadata = dict(current_metadata)
            enriched_metadata['llm_parameters'] = llm_params
            if system_prompt:
                enriched_metadata['system_prompt'] = system_prompt
            if finish_reason:
                enriched_metadata['finish_reason'] = finish_reason
            if request_id:
                enriched_metadata['request_id'] = request_id
            if model_version:
                enriched_metadata['model_version'] = model_version
            if usage:
                enriched_metadata['token_usage'] = {
                    'input_tokens': getattr(usage, 'prompt_tokens', usage.get('prompt_tokens', 0) if isinstance(usage, dict) else 0),
                    'output_tokens': getattr(usage, 'completion_tokens', usage.get('completion_tokens', 0) if isinstance(usage, dict) else 0),
                    'total_tokens': getattr(usage, 'total_tokens', usage.get('total_tokens', 0) if isinstance(usage, dict) else 0),
                }
            span.set_metadata(enriched_metadata)
        
        return response
        
    except Exception as e:
        latency = time.time() - start_time
        
        span.set_output({
            "error": str(e),
            "error_type": type(e).__name__,
            "latency": latency,
            "status": "error"
        })
        
        raise


def _execute_llm_call_sync(
    span_ctx: Any,
    original_func: Any,
    provider: str,
    model: str,
    *args,
    **kwargs
) -> Any:
    """Execute LLM call synchronously with tracing."""
    import time
    from ..cost_tracking import extract_and_calculate_cost
    
    # Extract LLM parameters (same as async version)
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
    
    # Extract messages and separate system prompts
    messages = kwargs.get("messages", [])
    system_prompt = None
    user_messages = []
    if messages:
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    system_prompt = content
                else:
                    user_messages.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                if msg.role == "system":
                    system_prompt = msg.content
                else:
                    user_messages.append({"role": msg.role, "content": msg.content})
    
    # Build input data
    input_data = {
        "provider": provider,
        "model": model,
    }
    if llm_params:
        input_data["parameters"] = llm_params
    if system_prompt:
        input_data["system_prompt"] = system_prompt
    if user_messages:
        input_data["messages"] = user_messages
    else:
        input_data["kwargs"] = {k: str(v)[:200] for k, v in kwargs.items() if k not in ['api_key', 'temperature', 'top_p', 'max_tokens']}
    
    span_ctx.set_input(input_data)
    
    start_time = time.time()
    
    try:
        response = original_func(*args, **kwargs)
        latency = time.time() - start_time
        
        # Extract token usage and cost
        usage = None
        cost_data = None
        
        if hasattr(response, 'usage'):
            usage = response.usage
        elif isinstance(response, dict) and 'usage' in response:
            usage = response['usage']
        
        if usage:
            cost_data = extract_and_calculate_cost(model=model, usage=usage)
        
        # Extract response metadata (same as async version)
        finish_reason = None
        request_id = None
        model_version = model
        response_metadata = {}
        
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            content = choice.message.content if hasattr(choice.message, 'content') else None
            finish_reason = getattr(choice, 'finish_reason', None)
            if hasattr(response, 'id'):
                request_id = response.id
            if hasattr(response, 'system_fingerprint'):
                response_metadata['system_fingerprint'] = response.system_fingerprint
            if hasattr(response, 'model'):
                model_version = response.model
        elif hasattr(response, 'content'):
            content = response.content
            if hasattr(response, 'stop_reason'):
                finish_reason = response.stop_reason
            if hasattr(response, 'id'):
                request_id = response.id
            if hasattr(response, 'model'):
                model_version = response.model
        elif isinstance(response, dict):
            content = response.get('content', str(response))[:500]
            finish_reason = response.get('finish_reason') or response.get('stop_reason')
            request_id = response.get('id') or response.get('request_id')
            model_version = response.get('model', model)
        else:
            content = str(response)[:500]
        
        output = {
            "latency": latency,
            "model": model,
            "provider": provider
        }
        
        if usage:
            output["usage"] = usage
        if cost_data:
            output["cost"] = cost_data.get("total_cost", 0)
        if content:
            output["content"] = content[:500]
        if finish_reason:
            output["finish_reason"] = finish_reason
        if request_id:
            output["request_id"] = request_id
        if model_version != model:
            output["model_version"] = model_version
        if response_metadata:
            output["response_metadata"] = response_metadata
        
        span_ctx.set_output(output)
        
        # Store in metadata
        if hasattr(span_ctx, 'set_metadata'):
            current_metadata = getattr(span_ctx, '_metadata', {})
            enriched_metadata = dict(current_metadata)
            enriched_metadata['llm_parameters'] = llm_params
            if system_prompt:
                enriched_metadata['system_prompt'] = system_prompt
            if finish_reason:
                enriched_metadata['finish_reason'] = finish_reason
            if request_id:
                enriched_metadata['request_id'] = request_id
            if model_version:
                enriched_metadata['model_version'] = model_version
            span_ctx.set_metadata(enriched_metadata)
        
        return response
        
    except Exception as e:
        latency = time.time() - start_time
        
        span_ctx.set_output({
            "error": str(e),
            "error_type": type(e).__name__,
            "latency": latency,
            "status": "error"
        })
        
        raise


# Import asyncio at module level
import asyncio
import time


def _patch_langchain_llms() -> None:
    """Patch LangChain LLM classes to auto-inject callbacks."""
    try:
        # Patch ChatOpenAI
        try:
            from langchain_openai import ChatOpenAI
            
            if ChatOpenAI not in _patched_modules:
                _patch_langchain_llm_class(ChatOpenAI, "openai")
                _patched_modules.add(ChatOpenAI)
        except ImportError:
            pass
        
        # Patch ChatAnthropic
        try:
            from langchain_anthropic import ChatAnthropic
            
            if ChatAnthropic not in _patched_modules:
                _patch_langchain_llm_class(ChatAnthropic, "anthropic")
                _patched_modules.add(ChatAnthropic)
        except ImportError:
            pass
        
        # Patch ChatGoogleGenerativeAI
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            if ChatGoogleGenerativeAI not in _patched_modules:
                _patch_langchain_llm_class(ChatGoogleGenerativeAI, "gemini")
                _patched_modules.add(ChatGoogleGenerativeAI)
        except ImportError:
            pass
        
        logger.debug("Patched LangChain LLM classes for auto-instrumentation")
        
    except Exception as e:
        logger.warning(f"Failed to patch LangChain LLMs: {e}")


def _patch_langchain_llm_class(llm_class: Any, provider: str) -> None:
    """Patch a LangChain LLM class to auto-inject callbacks and interception hooks.

    This provides full auto-instrumentation:
    1. Pre-call interception (blocking, validation)
    2. Tracing (spans, metrics)
    3. Post-call interception (quality checks, recommendations)
    """
    original_ainvoke = getattr(llm_class, 'ainvoke', None)
    original_invoke = getattr(llm_class, 'invoke', None)

    def _convert_messages_to_dict(messages) -> list:
        """Convert LangChain messages to dict format for interception."""
        messages_dict = []
        for msg in messages:
            if hasattr(msg, 'type'):
                role = msg.type
            elif hasattr(msg, '__class__'):
                role = msg.__class__.__name__.replace('Message', '').lower()
            else:
                role = 'user'
            content = msg.content if hasattr(msg, 'content') else str(msg)
            messages_dict.append({"role": role, "content": content})
        return messages_dict

    if original_ainvoke:
        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, messages, config=None, **kwargs):
            """Traced and intercepted version of LLM ainvoke.

            Automatically:
            - Runs pre-call interception hooks (can block requests)
            - Creates trace/span for observability
            - Runs post-call interception hooks (quality checks)
            """
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace

            aigie = get_aigie()
            model_name = getattr(self, 'model_name', None) or getattr(self, 'model', 'unknown')

            # Convert messages for interception
            messages_dict = _convert_messages_to_dict(messages)

            # Pre-call interception (if enabled)
            interception_ctx = None
            if aigie and aigie._initialized and aigie.config.enable_interception:
                try:
                    from ..interceptor import InterceptionDecision

                    interception_ctx = await aigie.intercept_pre_call(
                        provider=provider,
                        model=model_name,
                        messages=messages_dict,
                    )

                    # Check if blocked
                    if interception_ctx.decision == InterceptionDecision.BLOCK:
                        block_reason = getattr(interception_ctx, 'block_reason', 'Blocked by interception policy')
                        logger.warning(f"LLM call blocked: {block_reason}")
                        raise Exception(f"Request blocked: {block_reason}")
                except ImportError:
                    pass  # Interception not available
                except Exception as e:
                    if "blocked" in str(e).lower():
                        raise
                    # Log but continue if interception fails
                    logger.debug(f"Pre-call interception error (continuing): {e}")

            # Setup tracing callback
            # Use existing parent trace if available, otherwise create new one
            trace = None
            if aigie and aigie._initialized:
                from ..auto_instrument.trace import get_current_trace
                trace = get_current_trace()

                if trace:
                    logger.debug(f"Using existing parent trace: {trace.name} ({trace.id})")
                else:
                    # No parent trace - create one for this LLM call
                    trace = await get_or_create_trace(
                        name=f"LLM Call: {provider}",
                        metadata={"provider": provider, "type": "llm", "model": model_name}
                    )
                    logger.debug(f"Created new trace for LLM call: {trace.id if trace else 'None'}")

                if trace:
                    callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                    if config is None:
                        config = {}
                    if 'callbacks' not in config:
                        config['callbacks'] = []
                    config['callbacks'].append(callback)

            # Make the actual LLM call with potential auto-retry
            max_retries = getattr(aigie.config, 'auto_fix_max_retries', 2) if aigie else 2
            retry_count = 0
            last_response = None
            last_interception_ctx = interception_ctx

            while retry_count <= max_retries:
                # Make the LLM call
                response = await original_ainvoke(self, messages, config=config, **kwargs)
                last_response = response

                # Post-call interception (if enabled)
                if last_interception_ctx and aigie and aigie._initialized and aigie.config.enable_interception:
                    try:
                        response_content = response.content if hasattr(response, 'content') else str(response)
                        last_interception_ctx.response_content = response_content
                        last_interception_ctx = await aigie.intercept_post_call(last_interception_ctx, response=None)

                        from ..interceptor import InterceptionDecision

                        # Check if auto-fix/retry is needed
                        if last_interception_ctx.decision == InterceptionDecision.RETRY and retry_count < max_retries:
                            retry_count += 1
                            fixes = getattr(last_interception_ctx, 'fixes_applied', [])

                            logger.info(f"Quality issue detected - auto-retrying (attempt {retry_count}/{max_retries})")

                            # Apply fixes to messages
                            for fix_action in fixes:
                                if hasattr(fix_action, 'parameters') and fix_action.parameters:
                                    params = fix_action.parameters

                                    # Inject corrective instruction
                                    if 'instruction' in params:
                                        instruction = params['instruction']
                                        # Add instruction to system message or create one
                                        from langchain_core.messages import SystemMessage
                                        if messages and hasattr(messages[0], 'type') and messages[0].type == 'system':
                                            messages[0].content += f"\n\nIMPORTANT: {instruction}"
                                        else:
                                            messages = [SystemMessage(content=f"IMPORTANT: {instruction}")] + list(messages)
                                        logger.info(f"Injected corrective instruction: {instruction[:80]}...")

                                    # Modify messages if provided
                                    if 'messages' in params:
                                        messages = params['messages']

                            # Re-create interception context for retry
                            last_interception_ctx = await aigie.intercept_pre_call(
                                provider=provider,
                                model=model_name,
                                messages=_convert_messages_to_dict(messages),
                            )
                            continue  # Retry the loop

                        elif last_interception_ctx.decision == InterceptionDecision.MODIFY:
                            logger.info(f"Quality issues detected in LLM response - recommendation generated")

                    except Exception as e:
                        logger.debug(f"Post-call interception error (continuing): {e}")

                # No retry needed or max retries reached
                break

            return last_response

        llm_class.ainvoke = traced_ainvoke

    if original_invoke:
        @functools.wraps(original_invoke)
        def traced_invoke(self, messages, config=None, **kwargs):
            """Traced and intercepted version of LLM invoke (sync).

            Automatically:
            - Runs pre-call interception hooks (can block requests)
            - Creates trace/span for observability
            - Runs post-call interception hooks (quality checks)
            """
            from ..client import get_aigie
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace_sync

            aigie = get_aigie()
            model_name = getattr(self, 'model_name', None) or getattr(self, 'model', 'unknown')

            # Convert messages for interception
            messages_dict = _convert_messages_to_dict(messages)

            # Pre-call interception (if enabled) - need to run async in sync context
            interception_ctx = None
            if aigie and aigie._initialized and aigie.config.enable_interception:
                try:
                    from ..interceptor import InterceptionDecision
                    import asyncio

                    # Run async interception in sync context
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Can't run sync in async context, skip interception
                            pass
                        else:
                            interception_ctx = loop.run_until_complete(
                                aigie.intercept_pre_call(
                                    provider=provider,
                                    model=model_name,
                                    messages=messages_dict,
                                )
                            )
                    except RuntimeError:
                        interception_ctx = asyncio.run(
                            aigie.intercept_pre_call(
                                provider=provider,
                                model=model_name,
                                messages=messages_dict,
                            )
                        )

                    # Check if blocked
                    if interception_ctx and interception_ctx.decision == InterceptionDecision.BLOCK:
                        block_reason = getattr(interception_ctx, 'block_reason', 'Blocked by interception policy')
                        logger.warning(f"LLM call blocked: {block_reason}")
                        raise Exception(f"Request blocked: {block_reason}")
                except ImportError:
                    pass  # Interception not available
                except Exception as e:
                    if "blocked" in str(e).lower():
                        raise
                    logger.debug(f"Pre-call interception error (continuing): {e}")

            # Setup tracing callback
            # Use existing parent trace if available, otherwise create new one
            trace = None
            if aigie and aigie._initialized:
                from ..auto_instrument.trace import get_current_trace
                trace = get_current_trace()

                if not trace:
                    # No parent trace - create one for this LLM call
                    trace = get_or_create_trace_sync(
                        name=f"LLM Call: {provider}",
                        metadata={"provider": provider, "type": "llm", "model": model_name}
                    )

                if trace:
                    callback = AigieCallbackHandler(aigie=aigie, trace=trace)
                    if config is None:
                        config = {}
                    if 'callbacks' not in config:
                        config['callbacks'] = []
                    config['callbacks'].append(callback)

            # Make the actual LLM call
            response = original_invoke(self, messages, config=config, **kwargs)

            # Post-call interception (if enabled)
            if interception_ctx and aigie and aigie._initialized and aigie.config.enable_interception:
                try:
                    import asyncio
                    response_content = response.content if hasattr(response, 'content') else str(response)
                    interception_ctx.response_content = response_content

                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            interception_ctx = loop.run_until_complete(
                                aigie.intercept_post_call(interception_ctx, response=None)
                            )
                    except RuntimeError:
                        interception_ctx = asyncio.run(
                            aigie.intercept_post_call(interception_ctx, response=None)
                        )

                    from ..interceptor import InterceptionDecision
                    if interception_ctx and interception_ctx.decision == InterceptionDecision.MODIFY:
                        logger.info(f"Quality issues detected in LLM response - recommendation generated")
                except Exception as e:
                    logger.debug(f"Post-call interception error (continuing): {e}")

            return response

        llm_class.invoke = traced_invoke

