"""
Enhanced ASGI application supporting multiple servers (Uvicorn, Daphne, Gunicorn, runserver).
Compatible with both ..asgi:application and myproject.asgi:application
"""

from logging import getLogger

import django
from django.core.handlers.asgi import ASGIHandler
from fastmcp.server.http import StarletteWithLifespan

logger = getLogger(__name__)


class DjangoMCPApplication:
    """
    Unified ASGI application that routes requests between Django and MCP.
    Compatible with Uvicorn, Daphne, Gunicorn, and Django's runserver.
    """
    
    def __init__(self, django_app: ASGIHandler, mcp_app: StarletteWithLifespan):
        self.django_app = django_app
        self.mcp_app = mcp_app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            # 🔑 LA LIGNE QUI MANQUAIT
            await self.mcp_app(scope, receive, send)
            return

        path = scope.get("path", "")

        from ..core.conf import config

        if config.enabled and path.startswith(config.http_path):
            await self.mcp_app(scope, receive, send)
        else:
            await self.django_app(scope, receive, send)




def get_mcp_asgi_application():
    """
    Helper function to get the ASGI application.
    Can be used in custom ASGI files.
    """
    from ..core.conf import config
    from ..core.server import mcp_server
    django.setup(set_prefix=False)
    django_app = ASGIHandler()
    mcp_app = mcp_server.http_app(
        path=config.http_path,
    )
    return  DjangoMCPApplication(django_app, mcp_app)