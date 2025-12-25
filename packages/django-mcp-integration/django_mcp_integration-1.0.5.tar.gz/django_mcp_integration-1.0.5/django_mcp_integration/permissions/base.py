"""Base permission classes inspired by DRF."""
from typing import Any, Optional
from abc import ABC
from starlette.requests import Request
from ..models import AbstractAPIKey, APIKey


class KeyParser:
    keyword = "Api-Key"

    def get(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("authorization", None)

        if not authorization:
            return None

        keyword = f"{self.keyword} "
        if not authorization.startswith(keyword):
            return None
        
        api_key = authorization.removeprefix(keyword)
        return api_key
    
    
class BaseHasAPIKey(ABC):
    """
    Require valid API key
    
    Looks for API key in:
    1. Authorization header: "Api-Key YOUR_KEY"
    2. X-API-Key header
    3. api_key query parameter
    """
    prefix = "Api-Key"
    message = "Valid API key required."
    model: Optional[type[AbstractAPIKey]] = None
    key_parser = KeyParser()
    
    def get_key(self, request: Request) -> Optional[str]:
        return self.key_parser.get(request)
    

    def has_permission(self, tool: Any) -> bool:
        assert self.model is not None, (
            "%s must define `.model` with the API key model to use"
            % self.__class__.__name__
        )
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        key = self.get_key(request)
        if not key:
            return False
        return self.model.objects.is_valid(key)
    
    
class HasAPIKey(BaseHasAPIKey):
    model = APIKey


class AllowAny(BaseHasAPIKey):
    """Allow any access (no restrictions)."""
    
    async def has_permission(self, tool: Any) -> bool:
        return True



class CompositePermission(BaseHasAPIKey):
    """Combine multiple permissions with AND logic."""
    
    def __init__(self, *permissions: BaseHasAPIKey):
        self.permissions = permissions
    
    async def has_permission(self, tool: Any) -> bool:
        """All permissions must pass."""
        for permission in self.permissions:
            if not await permission.has_permission(tool):
                self.message = permission.message
                return False
        return True
    



class AnyPermission(BaseHasAPIKey):
    """Combine multiple permissions with OR logic."""
    
    def __init__(self, *permissions: BaseHasAPIKey):
        self.permissions = permissions
    
    async def has_permission(self, tool: Any) -> bool:
        """At least one permission must pass."""
        messages = []
        for permission in self.permissions:
            if await permission.has_permission(tool):
                return True
            messages.append(permission.message)
        
        self.message = " OR ".join(messages)
        return False