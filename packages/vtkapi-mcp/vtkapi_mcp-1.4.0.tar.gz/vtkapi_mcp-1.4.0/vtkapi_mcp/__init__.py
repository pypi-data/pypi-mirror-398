"""
VTK API MCP Server

Provides direct access to VTK API documentation through MCP tools.
Replaces the need for API docs in RAG retrieval.
"""

__version__ = "1.4.0"

from .core import VTKAPIIndex
from .validation import VTKCodeValidator, ValidationError, ValidationResult, load_validator

# Optional: MCP server (requires mcp package)
try:
    from .server import VTKAPIMCPServer  # noqa: F401
    __all__ = [
        'VTKAPIIndex',
        'VTKCodeValidator',
        'ValidationError',
        'ValidationResult',
        'VTKAPIMCPServer',
        'load_validator',
    ]
except ImportError:
    # MCP dependencies not installed
    __all__ = [
        'VTKAPIIndex',
        'VTKCodeValidator',
        'ValidationError',
        'ValidationResult',
        'load_validator',
    ]
