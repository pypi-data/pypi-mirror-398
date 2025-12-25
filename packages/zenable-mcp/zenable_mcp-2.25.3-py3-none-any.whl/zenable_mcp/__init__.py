__maintainer__ = "Zenable"
__copyright__ = "(c) Zenable, Inc."
__project_name__ = "zenable_mcp"
__version__ = "2.25.3"

from zenable_mcp.client import main

# This limits a `from zenable_mcp import *` to only get the main function/entrypoint
__all__ = ["main"]
