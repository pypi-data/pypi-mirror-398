"""
Registry for auto-discovering agents, tools, and prompts from directories
"""

import os
from typing import Dict, Callable, Any, Optional
from .loader import load_handler


class Registry:
    """Registry containing agents, tools, and prompts"""

    def __init__(
        self,
        agents: Optional[Dict[str, Callable]] = None,
        tools: Optional[Dict[str, Callable]] = None,
        prompts: Optional[Dict[str, Any]] = None,
    ):
        self.agents = agents or {}
        self.tools = tools or {}
        self.prompts = prompts or {}


def discover_registry(handler_path: str) -> Registry:
    """
    Auto-discover and load handlers from a directory structure.

    Expected structure:
        handler/
            agents/
                chatbot.py
                assistant.py
            tools/
                search.py
            prompts/
                system.py

    Args:
        handler_path: Path to the handler directory

    Returns:
        Registry with discovered agents, tools, and prompts

    Raises:
        ValueError: If handler path is not a directory or nothing is found
    """
    registry = Registry()

    try:
        handler_path = os.path.abspath(handler_path)

        if not os.path.exists(handler_path):
            raise FileNotFoundError(f"Handler path not found: {handler_path}")

        if not os.path.isdir(handler_path):
            raise ValueError(f"Handler path must be a directory: {handler_path}")

        # Discover agents
        agents_path = os.path.join(handler_path, "agents")
        if os.path.isdir(agents_path):
            agents = _load_directory(agents_path)
            registry.agents = agents

        # Discover tools
        tools_path = os.path.join(handler_path, "tools")
        if os.path.isdir(tools_path):
            tools = _load_directory(tools_path)
            registry.tools = tools

        # Discover prompts
        prompts_path = os.path.join(handler_path, "prompts")
        if os.path.isdir(prompts_path):
            prompts = _load_directory(prompts_path)
            registry.prompts = prompts

        # Validate that at least something was discovered
        if len(registry.agents) == 0 and len(registry.tools) == 0 and len(registry.prompts) == 0:
            raise ValueError(f"No agents, tools, or prompts found in directory: {handler_path}")

        return registry
    except Exception as e:
        if isinstance(e, (ValueError, FileNotFoundError)):
            raise
        raise ValueError(f"Failed to discover registry from '{handler_path}': {str(e)}") from e


def _load_directory(dir_path: str) -> Dict[str, Callable | Any]:
    """
    Load all handler files from a directory.
    Filename (without extension) becomes the key in the registry.

    Args:
        dir_path: Path to directory containing handler files

    Returns:
        Dictionary mapping handler names to handler functions
    """
    handlers: Dict[str, Callable | Any] = {}

    try:
        entries = os.listdir(dir_path)

        for entry in entries:
            full_path = os.path.join(dir_path, entry)

            # Skip if not a file
            if not os.path.isfile(full_path):
                continue

            # Only process Python files
            if not entry.endswith(".py"):
                continue

            # Skip __init__.py files
            if entry == "__init__.py":
                continue

            # Extract the key from filename (without extension)
            key = os.path.splitext(entry)[0]

            try:
                # Try loading as a handler file (expects agents/tools/prompts exports)
                loaded = load_handler(full_path)

                # Merge agents, tools, and prompts into the registry
                if loaded.agents:
                    agent_keys = list(loaded.agents.keys())
                    if len(agent_keys) == 1:
                        handlers[key] = loaded.agents[agent_keys[0]]
                    else:
                        for agent_key in agent_keys:
                            handlers[f"{key}.{agent_key}"] = loaded.agents[agent_key]

                if loaded.tools:
                    tool_keys = list(loaded.tools.keys())
                    if len(tool_keys) == 1:
                        handlers[key] = loaded.tools[tool_keys[0]]
                    else:
                        for tool_key in tool_keys:
                            handlers[f"{key}.{tool_key}"] = loaded.tools[tool_key]

                if loaded.prompts:
                    prompt_keys = list(loaded.prompts.keys())
                    if len(prompt_keys) == 1:
                        handlers[key] = loaded.prompts[prompt_keys[0]]
                    else:
                        for prompt_key in prompt_keys:
                            handlers[f"{key}.{prompt_key}"] = loaded.prompts[prompt_key]
            except (ValueError, ImportError):
                # If load_handler fails, try loading as direct export
                # This handles files that export functions directly (e.g., def chatbot(...))
                try:
                    import importlib.util

                    spec = importlib.util.spec_from_file_location("handler", full_path)
                    if spec is None or spec.loader is None:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Determine type based on directory name
                    dir_name = os.path.basename(dir_path)

                    # Check for direct exports matching the directory type
                    if dir_name == "agents":
                        # Look for exported function with same name as file, or any callable
                        exported_function = getattr(module, key, None) or getattr(
                            module, "default", None
                        )
                        if callable(exported_function):
                            handlers[key] = exported_function
                    elif dir_name == "tools":
                        exported_function = getattr(module, key, None) or getattr(
                            module, "default", None
                        )
                        if callable(exported_function):
                            handlers[key] = exported_function
                    elif dir_name == "prompts":
                        # For prompts, accept any export (function, object, string, etc.)
                        exported_value = getattr(module, key, None) or getattr(
                            module, "default", None
                        )
                        if exported_value is not None:
                            handlers[key] = exported_value
                        else:
                            # Check if module has any exports (excluding special attributes)
                            module_dict = {
                                k: v
                                for k, v in module.__dict__.items()
                                if not k.startswith("__") and k != "default"
                            }
                            if module_dict:
                                # Use the first export found
                                handlers[key] = next(iter(module_dict.values()))
                except Exception:
                    # Skip this file if both methods fail
                    continue

        return handlers
    except Exception as e:
        raise ValueError(f"Failed to load directory '{dir_path}': {str(e)}") from e
