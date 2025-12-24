from datetime import datetime
from typing import Any
from uuid import UUID


def serialize_for_firestore(obj: Any) -> Any:
    """Convert UUID and datetime objects to Firestore-compatible types (strings)."""
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "model_dump") and callable(obj.model_dump):
        # Handle LangChain BaseMessage and Pydantic models
        return serialize_for_firestore(obj.model_dump())
    elif isinstance(obj, dict):
        return {k: serialize_for_firestore(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_firestore(item) for item in obj]
    return obj


def deserialize_from_firestore(obj: Any) -> Any:
    """Convert strings back to UUID and datetime objects, and reconstruct Pydantic models."""
    if isinstance(obj, str):
        # Try to parse as UUID
        try:
            return UUID(obj)
        except (ValueError, AttributeError):
            pass
        # Try to parse as datetime
        try:
            return datetime.fromisoformat(obj)
        except (ValueError, TypeError):
            pass
    elif isinstance(obj, dict):
        # Recursively deserialize dict values
        deserialized = {k: deserialize_from_firestore(v) for k, v in obj.items()}

        # Try to reconstruct LangChain message objects from dict
        # Check if this looks like a message (has type field with specific values)
        if "type" in deserialized:
            try:
                from langchain_core.messages import (
                    AIMessage,
                    FunctionMessage,
                    HumanMessage,
                    SystemMessage,
                    ToolMessage,
                )

                msg_type = deserialized.get("type")
                if msg_type == "human":
                    return HumanMessage(**deserialized)
                elif msg_type == "ai":
                    return AIMessage(**deserialized)
                elif msg_type == "system":
                    return SystemMessage(**deserialized)
                elif msg_type == "tool":
                    return ToolMessage(**deserialized)
                elif msg_type == "function":
                    return FunctionMessage(**deserialized)
            except (ImportError, TypeError, ValueError):
                # If message reconstruction fails, return dict as-is
                pass

        return deserialized
    elif isinstance(obj, list):
        return [deserialize_from_firestore(item) for item in obj]
    return obj
