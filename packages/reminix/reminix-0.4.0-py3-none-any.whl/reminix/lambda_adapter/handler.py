"""
Lambda handler for Reminix handlers
"""

import json
import os
import asyncio
from typing import Dict, Any
from reminix.runtime import load_handler, is_file, discover_registry, execute_handler
from reminix.runtime.types import Context, MemoryStore, KnowledgeBase
from .converter import (
    convert_lambda_to_request,
    convert_response_to_lambda,
    convert_error_to_lambda,
)
from .types import APIGatewayProxyEvent, LambdaContext

# Handler registry (loaded once per Lambda container)
agents: Dict[str, Any] = {}
tools: Dict[str, Any] = {}
initialized = False


def _create_mock_memory_store() -> MemoryStore:
    """Mock memory store for development"""
    store: Dict[str, Any] = {}

    class MockMemoryStore:
        async def get(self, key: str):
            return store.get(key)

        async def set(self, key: str, value: Any):
            store[key] = value

        async def delete(self, key: str):
            store.pop(key, None)

        async def clear(self):
            store.clear()

    return MockMemoryStore()  # type: ignore


def _create_mock_knowledge_base() -> KnowledgeBase:
    """Mock knowledge base for development"""

    class MockKnowledgeBase:
        async def search(self, query: str, options=None):
            return []

        async def add(self, content: str, metadata=None):
            pass

        async def delete(self, id: str):
            pass

    return MockKnowledgeBase()  # type: ignore


async def _initialize_handlers() -> None:
    """Initialize handlers from environment variable or default path"""
    global agents, tools, initialized
    if initialized:
        return

    handler_path = os.environ.get("HANDLER_PATH", "/var/task/handler")

    try:
        if is_file(handler_path):
            # Single file handler
            loaded = load_handler(handler_path)
            agents = loaded.agents or {}
            tools = loaded.tools or {}
        else:
            # Directory - auto-discover
            registry = discover_registry(handler_path)
            agents = registry.agents
            tools = registry.tools
    except Exception as e:
        # Log error but continue with empty handlers
        print(f"Failed to initialize handlers: {e}")
        agents = {}
        tools = {}

    initialized = True


def _create_context(event: APIGatewayProxyEvent, context: LambdaContext) -> Context:
    """
    Create handler context from Lambda event/context.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Handler context
    """
    # Extract chatId from headers, path params, query params, or request ID
    headers = event.get("headers", {})
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    chat_id = (
        headers.get("x-chat-id")
        or path_params.get("chatId")
        or query_params.get("chatId")
        or context.request_id
    )

    return Context(
        chat_id=chat_id,
        memory=_create_mock_memory_store(),
        knowledge_base=_create_mock_knowledge_base(),
        metadata={
            "requestId": context.request_id,
            "functionName": context.function_name,
            "functionVersion": context.function_version,
            "awsRequestId": context.aws_request_id,
        },
    )


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext) -> Dict[str, Any]:
    """
    Main Lambda handler.

    Args:
        event: AWS Lambda event
        context: AWS Lambda context

    Returns:
        Lambda response
    """
    try:
        # Initialize handlers (only once per container)
        if not initialized:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we can't use run_until_complete
                    # In Lambda this shouldn't happen, but handle gracefully
                    # Just skip initialization and use empty handlers
                    pass
                else:
                    loop.run_until_complete(_initialize_handlers())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(_initialize_handlers())

        # Parse route from path
        path = event.get("path", "/")
        path_parts = [p for p in path.split("/") if p]

        # Route: /agents/:agentId/invoke
        if len(path_parts) >= 3 and path_parts[0] == "agents" and path_parts[2] == "invoke":
            agent_id = path_parts[1]
            agent = agents.get(agent_id)

            if not agent:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": f"Agent not found: {agent_id}"}),
                }

            handler_context = _create_context(event, context)
            handler_request = convert_lambda_to_request(event, context)
            handler_response = execute_handler(agent, handler_context, handler_request)

            return convert_response_to_lambda(handler_response)

        # Route: /tools/:toolId/invoke
        if len(path_parts) >= 3 and path_parts[0] == "tools" and path_parts[2] == "invoke":
            tool_id = path_parts[1]
            tool = tools.get(tool_id)

            if not tool:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": f"Tool not found: {tool_id}"}),
                }

            handler_context = _create_context(event, context)
            handler_request = convert_lambda_to_request(event, context)
            handler_response = execute_handler(tool, handler_context, handler_request)

            return convert_response_to_lambda(handler_response)

        # Route: /health (health check)
        if path_parts[0] == "health" or path == "/":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "status": "ok",
                        "agents": list(agents.keys()),
                        "tools": list(tools.keys()),
                    }
                ),
            }

        # 404 for unknown routes
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not found"}),
        }
    except Exception as e:
        return convert_error_to_lambda(e)
