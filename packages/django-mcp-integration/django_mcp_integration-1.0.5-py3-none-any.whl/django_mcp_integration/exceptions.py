from fastmcp.exceptions import FastMCPError


class DjangoMCPError(FastMCPError):
    """Base exception for django-mcp-integration."""
    pass


class ToolRegistrationError(DjangoMCPError):
    """Raised when tool registration fails."""
    
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Failed to register tool '{tool_name}': {reason}")


class InvalidToolSignatureError(ToolRegistrationError):
    """Raised when tool signature is invalid."""
    pass


class ToolDiscoveryError(DjangoMCPError):
    """Raised when tool discovery fails."""
    pass


class ServerConfigurationError(DjangoMCPError):
    """Raised when server configuration is invalid."""
    pass


class AuthenticationError(DjangoMCPError):
    """Error in authentifation operations."""