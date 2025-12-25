"""Enhanced tool discovery system."""
import importlib
import inspect
from pathlib import Path
from typing import List, Set, Type, Any
from django.apps import apps

from .conf import MCPConfig
from ..utils.logging import get_logger
from ..exceptions import ToolDiscoveryError

logger = get_logger(__name__)


class ToolDiscovery:
    """Advanced tool discovery engine."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self._discovered_modules: Set[str] = set()
        self._discovery_errors: List[Exception] = []
    
    def discover_all(self) -> List[Type]:
        """Discover all MCP tools across Django apps."""
        if not self.config.auto_discover:
            logger.info("🚫 Auto-discovery disabled")
            return []
        
        logger.info("🔍 Starting tool discovery across Django apps...")
        discovered_tools = []
        
        for app_config in apps.get_app_configs():
            # Skip Django internal apps
            if app_config.name.startswith('django.'):
                continue
            
            try:
                tools = self._discover_in_app(app_config)
                discovered_tools.extend(tools)
            except ToolDiscoveryError as e:
                logger.error(f"❌ Discovery failed in {app_config.name}: {e}")
                self._discovery_errors.append(e)
        
        logger.info(f"✅ Discovered {len(discovered_tools)} tools from {len(apps.get_app_configs())} apps")
        return discovered_tools
    
    def _discover_in_app(self, app_config) -> List[Type]:
        """Discover tools in a specific Django app."""
        app_path = Path(app_config.path)
        discovered = []
        
        logger.debug(f"📦 Scanning app: {app_config.name}")
        
        for pattern in self.config.discover_patterns:
            if "*" in pattern:
                # Handle directory patterns (e.g., "mcp/*.py")
                parts = pattern.split("/")
                if len(parts) == 2 and parts[1] == "*.py":
                    dir_name = parts[0]
                    dir_path = app_path / dir_name
                    if dir_path.exists() and dir_path.is_dir():
                        discovered.extend(
                            self._discover_in_directory(dir_path, app_config.name, dir_name)
                        )
            else:
                # Handle file patterns (e.g., "tools.py")
                file_path = app_path / pattern
                if file_path.exists():
                    module_name = pattern.replace(".py", "")
                    discovered.extend(
                        self._discover_in_file(file_path, app_config.name, module_name)
                    )
        
        return discovered
    
    def _discover_in_file(self, file_path: Path, app_name: str, module_name: str) -> List[Type]:
        """Discover tools in a Python file."""
        full_module = f"{app_name}.{module_name}"
        
        if full_module in self._discovered_modules:
            return []
        
        try:
            logger.debug(f"📄 Loading module: {full_module}")
            module = importlib.import_module(full_module)
            self._discovered_modules.add(full_module)
            
            tools = self._extract_tools_from_module(module)
            if tools:
                logger.info(f"✅ Found {len(tools)} tool(s) in {full_module}")
            
            return tools
            
        except ImportError as e:
            logger.warning(f"⚠️  Cannot import {full_module}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading {full_module}: {e}")
            self._discovery_errors.append(e)
            return []
    
    def _discover_in_directory(self, directory: Path, app_name: str, dir_name: str) -> List[Type]:
        """Discover tools in a directory."""
        discovered = []
        
        logger.debug(f"📁 Scanning directory: {directory}")
        
        for file_path in directory.glob("*.py"):
            if file_path.stem.startswith("_"):
                continue
            
            full_module = f"{app_name}.{dir_name}.{file_path.stem}"
            
            if full_module in self._discovered_modules:
                continue
            
            try:
                module = importlib.import_module(full_module)
                self._discovered_modules.add(full_module)
                tools = self._extract_tools_from_module(module)
                discovered.extend(tools)
                
                if tools:
                    logger.info(f"✅ Found {len(tools)} tool(s) in {full_module}")
                    
            except Exception as e:
                logger.error(f"❌ Error loading {full_module}: {e}")
                self._discovery_errors.append(e)
        
        return discovered
    
    def _extract_tools_from_module(self, module) -> List[Type]:
        """Extract tool classes from a module."""
        tools = []
        
        for name, obj in inspect.getmembers(module):
            if self._is_mcp_tool(obj):
                logger.debug(f"🎯 Found tool class: {name}")
                tools.append(obj)
        
        return tools
    
    def _is_mcp_tool(self, obj: Any) -> bool:
        """Check if object is an MCP tool."""
        return (
            inspect.isclass(obj)
            and hasattr(obj, "execute")
            and inspect.iscoroutinefunction(obj.execute)
            and hasattr(obj, "_mcp_tool_registered")
            and not obj.__name__.startswith("_")
        )
    
    def get_discovery_errors(self) -> List[Exception]:
        """Get list of discovery errors."""
        return self._discovery_errors.copy()
    
    def get_discovered_modules(self) -> Set[str]:
        """Get set of discovered module names."""
        return self._discovered_modules.copy()