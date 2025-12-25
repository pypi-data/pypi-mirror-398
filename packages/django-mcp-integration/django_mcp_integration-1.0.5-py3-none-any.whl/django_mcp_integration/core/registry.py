"""Enhanced thread-safe registry with auto-reload support."""
from typing import Any, Dict, List, Optional
from functools import lru_cache
from threading import RLock

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Thread-safe registry with caching and auto-reload support."""
    
    _instance: Optional["ToolRegistry"] = None
    _lock = RLock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            from .conf import config
            self._tools: Dict[str, Any] = {}
            self._metadata: Dict[str, Dict] = {}
            self._config = config
            self._initialized = True
            self._reload_count = 0
            logger.debug("🔧 Registry initialized")
    
    def register(
        self,
        tool_instance: Any,
        metadata: Optional[Dict] = None,
        force: bool = False
    ) -> None:
        """Register a tool with metadata."""
        tool_name = getattr(tool_instance, "name", type(tool_instance).__name__)
        
        with self._lock:
            if tool_name in self._tools and not force:
                logger.debug(f"🔄 Tool '{tool_name}' already registered, skipping...")
                return
            
            self._tools[tool_name] = tool_instance
            self._metadata[tool_name] = metadata or {}
            
            # Clear cache when registry changes
            if self._config.enable_cache:
                self.get_tools.cache_clear()
                self.get_tool_names.cache_clear()
            
            logger.info(f"✅ Registered tool: {tool_name}")
    
    def reload(self) -> None:
        """Reload all tools (for auto-reload support)."""
        with self._lock:
            self._reload_count += 1
            logger.info(f"🔄 Reloading registry (reload #{self._reload_count})...")
            
            # Keep tools but clear cache
            if self._config.enable_cache:
                self.get_tools.cache_clear()
                self.get_tool_names.cache_clear()
            
            logger.info(f"✅ Registry reloaded ({len(self._tools)} tools)")
    
    @lru_cache(maxsize=1)
    def get_tools(self) -> List[Any]:
        """Get all registered tools (cached)."""
        return list(self._tools.values())
    
    @lru_cache(maxsize=1)
    def get_tool_names(self) -> List[str]:
        """Get all tool names (cached)."""
        return list(self._tools.keys())
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get a specific tool by name."""
        return self._tools.get(name)
    
    def get_metadata(self, name: str) -> Optional[Dict]:
        """Get tool metadata."""
        return self._metadata.get(name)
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                if name in self._metadata:
                    del self._metadata[name]
                
                if self._config.enable_cache:
                    self.get_tools.cache_clear()
                    self.get_tool_names.cache_clear()
                
                logger.info(f"🗑️  Unregistered tool: {name}")
                return True
        return False
    
    def clear(self) -> None:
        """Clear all registered tools."""
        with self._lock:
            count = len(self._tools)
            self._tools.clear()
            self._metadata.clear()
            
            if self._config.enable_cache:
                self.get_tools.cache_clear()
                self.get_tool_names.cache_clear()
            
            logger.info(f"🧹 Registry cleared ({count} tools removed)")
    
    def stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "tools": list(self._tools.keys()),
            "cache_enabled": self._config.enable_cache,
            "reload_count": self._reload_count,
        }


# Global registry instance
registry = ToolRegistry()