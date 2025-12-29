"""
Load handler from file
"""

import importlib.util
import os
from typing import Dict, Callable, Any, Optional


class LoadedHandler:
    """Loaded handler with agents, tools, and prompts"""

    def __init__(
        self,
        agents: Optional[Dict[str, Callable]] = None,
        tools: Optional[Dict[str, Callable]] = None,
        prompts: Optional[Dict[str, Any]] = None,
    ):
        self.agents = agents or {}
        self.tools = tools or {}
        self.prompts = prompts or {}


def load_handler(handler_path: str) -> LoadedHandler:
    """
    Load handler from a file path.
    Supports Python (.py) files.

    Args:
        handler_path: Path to the handler file

    Returns:
        LoadedHandler with agents, tools, and prompts

    Raises:
        ValueError: If handler file doesn't export agents, tools, or prompts
        ImportError: If handler file cannot be loaded
    """
    try:
        # Resolve absolute path
        handler_path = os.path.abspath(handler_path)

        if not os.path.exists(handler_path):
            raise FileNotFoundError(f"Handler file not found: {handler_path}")

        if not handler_path.endswith(".py"):
            raise ValueError(f"Handler file must be a Python file (.py): {handler_path}")

        # Load module dynamically
        spec = importlib.util.spec_from_file_location("handler", handler_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load handler from: {handler_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Extract agents, tools, and prompts
        agents = getattr(module, "agents", None)
        tools = getattr(module, "tools", None)
        prompts = getattr(module, "prompts", None)

        # Validate that at least one export exists
        if not agents and not tools and not prompts:
            raise ValueError(
                f'Handler file "{handler_path}" must export at least one of: agents, tools, or prompts'
            )

        # Convert to dictionaries if they're not already
        agents_dict = agents if isinstance(agents, dict) else {}
        tools_dict = tools if isinstance(tools, dict) else {}
        prompts_dict = prompts if isinstance(prompts, dict) else {}

        return LoadedHandler(
            agents=agents_dict,
            tools=tools_dict,
            prompts=prompts_dict,
        )
    except Exception as e:
        if isinstance(e, (ValueError, ImportError, FileNotFoundError)):
            raise
        raise ImportError(f"Failed to load handler from '{handler_path}': {str(e)}") from e


def is_file(path: str) -> bool:
    """
    Check if a path is a file (not a directory).

    Args:
        path: Path to check

    Returns:
        True if path is a file, False if directory or doesn't exist
    """
    return os.path.isfile(path)
