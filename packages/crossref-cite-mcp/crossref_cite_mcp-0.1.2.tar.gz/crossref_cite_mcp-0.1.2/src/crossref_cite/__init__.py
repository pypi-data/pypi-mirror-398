"""
Crossref Citation MCP Tool

A Model Context Protocol server for resolving paper citations via Crossref API.
Supports multiple output formats: CSL-JSON, BibTeX, RIS, and formatted text.
"""

from crossref_cite.server import main, mcp

__version__ = "0.1.0"
__all__ = ["main", "mcp"]
