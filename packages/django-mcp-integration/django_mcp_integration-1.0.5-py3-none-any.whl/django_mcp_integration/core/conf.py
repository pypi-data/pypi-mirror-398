"""Centralized configuration management."""
from typing import Optional, List
from dataclasses import dataclass, field
from django.conf import settings


@dataclass
class MCPConfig:
    """MCP server configuration with validation."""
    
    # Core settings
    enabled: bool = getattr(settings, "MCP_ENABLED", True)
    name: str = getattr(settings, "MCP_SERVER_NAME", "Django MCP Integration")
    version: str = getattr(settings, "MCP_SERVER_VERSION", "1.0.0")
    instructions: Optional[str] = getattr(settings, "MCP_SERVER_INSTRUCTIONS", None)
    
    # Network settings
    host: str = getattr(settings, "MCP_HOST", "localhost")
    port: int = getattr(settings, "MCP_PORT", 8000)
    http_path: str = getattr(settings, "MCP_HTTP_PATH", "/mcp/")
    transport: str = "http"
    
    # Discovery settings
    auto_discover: bool = getattr(settings, "MCP_AUTO_DISCOVER", True)
    discover_patterns: List[str] = field(default_factory=lambda: [
        "tools.py",
        "mcp_tools.py",
        "mcp/*.py"
    ])
    
    # Performance settings
    enable_cache: bool = getattr(settings, "MCP_ENABLE_CACHE", True)
    cache_ttl: int = getattr(settings, "MCP_CACHE_TTL", 300)
    max_workers: int = getattr(settings, "MCP_MAX_WORKERS", 4)
    
    # Logging settings
    log_level: str = getattr(settings, "MCP_LOG_LEVEL", "INFO")
    log_requests: bool = getattr(settings, "MCP_LOG_REQUESTS", True)
    
    
    def validate(self) -> None:
        """Validate configuration."""
        from ..exceptions import ServerConfigurationError
        
        if self.port < 1 or self.port > 65535:
            raise ServerConfigurationError(f"Invalid port: {self.port}")
        
        if self.transport not in ["http", "stdio", "sse"]:
            raise ServerConfigurationError(f"Invalid transport: {self.transport}")
        
        if not self.http_path.startswith("/"):
            raise ServerConfigurationError(f"HTTP path must start with '/': {self.http_path}")
        
        
        
config = MCPConfig()
config.validate()