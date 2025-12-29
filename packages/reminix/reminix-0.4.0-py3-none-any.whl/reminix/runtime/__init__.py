"""
Reminix Runtime

Core runtime for building handlers that run on Reminix.
Includes types, loader, registry, and executor utilities.
"""

from .types import (
    AgentHandler,
    Context,
    KnowledgeBase,
    MemoryStore,
    Message,
    Request,
    Response,
    ToolCall,
    ToolHandler,
    ToolRegistry,
)
from .loader import LoadedHandler, load_handler, is_file
from .registry import Registry, discover_registry
from .executor import execute_handler, execute_agent, execute_tool

__all__ = [
    # Types
    "Message",
    "ToolCall",
    "Context",
    "Request",
    "Response",
    "MemoryStore",
    "KnowledgeBase",
    "ToolRegistry",
    "AgentHandler",
    "ToolHandler",
    # Loader
    "LoadedHandler",
    "load_handler",
    "is_file",
    # Registry
    "Registry",
    "discover_registry",
    # Executor
    "execute_handler",
    "execute_agent",
    "execute_tool",
]
