from agent_framework import ChatMessage, AgentExecutorResponse
from typing import Any

# Helper function to serialize executor input & output to JSON for frontend visualization
def serialize_data(data: Any, max_depth: int = 10) -> Any:
    """Serialize executor event data to JSON-serializable format.
    
    Handles complex types like ChatMessage, AgentExecutorResponse, dataclasses,
    enums, and objects with to_dict() or model_dump() methods.
    
    Args:
        data: The data to serialize
        max_depth: Maximum recursion depth to prevent infinite loops (default: 10)
    """
    if data is None:
        return None
    
    # Prevent infinite recursion
    if max_depth <= 0:
        return f"<max_depth_reached: {type(data).__name__}>"
    
    # Primitive types
    if isinstance(data, (str, int, float, bool)):
        return data
    
    # Handle Enum types (like Role)
    from enum import Enum
    if isinstance(data, Enum):
        return data.value if hasattr(data, 'value') else str(data)
    
    # Handle list
    if isinstance(data, list):
        return [serialize_data(item, max_depth - 1) for item in data]
    
    # Handle dict
    if isinstance(data, dict):
        return {k: serialize_data(v, max_depth - 1) for k, v in data.items()}
    
    # Handle ChatMessage - show as {"role":"xxx", "text":"xxx"}
    if isinstance(data, ChatMessage):
        role_str = data.role.value if hasattr(data.role, 'value') else str(data.role)
        return {"role": role_str, "text": data.text}
    
    # Handle AgentExecutorResponse
    if isinstance(data, AgentExecutorResponse):
        result = {}
        if hasattr(data, "agent_run_response") and data.agent_run_response:
            result["agent_run_response"] = serialize_data(data.agent_run_response, max_depth - 1)
        if hasattr(data, "full_conversation") and data.full_conversation:
            result["full_conversation"] = serialize_data(data.full_conversation, max_depth - 1)
        return result if result else {"type": type(data).__name__}
    
    # Handle objects with to_dict() method
    if hasattr(data, "to_dict") and callable(data.to_dict):
        try:
            return data.to_dict()
        except Exception:
            pass
    
    # Handle Pydantic models with model_dump()
    if hasattr(data, "model_dump") and callable(data.model_dump):
        try:
            return data.model_dump()
        except Exception:
            pass
    
    # Handle dataclasses
    if hasattr(data, "__dataclass_fields__"):
        try:
            from dataclasses import asdict
            return asdict(data)
        except Exception:
            pass
    
    # Handle objects with __dict__
    if hasattr(data, "__dict__"):
        try:
            return {k: serialize_data(v, max_depth - 1) for k, v in data.__dict__.items() if not k.startswith("_")}
        except Exception:
            pass
    
    # Fallback: convert to string representation
    try:
        return str(data)
    except Exception:
        return f"<{type(data).__name__}>"
