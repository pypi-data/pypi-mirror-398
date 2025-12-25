"""CLI for Sonnerrise web application."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    """Main entry point for the web server."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-web",
        description="Sonnerrise web interface",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    from sonnerrise_web.app import create_app

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)

    return 0


if __name__ == "__main__":
    sys.exit(main())
