"""Transitional entry point dispatching to CLI or MCP server."""

import sys

from skillport.interfaces.cli.app import app
from skillport.interfaces.mcp.server import run_server
from skillport.shared.config import Config


def main():
    args = sys.argv[1:]
    # Legacy: no args → run MCP server (backward compat)
    # Note: `skillport --reindex` is NOT supported; use `skillport serve --reindex`
    if not args:
        config = Config()
        run_server(config=config)
    else:
        app()


if __name__ == "__main__":
    main()
