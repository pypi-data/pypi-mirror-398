"""
Cursor state.vscdb Parser

This module provides the core parsing functionality for extracting
conversations from Cursor's SQLite database.
"""

import sqlite3
import json
import re
import logging
from pathlib import Path
from collections import defaultdict
from urllib.parse import unquote
from typing import Iterator

from .tool_calls import format_tool_call, get_approval_stats, format_approval_summary

logger = logging.getLogger(__name__)


class CursorDataParser:
    """
    Parser for Cursor's state.vscdb database.
    
    Usage:
        parser = CursorDataParser(db_path)
        parser.export_all(output_dir)
    """
    
    def __init__(self, db_path: Path | str):
        """
        Initialize the parser with a database path.
        
        Args:
            db_path: Path to the state.vscdb file
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        self._conn: sqlite3.Connection | None = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def connect(self) -> sqlite3.Connection:
        """Connect to the SQLite database."""
        if self._conn is None:
            logger.debug(f"Connecting to database: {self.db_path}")
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
    
    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            return self.connect()
        return self._conn
    
    def get_key_prefixes(self) -> dict[str, int]:
        """Get all unique key prefixes and their counts."""
        cursor = self.conn.execute("""
            SELECT
                CASE
                    WHEN instr(key, ':') > 0 THEN substr(key, 1, instr(key, ':') - 1)
                    ELSE key
                END as prefix,
                COUNT(*) as count
            FROM cursorDiskKV
            GROUP BY prefix
            ORDER BY count DESC
        """)
        return dict(cursor.fetchall())
    
    def get_bubble_stats(self) -> dict:
        """Get statistics about bubbleId entries (conversation messages)."""
        cursor = self.conn.execute("""
            SELECT
                json_extract(value, '$.type') as type,
                COUNT(*) as count
            FROM cursorDiskKV
            WHERE key LIKE 'bubbleId:%'
            GROUP BY type
        """)
        type_counts = dict(cursor.fetchall())

        # Get unique conversations (by first UUID in key)
        cursor = self.conn.execute("""
            SELECT COUNT(DISTINCT substr(key, 10, 36))
            FROM cursorDiskKV
            WHERE key LIKE 'bubbleId:%'
        """)
        conversation_count = cursor.fetchone()[0]

        return {
            "human_messages": type_counts.get(1, 0),
            "assistant_messages": type_counts.get(2, 0),
            "total_messages": sum(type_counts.values()),
            "conversations": conversation_count,
        }
    
    def get_session_names(self) -> dict[str, str]:
        """Get session/conversation names from composerData."""
        cursor = self.conn.execute("""
            SELECT
                json_extract(value, '$.composerId') as composer_id,
                json_extract(value, '$.name') as name,
                json_extract(value, '$.text') as text
            FROM cursorDiskKV
            WHERE key LIKE 'composerData:%'
        """)

        names = {}
        for composer_id, name, text in cursor.fetchall():
            if composer_id:
                if name:
                    names[composer_id] = name
                elif text:
                    # Use first 50 chars of initial prompt as fallback name
                    names[composer_id] = text[:50].replace("\n", " ").strip()

        return names
    
    def get_all_conversations(self) -> dict[str, dict]:
        """
        Get all conversations grouped by project.
        Returns: {project_name: {conv_id: [messages]}}
        """
        cursor = self.conn.execute("""
            SELECT
                key,
                value
            FROM cursorDiskKV
            WHERE key LIKE 'bubbleId:%'
            ORDER BY json_extract(value, '$.createdAt') ASC
        """)

        # First pass: group all messages by conversation ID
        conversations = defaultdict(list)
        conv_workspaces = {}  # Track workspace for each conversation

        for key, value in cursor.fetchall():
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                continue

            # Extract conversation ID from key: bubbleId:{conv_id}:{msg_id}
            parts = key.split(":")
            if len(parts) >= 2:
                conv_id = parts[1]
            else:
                continue

            conversations[conv_id].append(data)

            # Track workspace - use the first non-empty one we find for this conversation
            if conv_id not in conv_workspaces:
                workspace = data.get("workspaceUris")
                if workspace and workspace != "[]":
                    conv_workspaces[conv_id] = workspace

        # Second pass: group conversations by project
        projects = defaultdict(dict)

        for conv_id, messages in conversations.items():
            # Get project name from tracked workspace, or "unknown"
            workspace = conv_workspaces.get(conv_id)
            project = extract_project_name(workspace)
            projects[project][conv_id] = messages

        return dict(projects)
    
    def export_all(self, output_dir: Path | str) -> int:
        """
        Export all conversations to text files organized by project.
        
        Args:
            output_dir: Directory to write output files
            
        Returns:
            Number of files exported
        """
        output_dir = Path(output_dir)
        
        logger.info("Exporting conversations...")

        # Get session names for better file naming
        session_names = self.get_session_names()

        # Get all conversations
        projects = self.get_all_conversations()

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        total_files = 0

        for project_name, conversations in projects.items():
            # Create project directory
            project_dir = output_dir / sanitize_filename(project_name)
            project_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"  Project: {project_name} ({len(conversations)} conversations)")

            for conv_id, messages in conversations.items():
                if not messages:
                    continue

                # Get session name
                session_name = session_names.get(conv_id, "")

                # Create filename from timestamp and session name
                first_msg = messages[0]
                timestamp = (
                    first_msg.get("createdAt", "")[:19].replace(":", "-").replace("T", "_")
                )

                if session_name:
                    filename = f"{timestamp}_{sanitize_filename(session_name)}.txt"
                else:
                    filename = f"{timestamp}_{conv_id[:8]}.txt"

                # Format and write
                content = format_conversation(messages, session_name or conv_id[:8])
                filepath = project_dir / filename
                filepath.write_text(content, encoding="utf-8")
                total_files += 1

        logger.info(f"Exported {total_files} files to {output_dir}")
        return total_files
    
    def print_summary(self):
        """Print a summary of the database contents."""
        prefixes = self.get_key_prefixes()
        stats = self.get_bubble_stats()
        
        print(f"\n{'=' * 60}")
        print("  DATABASE SUMMARY")
        print(f"{'=' * 60}")
        print(f"\nDatabase: {self.db_path}")
        print(f"\nKey types found: {len(prefixes)}")
        
        for prefix, count in list(prefixes.items())[:10]:
            if prefix:
                print(f"  {prefix:40} {count:>6} rows")
        
        print(f"\nConversation messages:")
        print(f"  Total messages:     {stats['total_messages']:,}")
        print(f"  Human (type=1):     {stats['human_messages']:,}")
        print(f"  Assistant (type=2): {stats['assistant_messages']:,}")
        print(f"  Conversations:      {stats['conversations']}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def extract_project_name(workspace_uris: str | list | None) -> str:
    """Extract a clean project name from workspace URIs."""
    if not workspace_uris:
        return "unknown"

    # Parse if string
    if isinstance(workspace_uris, str):
        try:
            workspace_uris = json.loads(workspace_uris)
        except json.JSONDecodeError:
            return "unknown"

    if not workspace_uris or not isinstance(workspace_uris, list):
        return "unknown"

    uri = workspace_uris[0]
    # Handle file:// URIs
    if uri.startswith("file://"):
        path = uri.replace("file://", "")
        return Path(unquote(path)).name
    # Handle vscode-remote URIs
    elif "vscode-remote://" in uri:
        # Extract the path part after the host
        match = re.search(r"/workspace/([^/]+)", uri)
        if match:
            return match.group(1)
        match = re.search(r"%2F([^%/]+)$", uri)
        if match:
            return unquote(match.group(1))

    return "unknown"


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("._")
    return name[:100] if name else "untitled"


def format_message(data: dict) -> str:
    """Format a single message for text output."""
    lines = []

    msg_type = "HUMAN" if data.get("type") == 1 else "ASSISTANT"
    created_at = data.get("createdAt", "")

    # Header
    lines.append(f"\n{'─' * 70}")
    lines.append(f"[{msg_type}] {created_at}")

    # Model info (for assistant)
    if data.get("modelInfo"):
        lines.append(f"Model: {data['modelInfo'].get('modelName', 'unknown')}")

    # Token count
    if data.get("tokenCount"):
        tc = data["tokenCount"]
        if tc.get("inputTokens") or tc.get("outputTokens"):
            lines.append(
                f"Tokens: in={tc.get('inputTokens', 0)}, out={tc.get('outputTokens', 0)}"
            )

    lines.append("─" * 70)

    # Thinking block
    if data.get("thinking") and data["thinking"].get("text"):
        lines.append("\n<THINKING>")
        lines.append(data["thinking"]["text"])
        lines.append("</THINKING>")

    # Main text
    if data.get("text"):
        lines.append("\n" + data["text"])

    # Tool call - delegate to tool_calls module
    if data.get("toolFormerData") and data["toolFormerData"].get("name"):
        lines.extend(format_tool_call(data["toolFormerData"]))

    # Code blocks
    if data.get("codeBlocks"):
        for i, block in enumerate(data["codeBlocks"], 1):
            lines.append(f"\n<CODE_BLOCK {i}>")
            if isinstance(block, dict):
                if block.get("code"):
                    lines.append(
                        block["code"][:1000]
                        + ("..." if len(block.get("code", "")) > 1000 else "")
                    )
                elif block.get("content"):
                    lines.append(
                        block["content"][:1000]
                        + ("..." if len(block.get("content", "")) > 1000 else "")
                    )
            else:
                lines.append(str(block)[:1000])
            lines.append("</CODE_BLOCK>")

    # Suggested diffs
    if data.get("assistantSuggestedDiffs"):
        for diff in data["assistantSuggestedDiffs"]:
            lines.append(f'\n<DIFF file="{diff.get("uri", "unknown")}">')
            if diff.get("text"):
                lines.append(
                    diff["text"][:500]
                    + ("..." if len(diff.get("text", "")) > 500 else "")
                )
            lines.append("</DIFF>")

    # Attached context
    if data.get("attachedCodeChunks"):
        lines.append(f"\n[Attached {len(data['attachedCodeChunks'])} code chunks]")

    return "\n".join(lines)


def format_conversation(messages: list[dict], session_name: str = "") -> str:
    """Format a full conversation for text output."""
    lines = []

    # Calculate approval stats upfront
    approval_stats = get_approval_stats(messages)

    # Header
    lines.append("=" * 70)
    lines.append(f"CONVERSATION: {session_name or 'Untitled'}")
    lines.append(f"Messages: {len(messages)}")
    if messages:
        first_ts = messages[0].get("createdAt", "")
        last_ts = messages[-1].get("createdAt", "")
        lines.append(f"Period: {first_ts} to {last_ts}")

    # Add quick approval summary in header if there were changes
    if approval_stats["total_changes_proposed"] > 0:
        approved = approval_stats["approved"]
        rejected = approval_stats["rejected"]
        total = approval_stats["total_changes_proposed"]
        lines.append(f"Changes: {approved}/{total} approved, {rejected} rejected")

    lines.append("=" * 70)

    # Messages
    for msg in messages:
        lines.append(format_message(msg))

    # Detailed approval summary at end
    lines.extend(format_approval_summary(approval_stats))

    lines.append("\n" + "=" * 70)
    lines.append("END OF CONVERSATION")
    lines.append("=" * 70)

    return "\n".join(lines)


# Convenience functions for direct usage
def get_all_conversations(db_path: Path | str) -> dict[str, dict]:
    """Get all conversations from a database file."""
    with CursorDataParser(db_path) as parser:
        return parser.get_all_conversations()


def get_session_names(db_path: Path | str) -> dict[str, str]:
    """Get session names from a database file."""
    with CursorDataParser(db_path) as parser:
        return parser.get_session_names()

