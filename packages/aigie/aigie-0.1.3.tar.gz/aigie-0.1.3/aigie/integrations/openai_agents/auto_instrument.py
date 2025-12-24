"""
OpenAI Agents SDK auto-instrumentation.

Automatically patches OpenAI Agents SDK classes to create traces.
"""

import functools
import logging
import uuid
from typing import Any, Set

logger = logging.getLogger(__name__)

_patched_classes: Set[Any] = set()


def patch_openai_agents() -> bool:
    """Patch OpenAI Agents SDK classes for auto-instrumentation.

    This adds the Aigie tracing processor to the SDK's tracing system.
    It's additive - it doesn't replace existing tracing.

    Returns:
        True if patching was successful (or already patched)
    """
    success = True
    success = _add_aigie_processor() and success
    success = _patch_runner() and success
    success = _patch_agent() and success
    return success


def unpatch_openai_agents() -> None:
    """Remove OpenAI Agents SDK patches (for testing)."""
    global _patched_classes
    _patched_classes.clear()


def is_openai_agents_patched() -> bool:
    """Check if OpenAI Agents SDK has been patched."""
    return len(_patched_classes) > 0


def _add_aigie_processor() -> bool:
    """Add Aigie tracing processor to the SDK.

    Returns:
        True if successful
    """
    try:
        # Try to import the SDK
        try:
            from agents import add_trace_processor
        except ImportError:
            try:
                from openai_agents import add_trace_processor
            except ImportError:
                logger.debug("OpenAI Agents SDK not installed")
                return True  # Not an error, just not installed

        # Check if already added
        if "aigie_processor" in _patched_classes:
            return True

        # Create and add processor
        from .processor import AigieTracingProcessor
        processor = AigieTracingProcessor()

        try:
            add_trace_processor(processor)
            _patched_classes.add("aigie_processor")
            logger.debug("Added Aigie tracing processor to OpenAI Agents SDK")
        except Exception as e:
            logger.debug(f"Could not add trace processor: {e}")
            # Continue anyway - the processor can be added manually

        return True

    except Exception as e:
        logger.warning(f"Failed to add Aigie processor: {e}")
        return False


def _patch_runner() -> bool:
    """Patch Runner.run() and Runner.run_sync() methods.

    Returns:
        True if successful
    """
    try:
        # Try different import paths
        Runner = None
        try:
            from agents import Runner
        except ImportError:
            try:
                from openai_agents import Runner
            except ImportError:
                logger.debug("OpenAI Agents SDK Runner not found")
                return True

        if Runner in _patched_classes:
            return True

        original_run = getattr(Runner, 'run', None)
        original_run_sync = getattr(Runner, 'run_sync', None)

        if original_run:
            @functools.wraps(original_run)
            async def traced_run(agent, input_data, *args, **kwargs):
                """Traced version of Runner.run()."""
                from ...client import get_aigie
                from .handler import OpenAIAgentsHandler

                aigie = get_aigie()
                if aigie and aigie._initialized:
                    handler = OpenAIAgentsHandler(
                        trace_name=f"Agent: {getattr(agent, 'name', 'unknown')}",
                        metadata={'agent_type': type(agent).__name__},
                    )
                    handler._aigie = aigie

                    workflow_id = await handler.handle_workflow_start(
                        workflow_name=getattr(agent, 'name', 'agent_workflow'),
                        input_data=input_data,
                    )

                    try:
                        result = await original_run(agent, input_data, *args, **kwargs)

                        await handler.handle_workflow_end(
                            workflow_id=workflow_id,
                            output=result,
                        )

                        return result

                    except Exception as e:
                        await handler.handle_workflow_end(
                            workflow_id=workflow_id,
                            error=str(e),
                        )
                        raise

                return await original_run(agent, input_data, *args, **kwargs)

            Runner.run = staticmethod(traced_run)

        if original_run_sync:
            @functools.wraps(original_run_sync)
            def traced_run_sync(agent, input_data, *args, **kwargs):
                """Traced version of Runner.run_sync()."""
                from ...client import get_aigie
                from .handler import OpenAIAgentsHandler
                import asyncio

                aigie = get_aigie()
                if aigie and aigie._initialized:
                    handler = OpenAIAgentsHandler(
                        trace_name=f"Agent: {getattr(agent, 'name', 'unknown')}",
                        metadata={'agent_type': type(agent).__name__},
                    )
                    handler._aigie = aigie

                    # Run async handler in sync context
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    asyncio.run,
                                    handler.handle_workflow_start(
                                        workflow_name=getattr(agent, 'name', 'agent_workflow'),
                                        input_data=input_data,
                                    )
                                )
                                workflow_id = future.result(timeout=5)
                        else:
                            workflow_id = loop.run_until_complete(
                                handler.handle_workflow_start(
                                    workflow_name=getattr(agent, 'name', 'agent_workflow'),
                                    input_data=input_data,
                                )
                            )
                    except Exception as e:
                        logger.debug(f"Error starting workflow trace: {e}")
                        return original_run_sync(agent, input_data, *args, **kwargs)

                    try:
                        result = original_run_sync(agent, input_data, *args, **kwargs)

                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        asyncio.run,
                                        handler.handle_workflow_end(
                                            workflow_id=workflow_id,
                                            output=result,
                                        )
                                    )
                                    future.result(timeout=5)
                            else:
                                loop.run_until_complete(
                                    handler.handle_workflow_end(
                                        workflow_id=workflow_id,
                                        output=result,
                                    )
                                )
                        except Exception as e:
                            logger.debug(f"Error ending workflow trace: {e}")

                        return result

                    except Exception as e:
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        asyncio.run,
                                        handler.handle_workflow_end(
                                            workflow_id=workflow_id,
                                            error=str(e),
                                        )
                                    )
                                    future.result(timeout=5)
                            else:
                                loop.run_until_complete(
                                    handler.handle_workflow_end(
                                        workflow_id=workflow_id,
                                        error=str(e),
                                    )
                                )
                        except Exception:
                            pass
                        raise

                return original_run_sync(agent, input_data, *args, **kwargs)

            Runner.run_sync = staticmethod(traced_run_sync)

        _patched_classes.add(Runner)
        logger.debug("Patched Runner for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("OpenAI Agents SDK not installed, skipping Runner patch")
        return True
    except Exception as e:
        logger.warning(f"Failed to patch Runner: {e}")
        return False


def _patch_agent() -> bool:
    """Patch Agent class for additional instrumentation.

    Returns:
        True if successful
    """
    try:
        # Try different import paths
        Agent = None
        try:
            from agents import Agent
        except ImportError:
            try:
                from openai_agents import Agent
            except ImportError:
                logger.debug("OpenAI Agents SDK Agent not found")
                return True

        if Agent in _patched_classes:
            return True

        # Store original __init__
        original_init = Agent.__init__

        @functools.wraps(original_init)
        def traced_init(self, *args, **kwargs):
            """Traced version of Agent.__init__()."""
            original_init(self, *args, **kwargs)

            # Store agent info for tracing
            self._aigie_agent_id = str(uuid.uuid4())
            self._aigie_metadata = {
                "name": getattr(self, 'name', 'unknown'),
                "model": getattr(self, 'model', None),
                "tools": [
                    getattr(t, 'name', str(t))
                    for t in getattr(self, 'tools', [])
                ],
                "handoffs": [
                    getattr(h, 'name', str(h))
                    for h in getattr(self, 'handoffs', [])
                ],
            }

        Agent.__init__ = traced_init
        _patched_classes.add(Agent)

        logger.debug("Patched Agent for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("OpenAI Agents SDK not installed, skipping Agent patch")
        return True
    except Exception as e:
        logger.warning(f"Failed to patch Agent: {e}")
        return False
