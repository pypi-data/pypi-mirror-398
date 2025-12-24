"""
Tool call formatting handlers for Cursor state.vscdb export.

Each handler extracts and formats the relevant information from a tool call,
including both the arguments (what was requested) and the result (what was returned).
"""

import json
from typing import Any


def truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate text to max_len, adding suffix if truncated."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def parse_json_safe(data: str | dict | None) -> dict | None:
    """Safely parse JSON string to dict."""
    if data is None:
        return None
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


# =============================================================================
# ARGUMENT HANDLERS - Extract key info from rawArgs
# =============================================================================


def format_args_read_file(args: dict) -> list[str]:
    """Format read_file arguments."""
    lines = []
    if args.get("target_file"):
        lines.append(f"  File: {args['target_file']}")
    return lines


def format_args_read_file_v2(args: dict) -> list[str]:
    """Format read_file_v2 arguments."""
    return format_args_read_file(args)


def format_args_write(args: dict) -> list[str]:
    """Format write arguments."""
    lines = []
    if args.get("target_file"):
        lines.append(f"  File: {args['target_file']}")
    if args.get("contents"):
        lines.append(f"  Content length: {len(args['contents'])} chars")
    return lines


def format_args_edit_file_v2(args: dict) -> list[str]:
    """Format edit_file_v2 arguments."""
    lines = []
    if args.get("target_file"):
        lines.append(f"  File: {args['target_file']}")
    return lines


def format_args_search_replace(args: dict) -> list[str]:
    """Format search_replace arguments."""
    lines = []
    if args.get("target_file") or args.get("file_path"):
        lines.append(f"  File: {args.get('target_file') or args.get('file_path')}")
    if args.get("old_string"):
        old = truncate(args["old_string"], 200)
        lines.append(f"  Old: {old}")
    if args.get("new_string"):
        new = truncate(args["new_string"], 200)
        lines.append(f"  New: {new}")
    return lines


def format_args_apply_patch(args: dict) -> list[str]:
    """Format apply_patch arguments - the patch itself is in rawArgs as string."""
    # apply_patch rawArgs is just the patch string directly
    return []  # We'll show the patch in the main format


def format_args_delete_file(args: dict) -> list[str]:
    """Format delete_file arguments."""
    lines = []
    if args.get("target_file"):
        lines.append(f"  File: {args['target_file']}")
    return lines


def format_args_list_dir(args: dict) -> list[str]:
    """Format list_dir arguments."""
    lines = []
    if args.get("relative_dir_path"):
        lines.append(f"  Path: {args['relative_dir_path']}")
    elif args.get("target_directory"):
        lines.append(f"  Path: {args['target_directory']}")
    return lines


def format_args_list_dir_v2(args: dict) -> list[str]:
    """Format list_dir_v2 arguments."""
    return format_args_list_dir(args)


def format_args_run_terminal_cmd(args: dict) -> list[str]:
    """Format run_terminal_cmd arguments."""
    lines = []
    if args.get("command"):
        lines.append(f"  Command: {truncate(args['command'], 500)}")
    return lines


def format_args_run_terminal_command_v2(args: dict) -> list[str]:
    """Format run_terminal_command_v2 arguments."""
    return format_args_run_terminal_cmd(args)


def format_args_grep(args: dict) -> list[str]:
    """Format grep arguments."""
    lines = []
    if args.get("pattern"):
        lines.append(f"  Pattern: {args['pattern']}")
    if args.get("path"):
        lines.append(f"  Path: {args['path']}")
    return lines


def format_args_rg(args: dict) -> list[str]:
    """Format rg/ripgrep arguments."""
    return format_args_grep(args)


def format_args_ripgrep_raw_search(args: dict) -> list[str]:
    """Format ripgrep_raw_search arguments."""
    return format_args_grep(args)


def format_args_glob_file_search(args: dict) -> list[str]:
    """Format glob_file_search arguments."""
    lines = []
    if args.get("glob_pattern"):
        lines.append(f"  Pattern: {args['glob_pattern']}")
    if args.get("target_directory"):
        lines.append(f"  Directory: {args['target_directory']}")
    return lines


def format_args_file_search(args: dict) -> list[str]:
    """Format file_search arguments."""
    lines = []
    if args.get("query"):
        lines.append(f"  Query: {args['query']}")
    return lines


def format_args_codebase_search(args: dict) -> list[str]:
    """Format codebase_search arguments."""
    lines = []
    if args.get("query"):
        lines.append(f"  Query: {args['query']}")
    if args.get("target_directories"):
        lines.append(f"  Directories: {', '.join(args['target_directories'])}")
    if args.get("explanation"):
        lines.append(f"  Explanation: {truncate(args['explanation'], 150)}")
    return lines


def format_args_web_search(args: dict) -> list[str]:
    """Format web_search arguments."""
    lines = []
    if args.get("search_term"):
        lines.append(f"  Search: {args['search_term']}")
    if args.get("explanation"):
        lines.append(f"  Explanation: {truncate(args['explanation'], 150)}")
    return lines


def format_args_read_lints(args: dict) -> list[str]:
    """Format read_lints arguments."""
    lines = []
    if args.get("paths"):
        paths = args["paths"]
        if isinstance(paths, list):
            lines.append(f"  Paths: {', '.join(str(p) for p in paths[:5])}")
    return lines


def format_args_todo_write(args: dict) -> list[str]:
    """Format todo_write arguments."""
    lines = []
    if args.get("todos"):
        todos = args["todos"]
        for todo in todos[:5]:
            status = todo.get("status", "?")
            content = truncate(todo.get("content", ""), 80)
            lines.append(f"  [{status}] {content}")
    return lines


def format_args_ask_question(args: dict) -> list[str]:
    """Format ask_question arguments."""
    lines = []
    if args.get("title"):
        lines.append(f"  Title: {args['title']}")
    if args.get("questions"):
        for q in args["questions"][:3]:
            prompt = truncate(q.get("prompt", ""), 150)
            lines.append(f"  Q: {prompt}")
            if q.get("options"):
                for opt in q["options"][:4]:
                    label = truncate(opt.get("label", ""), 80)
                    lines.append(f"    - [{opt.get('id', '?')}] {label}")
    elif args.get("question"):
        lines.append(f"  Question: {truncate(args['question'], 200)}")
    return lines


def format_args_create_plan(args: dict) -> list[str]:
    """Format create_plan arguments."""
    lines = []
    if args.get("plan"):
        lines.append(f"  Plan: {truncate(args['plan'], 300)}")
    return lines


def format_args_mcp_tool(args: dict) -> list[str]:
    """Format MCP tool arguments."""
    lines = []
    # MCP tools have varying structures, show a summary
    for key, value in list(args.items())[:3]:
        if isinstance(value, str):
            lines.append(f"  {key}: {truncate(value, 100)}")
    return lines


# =============================================================================
# RESULT HANDLERS - Extract key info from result
# =============================================================================


def format_result_read_file(result: dict) -> list[str]:
    """Format read_file result - file contents."""
    lines = []
    if result.get("contents"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["contents"], 2000))
        lines.append("  </OUTPUT>")
    return lines


def format_result_read_file_v2(result: dict) -> list[str]:
    """Format read_file_v2 result."""
    return format_result_read_file(result)


def format_result_write(result: dict) -> list[str]:
    """Format write result - shows diff of what was written."""
    lines = []
    if result.get("diff") and result["diff"].get("chunks"):
        lines.append("\n  <OUTPUT>")
        for chunk in result["diff"]["chunks"][:3]:
            if chunk.get("diffString"):
                lines.append(truncate(chunk["diffString"], 500))
        lines.append("  </OUTPUT>")
    elif result.get("resultForModel"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["resultForModel"], 200))
        lines.append("  </OUTPUT>")
    return lines


def format_result_edit_file_v2(result: dict) -> list[str]:
    """Format edit_file_v2 result."""
    return format_result_write(result)


def format_result_search_replace(result: dict) -> list[str]:
    """Format search_replace result - shows diff."""
    lines = []
    if result.get("diff") and result["diff"].get("chunks"):
        lines.append("\n  <OUTPUT>")
        for chunk in result["diff"]["chunks"][:3]:
            if chunk.get("diffString"):
                lines.append(truncate(chunk["diffString"], 400))
        lines.append("  </OUTPUT>")
    return lines


def format_result_apply_patch(result: dict) -> list[str]:
    """Format apply_patch result."""
    lines = []
    if result.get("resultForModel"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["resultForModel"], 300))
        lines.append("  </OUTPUT>")
    elif result.get("diff") and result["diff"].get("chunks"):
        lines.append("\n  <OUTPUT>")
        for chunk in result["diff"]["chunks"][:3]:
            if chunk.get("diffString"):
                lines.append(truncate(chunk["diffString"], 400))
        lines.append("  </OUTPUT>")
    return lines


def format_result_delete_file(result: dict) -> list[str]:
    """Format delete_file result."""
    lines = []
    if result.get("fileDeletedSuccessfully"):
        lines.append("\n  <OUTPUT>")
        lines.append("  File deleted successfully")
        lines.append("  </OUTPUT>")
    return lines


def format_result_list_dir(result: dict) -> list[str]:
    """Format list_dir result - directory tree."""
    lines = []
    if result.get("directoryTreeRoot"):
        tree = result["directoryTreeRoot"]
        lines.append("\n  <OUTPUT>")
        lines.append(f"  Directory: {tree.get('absPath', 'unknown')}")
        if tree.get("childrenDirs"):
            dirs = [
                d.get("absPath", "").split("/")[-1]
                for d in tree["childrenDirs"][:10]
                if d.get("absPath")
            ]
            if dirs:
                lines.append(f"  Subdirs: {', '.join(dirs)}")
        if tree.get("childrenFiles"):
            files = [
                f.get("name", "") for f in tree["childrenFiles"][:15] if f.get("name")
            ]
            if files:
                lines.append(f"  Files: {', '.join(files)}")
        lines.append("  </OUTPUT>")
    return lines


def format_result_list_dir_v2(result: dict) -> list[str]:
    """Format list_dir_v2 result."""
    return format_result_list_dir(result)


def format_result_run_terminal_cmd(result: dict) -> list[str]:
    """Format run_terminal_cmd result - command output."""
    lines = []
    if result.get("output"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["output"], 1500))
        lines.append("  </OUTPUT>")
    return lines


def format_result_run_terminal_command_v2(result: dict) -> list[str]:
    """Format run_terminal_command_v2 result."""
    return format_result_run_terminal_cmd(result)


def format_result_grep(result: dict) -> list[str]:
    """Format grep result."""
    lines = []
    if result.get("success"):
        success = result["success"]
        lines.append("\n  <OUTPUT>")
        if success.get("workspaceResults"):
            for ws, data in success["workspaceResults"].items():
                if data.get("content") and data["content"].get("matches"):
                    for match in data["content"]["matches"][:5]:
                        file = match.get("file", "")
                        for m in match.get("matches", [])[:3]:
                            line_num = m.get("lineNumber", "?")
                            content = truncate(m.get("content", ""), 100)
                            lines.append(f"  {file}:{line_num}: {content}")
        lines.append("  </OUTPUT>")
    return lines


def format_result_rg(result: dict) -> list[str]:
    """Format rg/ripgrep result."""
    return format_result_grep(result)


def format_result_ripgrep_raw_search(result: dict) -> list[str]:
    """Format ripgrep_raw_search result."""
    return format_result_grep(result)


def format_result_glob_file_search(result: dict) -> list[str]:
    """Format glob_file_search result."""
    lines = []
    if result.get("files"):
        lines.append("\n  <OUTPUT>")
        files = result["files"][:20]
        for f in files:
            if isinstance(f, dict):
                lines.append(f"  {f.get('absPath', f.get('path', ''))}")
            else:
                lines.append(f"  {f}")
        lines.append("  </OUTPUT>")
    elif result.get("directories"):
        lines.append("\n  <OUTPUT>")
        for d in result["directories"][:10]:
            if isinstance(d, dict):
                lines.append(f"  {d.get('absPath', '')}")
        lines.append("  </OUTPUT>")
    return lines


def format_result_file_search(result: dict) -> list[str]:
    """Format file_search result."""
    return format_result_glob_file_search(result)


def format_result_codebase_search(result: dict) -> list[str]:
    """Format codebase_search result - code snippets."""
    lines = []
    if result.get("codeResults"):
        lines.append("\n  <OUTPUT>")
        for code_result in result["codeResults"][:3]:
            block = code_result.get("codeBlock", {})
            path = block.get("relativeWorkspacePath", "")
            contents = block.get("contents", "")
            lines.append(f"  --- {path} ---")
            lines.append(truncate(contents, 500))
        lines.append("  </OUTPUT>")
    return lines


def format_result_web_search(result: dict) -> list[str]:
    """Format web_search result."""
    lines = []
    if result.get("references"):
        lines.append("\n  <OUTPUT>")
        for ref in result["references"][:2]:
            title = ref.get("title", "")
            chunk = truncate(ref.get("chunk", ""), 600)
            lines.append(f"  --- {title} ---")
            lines.append(chunk)
        lines.append("  </OUTPUT>")
    return lines


def format_result_read_lints(result: dict) -> list[str]:
    """Format read_lints result - linter errors."""
    lines = []
    if result.get("linterErrorsByFile"):
        lines.append("\n  <OUTPUT>")
        for file_errors in result["linterErrorsByFile"][:3]:
            path = file_errors.get("relativeWorkspacePath", "")
            errors = file_errors.get("errors", [])
            for err in errors[:5]:
                msg = err.get("message", "")
                severity = err.get("severity", "").replace("DIAGNOSTIC_SEVERITY_", "")
                rng = err.get("range", {}).get("startPosition", {})
                line = rng.get("line", "?")
                lines.append(f"  {path}:{line} [{severity}] {msg}")
        lines.append("  </OUTPUT>")
    elif result.get("path"):
        # No errors case
        lines.append("\n  <OUTPUT>")
        lines.append(f"  No lint errors in {result['path']}")
        lines.append("  </OUTPUT>")
    return lines


def format_result_todo_write(result: dict) -> list[str]:
    """Format todo_write result."""
    lines = []
    if result.get("finalTodos"):
        lines.append("\n  <OUTPUT>")
        for todo in result["finalTodos"][:5]:
            status = todo.get("status", "?")
            content = truncate(todo.get("content", ""), 80)
            lines.append(f"  [{status}] {content}")
        lines.append("  </OUTPUT>")
    return lines


def format_result_ask_question(result: dict) -> list[str]:
    """Format ask_question result."""
    lines = []
    if result.get("answers"):
        lines.append("\n  <OUTPUT>")
        for ans in result["answers"]:
            qid = ans.get("questionId", "?")
            selected = ans.get("selectedOptionIds", [])
            if selected:
                lines.append(f"  {qid}: {', '.join(selected)}")
            else:
                lines.append(f"  {qid}: (no selection)")
        lines.append("  </OUTPUT>")
    elif result.get("answer"):
        lines.append("\n  <OUTPUT>")
        lines.append(f"  Answer: {truncate(result['answer'], 200)}")
        lines.append("  </OUTPUT>")
    return lines


def format_result_create_plan(result: dict) -> list[str]:
    """Format create_plan result."""
    lines = []
    if result.get("plan"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["plan"], 400))
        lines.append("  </OUTPUT>")
    return lines


def format_result_mcp_tool(result: dict) -> list[str]:
    """Format MCP tool result."""
    lines = []
    # Show a summary of the result
    result_str = json.dumps(result)[:500] if result else ""
    if result_str:
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result_str, 400))
        lines.append("  </OUTPUT>")
    return lines


def format_result_generic(result: dict) -> list[str]:
    """Generic fallback for unknown result types."""
    lines = []
    # Try common patterns
    if result.get("contents"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["contents"], 1000))
        lines.append("  </OUTPUT>")
    elif result.get("output"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(result["output"], 1000))
        lines.append("  </OUTPUT>")
    elif result.get("result"):
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(str(result["result"]), 500))
        lines.append("  </OUTPUT>")
    return lines


# =============================================================================
# HANDLER REGISTRY
# =============================================================================

ARGS_HANDLERS = {
    "read_file": format_args_read_file,
    "read_file_v2": format_args_read_file_v2,
    "write": format_args_write,
    "edit_file_v2": format_args_edit_file_v2,
    "search_replace": format_args_search_replace,
    "apply_patch": format_args_apply_patch,
    "delete_file": format_args_delete_file,
    "list_dir": format_args_list_dir,
    "list_dir_v2": format_args_list_dir_v2,
    "run_terminal_cmd": format_args_run_terminal_cmd,
    "run_terminal_command_v2": format_args_run_terminal_command_v2,
    "grep": format_args_grep,
    "rg": format_args_rg,
    "ripgrep_raw_search": format_args_ripgrep_raw_search,
    "glob_file_search": format_args_glob_file_search,
    "file_search": format_args_file_search,
    "codebase_search": format_args_codebase_search,
    "web_search": format_args_web_search,
    "read_lints": format_args_read_lints,
    "todo_write": format_args_todo_write,
    "ask_question": format_args_ask_question,
    "create_plan": format_args_create_plan,
}

RESULT_HANDLERS = {
    "read_file": format_result_read_file,
    "read_file_v2": format_result_read_file_v2,
    "write": format_result_write,
    "edit_file_v2": format_result_edit_file_v2,
    "search_replace": format_result_search_replace,
    "apply_patch": format_result_apply_patch,
    "delete_file": format_result_delete_file,
    "list_dir": format_result_list_dir,
    "list_dir_v2": format_result_list_dir_v2,
    "run_terminal_cmd": format_result_run_terminal_cmd,
    "run_terminal_command_v2": format_result_run_terminal_command_v2,
    "grep": format_result_grep,
    "rg": format_result_rg,
    "ripgrep_raw_search": format_result_ripgrep_raw_search,
    "glob_file_search": format_result_glob_file_search,
    "file_search": format_result_file_search,
    "codebase_search": format_result_codebase_search,
    "web_search": format_result_web_search,
    "read_lints": format_result_read_lints,
    "todo_write": format_result_todo_write,
    "ask_question": format_result_ask_question,
    "create_plan": format_result_create_plan,
}


# =============================================================================
# APPROVAL TRACKING
# =============================================================================

# Tools that propose changes requiring user approval
CHANGE_PROPOSING_TOOLS = {
    "write",
    "edit_file_v2",
    "search_replace",
    "apply_patch",
    "delete_file",
    "run_terminal_cmd",
    "run_terminal_command_v2",
    "create_plan",
}

# Map internal status to human-readable approval status
STATUS_DISPLAY = {
    "completed": "APPROVED",
    "cancelled": "REJECTED",
    "error": "ERROR",
    "loading": "PENDING",
}


def is_change_proposing(tool_name: str) -> bool:
    """Check if a tool proposes changes requiring user approval."""
    return tool_name in CHANGE_PROPOSING_TOOLS


def get_approval_status(tool_data: dict) -> tuple[str, str]:
    """
    Get the approval status for a tool call.

    Returns:
        (raw_status, display_status) tuple
    """
    raw_status = tool_data.get("status", "unknown")
    display_status = STATUS_DISPLAY.get(raw_status, raw_status.upper())
    return raw_status, display_status


def get_approval_stats(messages: list[dict]) -> dict:
    """
    Calculate approval statistics for a conversation.

    Args:
        messages: List of message dicts from a conversation

    Returns:
        Dict with approval stats for change-proposing tools
    """
    stats = {
        "total_changes_proposed": 0,
        "approved": 0,
        "rejected": 0,
        "errors": 0,
        "pending": 0,
        "by_tool": {},
    }

    for msg in messages:
        tool_data = msg.get("toolFormerData")
        if not tool_data:
            continue

        tool_name = tool_data.get("name")
        if not tool_name or not is_change_proposing(tool_name):
            continue

        raw_status = tool_data.get("status", "unknown")

        # Initialize tool stats if needed
        if tool_name not in stats["by_tool"]:
            stats["by_tool"][tool_name] = {"approved": 0, "rejected": 0, "errors": 0, "pending": 0}

        stats["total_changes_proposed"] += 1

        if raw_status == "completed":
            stats["approved"] += 1
            stats["by_tool"][tool_name]["approved"] += 1
        elif raw_status == "cancelled":
            stats["rejected"] += 1
            stats["by_tool"][tool_name]["rejected"] += 1
        elif raw_status == "error":
            stats["errors"] += 1
            stats["by_tool"][tool_name]["errors"] += 1
        elif raw_status == "loading":
            stats["pending"] += 1
            stats["by_tool"][tool_name]["pending"] += 1

    return stats


def format_approval_summary(stats: dict) -> list[str]:
    """
    Format approval stats as a summary block for export.

    Args:
        stats: Dict from get_approval_stats()

    Returns:
        List of formatted lines
    """
    if stats["total_changes_proposed"] == 0:
        return []

    lines = [
        "",
        "=" * 70,
        "APPROVAL SUMMARY",
        "=" * 70,
        f"Total changes proposed: {stats['total_changes_proposed']}",
        f"  ✓ Approved: {stats['approved']}",
        f"  ✗ Rejected: {stats['rejected']}",
        f"  ⚠ Errors:   {stats['errors']}",
    ]

    if stats["pending"] > 0:
        lines.append(f"  ⏳ Pending:  {stats['pending']}")

    if stats["by_tool"]:
        lines.append("")
        lines.append("By tool:")
        for tool_name, tool_stats in sorted(stats["by_tool"].items()):
            total = sum(tool_stats.values())
            approved = tool_stats["approved"]
            rejected = tool_stats["rejected"]
            lines.append(f"  {tool_name}: {approved}/{total} approved, {rejected} rejected")

    return lines


# =============================================================================
# MAIN FORMATTER
# =============================================================================


def format_tool_call(tool_data: dict) -> list[str]:
    """
    Format a complete tool call with arguments and results.

    Args:
        tool_data: The toolFormerData dict from a message

    Returns:
        List of formatted lines
    """
    tool_name = tool_data.get("name")
    if not tool_name:
        return []

    raw_status, display_status = get_approval_status(tool_data)

    # For change-proposing tools, make approval status prominent
    if is_change_proposing(tool_name):
        lines = [f'\n<TOOL_CALL name="{tool_name}" status="{raw_status}" approval="{display_status}">']
    else:
        lines = [f'\n<TOOL_CALL name="{tool_name}" status="{raw_status}">']

    # Handle apply_patch specially - rawArgs IS the patch
    if tool_name == "apply_patch":
        raw_args = tool_data.get("rawArgs", "")
        if raw_args and isinstance(raw_args, str) and raw_args.startswith("***"):
            lines.append(f"  Patch:\n{truncate(raw_args, 800)}")
    else:
        # Format arguments
        raw_args = tool_data.get("rawArgs")
        args = parse_json_safe(raw_args)
        if args:
            # Check for MCP tools
            if tool_name.startswith("mcp_"):
                lines.extend(format_args_mcp_tool(args))
            elif tool_name in ARGS_HANDLERS:
                lines.extend(ARGS_HANDLERS[tool_name](args))
            elif args.get("explanation"):
                lines.append(f"  Explanation: {truncate(args['explanation'], 200)}")

    # Format result
    raw_result = tool_data.get("result")
    result = parse_json_safe(raw_result)
    if result:
        # Check for MCP tools
        if tool_name.startswith("mcp_"):
            lines.extend(format_result_mcp_tool(result))
        elif tool_name in RESULT_HANDLERS:
            lines.extend(RESULT_HANDLERS[tool_name](result))
        else:
            lines.extend(format_result_generic(result))
    elif raw_result and isinstance(raw_result, str):
        # Plain text result
        lines.append("\n  <OUTPUT>")
        lines.append(truncate(raw_result, 500))
        lines.append("  </OUTPUT>")

    lines.append("</TOOL_CALL>")
    return lines

