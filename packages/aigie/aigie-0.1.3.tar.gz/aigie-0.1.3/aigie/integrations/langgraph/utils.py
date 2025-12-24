"""
Utility functions for LangGraph integration.
"""

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


def is_langgraph_available() -> bool:
    """Check if LangGraph is installed and importable.

    Returns:
        True if LangGraph is available
    """
    try:
        import langgraph
        return True
    except ImportError:
        return False


def get_langgraph_version() -> Optional[str]:
    """Get the installed LangGraph version.

    Returns:
        Version string or None if not installed
    """
    try:
        import langgraph
        return getattr(langgraph, "__version__", "unknown")
    except ImportError:
        return None


def safe_str(value: Any, max_length: int = 1000) -> str:
    """Safely convert a value to string with length limit.

    Args:
        value: Value to convert
        max_length: Maximum length of output string

    Returns:
        String representation, truncated if necessary
    """
    try:
        if value is None:
            return ""
        s = str(value)
        if len(s) > max_length:
            return s[:max_length] + "..."
        return s
    except Exception as e:
        return f"<error: {e}>"


def extract_node_name(node: Any) -> str:
    """Extract a meaningful name from a LangGraph node.

    Args:
        node: The node object or name

    Returns:
        Node name string
    """
    if isinstance(node, str):
        return node

    # Try common attributes
    name_attrs = ["name", "__name__", "_name", "node_name"]
    for attr in name_attrs:
        if hasattr(node, attr):
            value = getattr(node, attr)
            if isinstance(value, str) and value:
                return value

    # Fallback to class name
    if hasattr(node, "__class__"):
        return node.__class__.__name__

    return "unknown_node"


def extract_edge_name(source: Any, target: Any) -> str:
    """Create a name for an edge between two nodes.

    Args:
        source: Source node
        target: Target node

    Returns:
        Edge name string
    """
    source_name = extract_node_name(source)
    target_name = extract_node_name(target)
    return f"{source_name} -> {target_name}"


def extract_graph_structure(graph: Any) -> Dict[str, Any]:
    """Extract structural information from a LangGraph graph.

    Args:
        graph: The LangGraph StateGraph or CompiledGraph

    Returns:
        Dictionary with graph structure information
    """
    structure = {
        "nodes": [],
        "edges": [],
        "entry_point": None,
        "node_count": 0,
        "edge_count": 0,
    }

    try:
        # Try to get nodes
        if hasattr(graph, "nodes"):
            nodes = graph.nodes
            if isinstance(nodes, dict):
                structure["nodes"] = list(nodes.keys())
            elif hasattr(nodes, "__iter__"):
                structure["nodes"] = [extract_node_name(n) for n in nodes]
            structure["node_count"] = len(structure["nodes"])

        # Try to get edges
        if hasattr(graph, "edges"):
            edges = graph.edges
            if isinstance(edges, dict):
                structure["edges"] = [
                    {"source": k[0] if isinstance(k, tuple) else k,
                     "target": v if isinstance(v, str) else extract_node_name(v)}
                    for k, v in edges.items()
                ]
            elif hasattr(edges, "__iter__"):
                structure["edges"] = list(edges)
            structure["edge_count"] = len(structure["edges"])

        # Try to get entry point
        if hasattr(graph, "_entry_point"):
            structure["entry_point"] = extract_node_name(graph._entry_point)
        elif hasattr(graph, "entry_point"):
            structure["entry_point"] = extract_node_name(graph.entry_point)

    except Exception as e:
        logger.debug(f"Error extracting graph structure: {e}")

    return structure


def extract_state_info(state: Any) -> Dict[str, Any]:
    """Extract information from a LangGraph state object.

    Args:
        state: The state object (typically a TypedDict or dict)

    Returns:
        Dictionary with state information
    """
    info = {
        "type": type(state).__name__,
        "keys": [],
        "message_count": 0,
        "has_messages": False,
    }

    try:
        if isinstance(state, dict):
            info["keys"] = list(state.keys())

            # Check for messages (common in chat-based graphs)
            if "messages" in state:
                messages = state["messages"]
                if isinstance(messages, list):
                    info["message_count"] = len(messages)
                    info["has_messages"] = True

        elif hasattr(state, "__dict__"):
            info["keys"] = list(state.__dict__.keys())

    except Exception as e:
        logger.debug(f"Error extracting state info: {e}")

    return info


def format_state_for_trace(state: Any, max_length: int = 2000) -> Dict[str, Any]:
    """Format a state object for inclusion in trace metadata.

    Args:
        state: The state object
        max_length: Maximum length for string values

    Returns:
        Formatted state dictionary
    """
    try:
        if isinstance(state, dict):
            formatted = {}
            for key, value in state.items():
                if key == "messages" and isinstance(value, list):
                    # Summarize messages instead of full content
                    formatted["messages"] = {
                        "count": len(value),
                        "last_message": safe_str(value[-1], max_length) if value else None,
                    }
                elif isinstance(value, str) and len(value) > max_length:
                    formatted[key] = value[:max_length] + "..."
                elif isinstance(value, (dict, list)):
                    formatted[key] = safe_str(value, max_length)
                else:
                    formatted[key] = value
            return formatted

        return {"state": safe_str(state, max_length)}

    except Exception as e:
        return {"error": str(e)}


def get_execution_path(events: List[Any]) -> List[str]:
    """Extract the execution path from a list of LangGraph events.

    Args:
        events: List of events from graph execution

    Returns:
        List of node names in execution order
    """
    path = []

    for event in events:
        try:
            if isinstance(event, dict):
                # Handle standard event format
                if "name" in event:
                    path.append(event["name"])
                elif "node" in event:
                    path.append(event["node"])
                elif "__langgraph_name__" in event:
                    path.append(event["__langgraph_name__"])

            elif hasattr(event, "name"):
                path.append(event.name)

        except Exception:
            continue

    return path


def mask_sensitive_state(state: dict, patterns: Optional[List[str]] = None) -> dict:
    """Mask potentially sensitive data in state.

    Args:
        state: State dictionary to mask
        patterns: Optional list of key patterns to mask

    Returns:
        State with sensitive data masked
    """
    import re

    # Default patterns for sensitive keys
    default_patterns = [
        r".*password.*",
        r".*secret.*",
        r".*token.*",
        r".*api_key.*",
        r".*apikey.*",
        r".*credential.*",
        r".*auth.*",
    ]

    patterns_to_use = patterns if patterns is not None else default_patterns

    def should_mask(key: str) -> bool:
        for pattern in patterns_to_use:
            if re.match(pattern, key, re.IGNORECASE):
                return True
        return False

    def mask_dict(d: dict) -> dict:
        masked = {}
        for key, value in d.items():
            if should_mask(key):
                masked[key] = "[REDACTED]"
            elif isinstance(value, dict):
                masked[key] = mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [mask_dict(v) if isinstance(v, dict) else v for v in value]
            else:
                masked[key] = value
        return masked

    return mask_dict(state)


def calculate_state_diff(old_state: dict, new_state: dict) -> Dict[str, Any]:
    """Calculate the difference between two state objects.

    Args:
        old_state: Previous state
        new_state: New state

    Returns:
        Dictionary describing the changes
    """
    diff = {
        "added": [],
        "removed": [],
        "modified": [],
        "unchanged": [],
    }

    old_keys = set(old_state.keys()) if isinstance(old_state, dict) else set()
    new_keys = set(new_state.keys()) if isinstance(new_state, dict) else set()

    diff["added"] = list(new_keys - old_keys)
    diff["removed"] = list(old_keys - new_keys)

    for key in old_keys & new_keys:
        if old_state.get(key) != new_state.get(key):
            diff["modified"].append(key)
        else:
            diff["unchanged"].append(key)

    return diff
