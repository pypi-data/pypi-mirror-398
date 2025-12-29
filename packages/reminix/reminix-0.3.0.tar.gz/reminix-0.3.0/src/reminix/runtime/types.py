"""
Handler types for Reminix agents and tools
"""

from typing import Dict, List, Optional, Any, Protocol, Callable
from dataclasses import dataclass


@dataclass
class Message:
    """Message in a conversation"""

    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolCall:
    """Tool call made by an agent"""

    id: str
    name: str
    arguments: Dict[str, Any]


class MemoryStore(Protocol):
    """Memory store interface"""

    async def get(self, key: str) -> Any:
        """Get value from memory"""
        ...

    async def set(self, key: str, value: Any) -> None:
        """Set value in memory"""
        ...

    async def delete(self, key: str) -> None:
        """Delete value from memory"""
        ...

    async def clear(self) -> None:
        """Clear all memory"""
        ...


class KnowledgeBase(Protocol):
    """Knowledge base interface"""

    async def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Search knowledge base"""
        ...

    async def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add content to knowledge base"""
        ...

    async def delete(self, id: str) -> None:
        """Delete content from knowledge base"""
        ...


class ToolRegistry(Protocol):
    """Tool registry interface"""

    def get(self, name: str) -> Optional[Callable]:
        """Get tool by name"""
        ...

    def list(self) -> List[str]:
        """List all available tools"""
        ...


@dataclass
class Context:
    """Context provides persistent resources to handlers"""

    # Chat/thread identifier
    chat_id: str

    # Thread identifier (optional)
    thread_id: Optional[str] = None

    # Memory store for persistent memory
    memory: MemoryStore = None  # type: ignore

    # Knowledge base for RAG/retrieval
    knowledge_base: KnowledgeBase = None  # type: ignore

    # Available tools registry
    tools: Optional[ToolRegistry] = None

    # User identifier
    user_id: Optional[str] = None

    # Session identifier
    session_id: Optional[str] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    # Extensible for future additions
    def __getitem__(self, key: str) -> Any:
        """Allow extensible access"""
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow extensible assignment"""
        setattr(self, key, value)


@dataclass
class Request:
    """Request represents the current invocation"""

    # Conversation messages
    messages: List[Message]

    # Additional metadata for this request
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """Response from a handler"""

    # Response messages
    messages: List[Message]

    # Optional metadata (tokens, model, latency, etc.)
    metadata: Optional[Dict[str, Any]] = None

    # Tool calls made by the agent
    tool_calls: Optional[List[ToolCall]] = None

    # State updates
    state_updates: Optional[Dict[str, Any]] = None

    # Extensible for future additions
    def __getitem__(self, key: str) -> Any:
        """Allow extensible access"""
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow extensible assignment"""
        setattr(self, key, value)


# Type aliases for handler signatures
AgentHandler = Callable[[Context, Request], Any]  # Returns Response (async)
ToolHandler = Callable[[Context, Request], Any]  # Returns Response (async)
