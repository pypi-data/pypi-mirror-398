"""
UniProt MCP server package.

This module exposes high-level helpers for the stdio FastMCP server defined in
`uniprot_mcp.server`. The package structure follows the Solution 1 plan focused
on a direct UniProt REST integration.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("uniprot-mcp")
except PackageNotFoundError:  # pragma: no cover - handled during development
    __version__ = "0.0.0"

__all__ = ["__version__"]
