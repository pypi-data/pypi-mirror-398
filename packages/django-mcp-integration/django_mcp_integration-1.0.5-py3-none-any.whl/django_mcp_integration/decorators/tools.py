"""Unified tool decorator supporting both classes and functions."""
import inspect
from typing import Any, Callable, Optional, Type, Union, List
from mcp.types import Icon, ToolAnnotations
from fastmcp.utilities.types import NotSet, NotSetT
from fastmcp.server.tasks.config import TaskConfig
from ..core.registry import registry
from ..exceptions import InvalidToolSignatureError
from ..utils.logging import get_logger
from ..permissions.base import BaseHasAPIKey

logger = get_logger(__name__)


class ToolWrapper:
    """Unified wrapper for both class-based and function-based tools."""
    
    def __init__(
        self,
        target: Union[Type, Callable],
        name: str,
        description: str,
        title: str | None = None,
        icons: list[Icon] | None = None,
        tags: set[str] | None = None,
        output_schema: dict[str, Any] | NotSetT | None = NotSet,
        annotations: ToolAnnotations | dict[str, Any] | None = None,
        exclude_args: list[str] | None = None,
        meta: dict[str, Any] | None = None,
        enabled: bool | None = None,
        task: bool | TaskConfig | None = None,
        permissions: Optional[List[BaseHasAPIKey]] = None
    ):
        self.original_target = target
        self.name = name
        self.description = description
        self.is_class = inspect.isclass(target)
        self.title = title
        self.icons = icons
        self.tags = tags
        self.output_schema = output_schema
        self.annotations = annotations
        self.exclude_args = exclude_args
        self.meta = meta
        self.enabled = enabled
        self.task = task
        self.permissions = permissions
        
        # Validate and get the executable target
        self._validate()
        self.target = self._get_executable_target()
    
    def _get_executable_target(self):
        """Get the actual executable function."""
        if self.is_class:
            # For class-based tools, return the execute method
            instance = self.original_target()
            return instance.execute
        else:
            # For function-based tools, return the function itself
            return self.original_target
    
    def _validate(self) -> None:
        """Validate tool structure."""
        if self.is_class:
            self._validate_class()
        else:
            self._validate_function()
    
    def _validate_class(self) -> None:
        """Validate class-based tool."""
        if not hasattr(self.original_target, 'execute'):
            raise InvalidToolSignatureError(
                self.original_target.__name__,
                "Tool class must have an 'execute' method"
            )
        
        if not inspect.iscoroutinefunction(self.original_target.execute):
            raise InvalidToolSignatureError(
                self.original_target.__name__,
                "'execute' method must be async (async def)"
            )
        
        self._check_kwargs(self.original_target.execute, self.original_target.__name__)
    
    def _validate_function(self) -> None:
        """Validate function-based tool."""
        if not inspect.iscoroutinefunction(self.original_target):
            raise InvalidToolSignatureError(
                self.original_target.__name__,
                "Tool function must be async (async def)"
            )
        
        self._check_kwargs(self.original_target, self.original_target.__name__)
    
    def _check_kwargs(self, func: Callable, name: str) -> None:
        """Check for **kwargs in signature."""
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param.kind == param.VAR_KEYWORD:
                raise InvalidToolSignatureError(
                    name,
                    f"Tool cannot use **kwargs. Define parameters explicitly."
                )
    
    def _get_param_type(self, param) -> str:
        """Determine JSON type from parameter annotation."""
        if param.annotation != param.empty:
            type_map = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            return type_map.get(param.annotation, "string")
        return "string"


def mcp_tool(
    name: Optional[str] = None,
    title: str | None = None,
    description: Optional[str] = None,
    icons: list[Icon] | None = None,
    tags: set[str] | None = None,
    output_schema: dict[str, Any] | NotSetT | None = NotSet,
    annotations: ToolAnnotations | dict[str, Any] | None = None,
    exclude_args: list[str] | None = None,
    meta: dict[str, Any] | None = None,
    enabled: bool | None = None,
    task: bool | TaskConfig | None = None,
    permissions: Optional[List[BaseHasAPIKey]] = None
):
    """
    Unified decorator for both class and function-based tools.
    """
    def decorator(target: Union[Type, Callable]) -> Union[Type, Callable]:
        # Determine if it's a class or function
        is_class = inspect.isclass(target)
        
        # Determine metadata
        tool_name = name or target.__name__
        tool_description = description or target.__doc__ or f"Tool {tool_name}"
        
        # Create wrapper
        wrapper = ToolWrapper(
            target=target,
            name=tool_name,
            title=title,
            description=tool_description,
            icons=icons,
            tags=tags,
            output_schema=output_schema,
            annotations=annotations,
            exclude_args=exclude_args,
            meta=meta,
            enabled=enabled,
            task=task,
            permissions=permissions
        )
        
        # Register in registry
        registry.register(wrapper, metadata={
            "type": "class" if is_class else "function",
        })
        
        # Mark as registered
        target._mcp_tool_registered = True
        
        logger.info(
            f"🛠️  {'Class' if is_class else 'Function'} tool registered: {tool_name}"
        )
        
        return target
    
    return decorator


# Aliases for convenience
tool = mcp_tool
resource = mcp_tool
prompt = mcp_tool