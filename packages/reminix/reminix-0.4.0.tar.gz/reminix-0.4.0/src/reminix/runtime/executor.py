"""
Core handler execution logic
"""

import asyncio
from typing import Any
from .types import Context, Request, AgentHandler, ToolHandler


def execute_handler(handler: AgentHandler | ToolHandler, context: Context, request: Request) -> Any:
    """
    Execute a handler (agent or tool), handling both sync and async handlers.

    Args:
        handler: Handler function (sync or async)
        context: Handler context
        request: Handler request

    Returns:
        Handler response
    """
    if asyncio.iscoroutinefunction(handler):
        # Async handler - run in event loop
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(handler(context, request))
        except RuntimeError:
            # No event loop running, create one
            return asyncio.run(handler(context, request))
    else:
        # Sync handler
        return handler(context, request)


def execute_agent(handler: AgentHandler, context: Context, request: Request) -> Any:
    """
    Execute an agent handler.

    Args:
        handler: Agent handler function
        context: Handler context
        request: Handler request

    Returns:
        Handler response
    """
    return execute_handler(handler, context, request)


def execute_tool(handler: ToolHandler, context: Context, request: Request) -> Any:
    """
    Execute a tool handler.

    Args:
        handler: Tool handler function
        context: Handler context
        request: Handler request

    Returns:
        Handler response
    """
    return execute_handler(handler, context, request)
