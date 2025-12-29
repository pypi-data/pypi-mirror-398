"""
CLI entry point for Reminix HTTP adapter

Usage:
    python -m reminix.http_adapter serve <handler-path> [options]
"""

import sys
import argparse
from .server import start_server, ServerOptions


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Reminix HTTP adapter - Run handlers locally",
        prog="python -m reminix.http_adapter",
    )

    parser.add_argument(
        "command",
        choices=["serve"],
        help="Command to run",
    )

    parser.add_argument(
        "handler_path",
        help="Path to handler file or directory",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to listen on (default: 3000)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to listen on (default: localhost)",
    )

    args = parser.parse_args()

    if args.command != "serve":
        parser.print_help()
        sys.exit(1)

    try:
        options = ServerOptions(
            port=args.port,
            host=args.host,
        )

        start_server(args.handler_path, options)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
