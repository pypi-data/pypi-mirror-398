"""
Aigie Realtime Module - Backend connector for real-time interception.

This module provides WebSocket-based communication with the Aigie backend
for real-time consultation, fix application, and leveraging historical data.
"""

from .connector import BackendConnector, ConnectionState
from .auto_fix import AutoFixApplicator, FixStrategy, FixResult, FixConfig

__all__ = [
    "BackendConnector",
    "ConnectionState",
    "AutoFixApplicator",
    "FixStrategy",
    "FixResult",
    "FixConfig",
]
