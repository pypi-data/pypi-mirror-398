"""Django app configuration with auto-reload support."""
from django.apps import AppConfig
from django.utils.autoreload import autoreload_started

from .utils.logging import get_logger

logger = get_logger(__name__)


class DjangoMCPConfig(AppConfig):
    """Django MCP Integration app configuration with auto-reload."""
    
    name = "django_mcp_integration"
    verbose_name = "Django MCP Integration"
    default_auto_field = "django.db.models.BigAutoField"
    
    def ready(self):
        """Initialize MCP integration when Django starts."""
        try:
            logger.info("🚀 Initializing Django MCP Integration...")
            
            # Register auto-reload handler
            autoreload_started.connect(self._on_autoreload_started)
            
            # Initialize normally
            self._initialize_mcp()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP: {e}", exc_info=True)
            raise
    
    def _initialize_mcp(self):
        """Initialize MCP components."""
        # Load configuration
        from .core.conf import config
        
        # Clear registry (important for reload)
        from .core.registry import registry
        registry.reload()
        
        # Discover tools
        from .core.discovery import ToolDiscovery
        discovery = ToolDiscovery(config)
        discovered_tools = discovery.discover_all()
        
        # Register tools in MCP server
        self._register_tools_to_server()
        
        # Log statistics
        stats = registry.stats()
        logger.info(f"✅ Django MCP Integration initialized")
        logger.info(f"📊 Statistics: {stats['total_tools']} tools, reload #{stats['reload_count']}")
        
        # Log any discovery errors
        errors = discovery.get_discovery_errors()
        if errors:
            logger.warning(f"⚠️  {len(errors)} discovery error(s) occurred")
    
    def _on_autoreload_started(self, sender, **kwargs):
        """Handle Django auto-reload event."""
        logger.info("🔄 Auto-reload detected, reinitializing MCP...")
        self._initialize_mcp()
    
    def _register_tools_to_server(self):
        """Register all tools from registry to MCP server."""
        from .core.server import mcp_server
        from .core.registry import registry
        from .decorators.tools import ToolWrapper
        
        tools: list[ToolWrapper] = registry.get_tools()
        logger.info(f"🔧 Registering {len(tools)} tools to MCP server...")
        
        for tool_wrapper in tools:
            try:
                
                # Create executor with explicit parameters (no **kwargs)
                executor = tool_wrapper.target
                
                # Register the executor to FastMCP
                mcp_server.tool(
                    name=tool_wrapper.name,
                    title=tool_wrapper.title,
                    description=tool_wrapper.description,
                    icons=tool_wrapper.icons,
                    tags=tool_wrapper.tags,
                    output_schema=tool_wrapper.output_schema,
                    annotations=tool_wrapper.annotations,
                    exclude_args=tool_wrapper.exclude_args,
                    meta=tool_wrapper.meta,
                    enabled=tool_wrapper.enabled,
                    task=tool_wrapper.task
                )(executor)
                
                logger.debug(f"✅ Registered to server: {tool_wrapper.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to register tool {tool_wrapper.name}: {e}", exc_info=True)