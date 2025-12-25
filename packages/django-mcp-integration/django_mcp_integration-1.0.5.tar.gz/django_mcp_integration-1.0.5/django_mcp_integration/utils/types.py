"""Type definitions and helpers."""
from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ToolProtocol(Protocol):
    """Protocol for MCP tools."""
    name: str
    description: str
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the tool."""
        ...


def is_valid_tool(obj: Any) -> bool:
    """Check if an object is a valid MCP tool."""
    return (
        hasattr(obj, 'name') and
        hasattr(obj, 'description') and
        hasattr(obj, 'execute') and
        callable(obj.execute)
    )