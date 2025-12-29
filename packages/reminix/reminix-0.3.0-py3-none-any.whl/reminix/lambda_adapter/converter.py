"""
Convert between Lambda and Handler formats
"""

import json
from typing import Dict, Any
from reminix.runtime.types import Request, Response, Message
from .types import APIGatewayProxyEvent, LambdaContext


def convert_lambda_to_request(event: APIGatewayProxyEvent, context: LambdaContext) -> Request:
    """
    Convert Lambda API Gateway event to Handler Request.
    Extracts messages from Lambda event body.

    Args:
        event: AWS Lambda API Gateway event
        context: AWS Lambda context

    Returns:
        Handler Request with messages and metadata
    """
    try:
        # Parse body
        parsed_body: Dict[str, Any] = {}
        body = event.get("body")
        if body:
            try:
                parsed_body = json.loads(body)
            except json.JSONDecodeError:
                # If not JSON, treat as text
                parsed_body = {"content": body}

        # Extract messages from body
        # Expected format: { messages: List[Message] } or { message: Message } or just List[Message]
        messages: list[Message] = []

        if isinstance(parsed_body, list):
            # Body is array of messages
            messages = [Message(**msg) if isinstance(msg, dict) else msg for msg in parsed_body]
        elif isinstance(parsed_body, dict):
            if "messages" in parsed_body and isinstance(parsed_body["messages"], list):
                # Body has messages array
                messages = [
                    Message(**msg) if isinstance(msg, dict) else msg
                    for msg in parsed_body["messages"]
                ]
            elif "message" in parsed_body:
                # Body has single message
                msg = parsed_body["message"]
                messages = [Message(**msg) if isinstance(msg, dict) else msg]
            elif "content" in parsed_body or "role" in parsed_body:
                # Body is a single message object
                messages = [Message(**parsed_body)]

        # Build metadata from Lambda event
        metadata: Dict[str, Any] = {
            "requestId": context.request_id,
            "httpMethod": event.get("httpMethod"),
            "path": event.get("path"),
            "pathParameters": event.get("pathParameters"),
            "queryStringParameters": event.get("queryStringParameters"),
            "headers": event.get("headers", {}),
        }

        # Add request context info if available
        request_context = event.get("requestContext", {})
        if request_context:
            metadata["stage"] = request_context.get("stage")
            metadata["accountId"] = request_context.get("accountId")
            metadata["resourcePath"] = event.get("resource")

        # Merge any additional metadata from body
        if isinstance(parsed_body, dict) and "metadata" in parsed_body:
            metadata.update(parsed_body["metadata"])

        return Request(messages=messages, metadata=metadata)
    except Exception as e:
        raise ValueError(f"Failed to convert Lambda request: {str(e)}") from e


def convert_response_to_lambda(response: Response) -> Dict[str, Any]:
    """
    Convert Handler Response to Lambda API Gateway response.

    Args:
        response: Handler response

    Returns:
        Lambda API Gateway response
    """
    try:
        # Set status code (default 200)
        status_code = response.metadata.get("statusCode", 200) if response.metadata else 200

        # Set headers
        headers: Dict[str, str] = {"Content-Type": "application/json"}

        if response.metadata and "headers" in response.metadata:
            response_headers = response.metadata["headers"]
            if isinstance(response_headers, dict):
                for key, value in response_headers.items():
                    if isinstance(value, str):
                        headers[key] = value

        # Prepare response body
        response_body: Dict[str, Any] = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **(msg.metadata or {}),
                }
                for msg in response.messages
            ],
        }

        if response.metadata:
            response_body["metadata"] = response.metadata

        if response.tool_calls:
            response_body["toolCalls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                for tc in response.tool_calls
            ]

        if response.state_updates:
            response_body["stateUpdates"] = response.state_updates

        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(response_body),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }


def convert_error_to_lambda(error: Exception) -> Dict[str, Any]:
    """
    Convert error to Lambda error response.

    Args:
        error: Exception to convert

    Returns:
        Lambda error response
    """
    error_body = {"error": str(error)}
    # Add stack trace in debug mode
    import os

    if os.getenv("DEBUG") == "1" or os.getenv("DEBUG") == "true":
        import traceback

        error_body["stack"] = traceback.format_exc()

    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(error_body),
    }
