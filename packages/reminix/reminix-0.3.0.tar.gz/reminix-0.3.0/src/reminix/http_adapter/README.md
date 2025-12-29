# Reminix HTTP Adapter

HTTP adapter for running Reminix handlers locally. This package provides an HTTP server that can load and execute Python handlers, making them accessible via REST API.

## Installation

```bash
pip install reminix
# or
poetry add reminix
```

## Quick Start

### 1. Create a Handler

Create a file `my_handler.py`:

```python
from reminix.runtime.types import AgentHandler, Context, Request, Response, Message

def chatbot(context: Context, request: Request) -> Response:
    last_message = request.messages[-1] if request.messages else None
    return Response(
        messages=[
            Message(
                role="assistant",
                content=f"You said: {last_message.content if last_message else 'Hello!'}",
            )
        ],
        metadata={},
    )

# Export agents, tools, and prompts
agents = {
    "chatbot": chatbot,
}
```

### 2. Start the Server

```bash
# Using poetry (from project root)
poetry run python -m reminix.http_adapter serve examples/basic_handler.py

# Or using python directly (if installed)
python -m reminix.http_adapter serve my_handler.py
```

### 3. Test the Handler

```bash
# Health check
curl http://localhost:3000/health

# Invoke the agent
curl -X POST http://localhost:3000/agents/chatbot/invoke \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## Usage

### Command Line

```bash
# Basic usage
python -m reminix.http_adapter serve <handler-path> [options]

# Options
--port <number>    Port to listen on (default: 3000)
--host <string>    Host to listen on (default: localhost)

# Examples
python -m reminix.http_adapter serve ./my_handler.py
python -m reminix.http_adapter serve ./my_handler.py --port 8080
python -m reminix.http_adapter serve ./my_handler --host 0.0.0.0
```

### Programmatic API

```python
from reminix.http_adapter import start_server, ServerOptions

# Start server with default options
start_server('./my_handler.py')

# Start server with custom options
options = ServerOptions(
    port=8080,
    host='0.0.0.0',
    context=lambda req: {
        'chat_id': req.headers.get('X-Chat-Id', 'default'),
        # ... other context properties
    },
)
start_server('./my_handler.py', options)
```

## Handler Formats

### Single File Handler

Export `agents`, `tools`, and/or `prompts`:

```python
from reminix.runtime.types import AgentHandler, ToolHandler, Context, Request, Response

def chatbot(context: Context, request: Request) -> Response:
    return Response(messages=[], metadata={})

def calculator(context: Context, request: Request) -> Response:
    return Response(messages=[], metadata={})

# Export handlers
agents = {
    "chatbot": chatbot,
}

tools = {
    "calculator": calculator,
}

prompts = {
    "system": "You are a helpful assistant.",
}
```

### Directory-Based Handler (Auto-Discovery)

Organize handlers in a directory structure:

```
my_handler/
  agents/
    chatbot.py      # def chatbot(context, request): ...
    assistant.py    # def assistant(context, request): ...
  tools/
    search.py       # def search(context, request): ...
    weather.py      # def weather(context, request): ...
  prompts/
    system.py       # system = {...}
```

The adapter will automatically discover and load all handlers from this structure.

**Note:** `__init__.py` files are automatically skipped during discovery.

## API Endpoints

### Health Check

```http
GET /health
```

Returns:
```json
{
  "status": "ok",
  "agents": ["chatbot", "assistant"],
  "tools": ["search", "weather"],
  "prompts": ["system"]
}
```

### Invoke Agent

```http
POST /agents/:agentId/invoke
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "metadata": {
    "chatId": "chat-123"
  }
}
```

### Invoke Tool

```http
POST /tools/:toolId/invoke
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "5 + 3"
    }
  ]
}
```

## Handler Interface

Handlers receive a `Context` and `Request`, and return a `Response`:

```python
from reminix.runtime.types import AgentHandler, Context, Request, Response, Message

def my_agent(context: Context, request: Request) -> Response:
    # Access context
    chat_id = context.chat_id
    memory = context.memory
    
    # Access request
    messages = request.messages
    metadata = request.metadata
    
    # Return response
    return Response(
        messages=[
            Message(
                role="assistant",
                content="Response here",
            )
        ],
        metadata={"tokensUsed": 100},
        tool_calls=[],  # Optional
        state_updates={},  # Optional
    )
```

Handlers can be either synchronous or asynchronous:

```python
import asyncio
from reminix.runtime.types import AgentHandler, Context, Request, Response

# Synchronous handler
def sync_handler(context: Context, request: Request) -> Response:
    return Response(messages=[], metadata={})

# Asynchronous handler
async def async_handler(context: Context, request: Request) -> Response:
    await asyncio.sleep(0.1)  # Simulate async work
    return Response(messages=[], metadata={})
```


## API Reference

### `start_server(handler_path, options=None)`

Start an HTTP server for the given handler.

**Parameters:**
- `handler_path` (str): Path to handler file or directory
- `options` (ServerOptions, optional):
  - `port` (int): Port to listen on (default: 3000)
  - `host` (str): Host to listen on (default: 'localhost')
  - `context` (Callable): Custom context provider

**Returns:** `None`

### `load_handler(handler_path)`

Load a handler from a file.

**Parameters:**
- `handler_path` (str): Path to handler file

**Returns:** `LoadedHandler`

### `discover_registry(handler_path)`

Auto-discover handlers from a directory structure.

**Parameters:**
- `handler_path` (str): Path to handler directory

**Returns:** `Registry`

### `convert_http_to_request(http_request)`

Convert HTTP request to handler Request format.

**Parameters:**
- `http_request` (HTTPRequest): HTTP request object

**Returns:** `Request`

### `convert_response_to_http(handler_res, http_response)`

Convert handler Response to HTTP response.

**Parameters:**
- `handler_res` (Response): Handler response
- `http_response` (HTTPResponse): HTTP response object

**Returns:** `None`

## Python Version

Requires Python 3.10 or higher.

## License

MIT

## Links

- [GitHub Repository](https://github.com/reminix-ai/reminix-python)
- [Documentation](https://docs.reminix.com)

