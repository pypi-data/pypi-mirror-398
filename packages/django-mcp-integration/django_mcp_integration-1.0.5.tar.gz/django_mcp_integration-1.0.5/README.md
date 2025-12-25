# Django MCP Integration

Intégration transparente de MCP (Model Context Protocol) dans Django via FastMCP.

## Installation

```bash
pip install django-mcp-integration

```

## Configuration Django

- Modifier le fichier **settings.py**
```python
# settings.py

INSTALLED_APPS = [
    # ...
    'django_mcp_integration',
]


# Optionnel

MCP_SERVER_NAME = "Mon Serveur MCP"
MCP_HOST = "localhost"
MCP_PORT = 8000
MCP_HTTP_PATH = "/mcp/"
MCP_ENABLED  = True
MCP_SERVER_INSTRUCTIONS = None
MCP_SERVER_VERSION = "1.0.0"

```

- Modifier le fichier **asgi.py**
```python
# asgi.py


import os

# from django.core.asgi import get_asgi_application
from django_mcp_integration.handlers.asgi import get_mcp_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')

application = get_mcp_asgi_application()

```

## Utiliser dans un outil

```python
# blog/tools.py or blog/mcp_tools.py
from django_mcp_integration import mcp_tool


@mcp_tool(
    name="add",
    description="make a + b",
)
async def add(a: int, b: int) -> int:
    return a + b


@mcp_tool(
    name="create_post",
    description="create post by IA"
)
class CreatePostTool:

    # optional
    def check_permission(self, obj):
        pass

    # required method
    async def execute(self, title: str, content: str):
        pass

```


## lancerment du server

```bash

uvicorn django_mcp_test.asgi:application

```

