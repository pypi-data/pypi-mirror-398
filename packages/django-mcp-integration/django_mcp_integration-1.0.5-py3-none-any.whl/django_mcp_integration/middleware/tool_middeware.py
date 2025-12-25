from typing import List

from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError

from ..core.registry import registry



class ToolMiddleware(Middleware):
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        result = await call_next(context)
        
        from ..permissions.handlers import PermissionHandler
        
        tools = [
            tool for tool in result 
            if PermissionHandler.check_permissions(registry.get_tool(tool.name))
        ]        
        return tools
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Access the tool object to check its metadata
        if context.fastmcp_context:
            try:
                tool = registry.get_tool(context.message.name)
                
                from ..permissions.handlers import PermissionHandler
                
                if not PermissionHandler.check_permissions(tool):
                    raise ToolError(f"Access denied for tool: {tool.name}")
                
                if not tool.enabled:
                    raise ToolError("Tool is currently disabled")
                
            except Exception:
                pass
        
        return await call_next(context)
    
    