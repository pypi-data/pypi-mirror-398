"""Permission handling utilities."""
from typing import List, Any, Optional
from .base import BaseHasAPIKey, AllowAny
from ..exceptions import DjangoMCPError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PermissionDenied(DjangoMCPError):
    """Exception raised when permission is denied."""
    
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(message)


class PermissionHandler:
    """Handle permission checks for tools."""
    
    @staticmethod
    async def check_permissions(
        tool: Any,
    ) -> None:    
            
        permissions = tool.permissions
        
        if not permissions:
            # No permissions specified, allow access
            return await AllowAny().has_permission(tool)
        
        # Check global permissions
        for permission in permissions:
            has_perm = await permission.has_permission(tool)
            
            if not has_perm:
                logger.warning(
                    f"Permission denied for tool '{getattr(tool, 'name', 'unknown')}': "
                    f"{permission.message}"
                )
                raise PermissionDenied(permission.message)
        
        logger.debug(f"All permissions passed for tool '{getattr(tool, 'name', 'unknown')}'")
    
    @staticmethod
    def get_permission_classes(
        permission_classes: Optional[List[type]] = None
    ) -> List[BaseHasAPIKey]:
        """
        Instantiate permission classes.
        
        Args:
            permission_classes: List of permission class types
        
        Returns:
            List of instantiated permission objects
        """
        if not permission_classes:
            return [AllowAny()]
        
        return [perm() if isinstance(perm, type) else perm 
                for perm in permission_classes]