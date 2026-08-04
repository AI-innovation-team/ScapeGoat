"""MCP server layer exposing scapegoat core abilities as tools."""

from __future__ import annotations

__all__ = ["main", "mcp"]


def __getattr__(name: str):
    if name in __all__:
        from scapegoat.mcp import server

        return getattr(server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
