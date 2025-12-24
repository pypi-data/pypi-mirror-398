"""
LangChain callback handler for Aigie SDK.

This module provides the AigieCallbackHandler which implements LangChain's
BaseCallbackHandler protocol for automatic trace/span creation.

For full implementation, see aigie/callback.py which contains the main
AigieCallbackHandler class. This module re-exports it for convenience
and may add LangChain-specific enhancements in the future.
"""

# Re-export the main callback handler
from ...callback import AigieCallbackHandler

# Export for convenience
__all__ = ["AigieCallbackHandler", "LangChainHandler"]

# Alias for consistency with other integrations
LangChainHandler = AigieCallbackHandler
