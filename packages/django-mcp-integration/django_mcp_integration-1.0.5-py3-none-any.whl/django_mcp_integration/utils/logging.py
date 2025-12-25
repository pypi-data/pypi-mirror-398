"""Enhanced logging utilities."""
import logging
import functools
from time import time
from typing import Callable, Any
from django.conf import settings


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    level = getattr(settings, "MCP_LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, level))
    return logger


def log_tool_execution(func: Callable) -> Callable:
    """Decorator to log tool execution with timing."""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)
        tool_name = getattr(args[0], 'name', func.__name__) if args else func.__name__
        start = time()
        
        logger.info(f"⚡ Executing tool: {tool_name}")
        logger.debug(f"Arguments: args={args[1:]}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            duration = time() - start
            logger.info(f"✅ Tool {tool_name} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time() - start
            logger.error(f"❌ Tool {tool_name} failed after {duration:.3f}s: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)
        tool_name = getattr(args[0], 'name', func.__name__) if args else func.__name__
        start = time()
        
        logger.info(f"⚡ Executing tool: {tool_name}")
        logger.debug(f"Arguments: args={args[1:]}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            duration = time() - start
            logger.info(f"✅ Tool {tool_name} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time() - start
            logger.error(f"❌ Tool {tool_name} failed after {duration:.3f}s: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


import asyncio