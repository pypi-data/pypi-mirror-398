"""
MyCursorData - Extract and parse your Cursor IDE conversation history.

A tool to export conversations, messages, and tool calls from Cursor's
internal state.vscdb database into readable text files.
"""

__version__ = "0.1.0"

from .parser import (
    CursorDataParser,
    get_all_conversations,
    get_session_names,
    format_conversation,
)
from .discovery import discover_cursor_databases, get_default_cursor_paths

__all__ = [
    "__version__",
    "CursorDataParser",
    "get_all_conversations",
    "get_session_names", 
    "format_conversation",
    "discover_cursor_databases",
    "get_default_cursor_paths",
]

