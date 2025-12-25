"""Tool usage formatting utilities for Claude Agent SDK.

This module provides formatting functions to convert Claude Agent SDK tool usage
into human-readable messages for display in the Vicoa dashboard.

Based on: https://platform.claude.com/docs/en/agent-sdk/python#tool-input-output-types
"""

from typing import Any, Dict


def _format_edit_diff(
    old_string: str, new_string: str, replace_all: bool = False
) -> str:
    """Generate a formatted diff for Edit operations.

    Args:
        old_string: The original content being replaced
        new_string: The new content
        replace_all: Whether this is a replace-all operation

    Returns:
        Formatted diff as a markdown code block
    """
    diff_lines = []

    if replace_all:
        diff_lines.append("*Replacing all occurrences*")
        diff_lines.append("")

    # Handle empty old_string (new content addition)
    if not old_string and new_string:
        diff_lines.append("```diff")
        for line in new_string.splitlines():
            diff_lines.append(f"+ {line}")
        diff_lines.append("```")
    # Handle empty new_string (content deletion)
    elif old_string and not new_string:
        diff_lines.append("```diff")
        for line in old_string.splitlines():
            diff_lines.append(f"- {line}")
        diff_lines.append("```")
    # Handle replacement - show context-aware diff
    elif old_string and new_string:
        old_lines = old_string.splitlines()
        new_lines = new_string.splitlines()

        # Find common prefix
        common_prefix = []
        for i in range(min(len(old_lines), len(new_lines))):
            if old_lines[i] == new_lines[i]:
                common_prefix.append(old_lines[i])
            else:
                break

        # Find common suffix
        old_remaining = old_lines[len(common_prefix) :]
        new_remaining = new_lines[len(common_prefix) :]
        common_suffix = []

        if old_remaining and new_remaining:
            for i in range(1, min(len(old_remaining), len(new_remaining)) + 1):
                if old_remaining[-i] == new_remaining[-i]:
                    common_suffix.insert(0, old_remaining[-i])
                else:
                    break

        # Get the actual changed lines
        changed_old = (
            old_remaining[: len(old_remaining) - len(common_suffix)]
            if common_suffix
            else old_remaining
        )
        changed_new = (
            new_remaining[: len(new_remaining) - len(common_suffix)]
            if common_suffix
            else new_remaining
        )

        # Show context-aware diff
        if (common_prefix or common_suffix) and (changed_old or changed_new):
            diff_lines.append("```diff")

            # Show context before (last 2 lines of prefix)
            context_before = (
                common_prefix[-2:] if len(common_prefix) > 2 else common_prefix
            )
            for line in context_before:
                diff_lines.append(f"  {line}")

            # Show removed lines
            for line in changed_old:
                diff_lines.append(f"- {line}")

            # Show added lines
            for line in changed_new:
                diff_lines.append(f"+ {line}")

            # Show context after (first 2 lines of suffix)
            context_after = (
                common_suffix[:2] if len(common_suffix) > 2 else common_suffix
            )
            for line in context_after:
                diff_lines.append(f"  {line}")

            diff_lines.append("```")
        else:
            # Full replacement - no common context
            diff_lines.append("```diff")
            for line in old_lines:
                diff_lines.append(f"- {line}")
            for line in new_lines:
                diff_lines.append(f"+ {line}")
            diff_lines.append("```")

    return "\n".join(diff_lines)


def format_tool_use(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Format a tool use into a human-readable message.

    Args:
        tool_name: Name of the tool being used
        tool_input: Dictionary of tool input parameters

    Returns:
        Formatted string for display in Vicoa dashboard
    """
    # Task - delegates work to specialized subagents
    if tool_name == "Task":
        description = tool_input.get("description", "task")
        subagent_type = tool_input.get("subagent_type", "unknown")
        return f"🔧 Using tool: Task - `{description}` (agent: {subagent_type})"

    # Bash - execute shell commands
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if command:
            return f"🔧 Using tool: Bash - `{command}`"
        return "🔧 Using tool: Bash"

    # Edit - modify file contents with string replacement
    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "unknown")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)

        formatted = f"🔧 Using tool: **Edit** - `{file_path}`\n\n"
        formatted += _format_edit_diff(old_string, new_string, replace_all)
        return formatted

    # MultiEdit - multiple edits to a single file
    elif tool_name == "MultiEdit":
        file_path = tool_input.get("file_path", "unknown")
        edits = tool_input.get("edits", [])

        formatted_lines = [f"🔧 Using tool: **MultiEdit** - `{file_path}`"]
        formatted_lines.append(
            f"*Making {len(edits)} edit{'s' if len(edits) != 1 else ''}:*"
        )
        formatted_lines.append("")

        for i, edit in enumerate(edits, 1):
            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")
            replace_all = edit.get("replace_all", False)

            if replace_all:
                formatted_lines.append(f"### Edit {i} *(replacing all occurrences)*")
            else:
                formatted_lines.append(f"### Edit {i}")
            formatted_lines.append("")
            formatted_lines.append(
                _format_edit_diff(old_string, new_string, replace_all)
            )
            formatted_lines.append("")

        return "\n".join(formatted_lines)

    # Read - retrieve file contents
    elif tool_name == "Read":
        file_path = tool_input.get("file_path", "unknown")
        offset = tool_input.get("offset")
        limit = tool_input.get("limit")

        if offset is not None or limit is not None:
            details = []
            if offset is not None:
                details.append(f"offset={offset}")
            if limit is not None:
                details.append(f"limit={limit}")
            return f"🔧 Using tool: Read - `{file_path}` ({', '.join(details)})"
        return f"🔧 Using tool: Read - `{file_path}`"

    # Write - create or overwrite files
    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "unknown")
        return f"🔧 Using tool: Write - `{file_path}`"

    # Glob - find files matching patterns
    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")
        if pattern:
            if path and path != ".":
                return f"🔧 Using tool: Glob - `{pattern}` in `{path}`"
            return f"🔧 Using tool: Glob - `{pattern}`"
        return "🔧 Using tool: Glob"

    # Grep - search files by regex
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")
        case_insensitive = tool_input.get("-i", False)
        multiline = tool_input.get("multiline", False)

        details = []
        if case_insensitive:
            details.append("case-insensitive")
        if multiline:
            details.append("multiline")

        if pattern:
            base = f"🔧 Using tool: Grep - `{pattern}`"
            if path and path != ".":
                base += f" in `{path}`"
            if details:
                base += f" ({', '.join(details)})"
            return base
        return "🔧 Using tool: Grep"

    # NotebookEdit - modify Jupyter notebook cells
    elif tool_name in ["NotebookEdit", "NotebookRead"]:
        notebook_path = tool_input.get("notebook_path", "unknown")
        cell_id = tool_input.get("cell_id")
        edit_mode = tool_input.get("edit_mode", "replace")

        if tool_name == "NotebookEdit" and cell_id:
            return f"🔧 Using tool: NotebookEdit - `{notebook_path}` (cell: {cell_id}, mode: {edit_mode})"
        return f"🔧 Using tool: {tool_name} - `{notebook_path}`"

    # WebFetch - retrieve and process web content
    elif tool_name == "WebFetch":
        url = tool_input.get("url", "")
        if url:
            return f"🔧 Using tool: WebFetch - `{url}`"
        return "🔧 Using tool: WebFetch"

    # WebSearch - query search engines
    elif tool_name == "WebSearch":
        query = tool_input.get("query", "")
        allowed_domains = tool_input.get("allowed_domains", [])
        blocked_domains = tool_input.get("blocked_domains", [])

        if query:
            base = f"🔧 Using tool: WebSearch - `{query}`"
            filters = []
            if allowed_domains:
                filters.append(f"allowed: {', '.join(allowed_domains)}")
            if blocked_domains:
                filters.append(f"blocked: {', '.join(blocked_domains)}")
            if filters:
                base += f" ({'; '.join(filters)})"
            return base
        return "🔧 Using tool: WebSearch"

    # TodoWrite - manage task lists
    elif tool_name == "TodoWrite":
        todos = tool_input.get("todos", [])
        if todos:
            status_icon = {
                "completed": "●",
                "in_progress": "◐",
                "pending": "○",
            }

            lines = [
                f"🔧 Using tool: TodoWrite - {len(todos)} todo{'s' if len(todos) != 1 else ''}",
                "",
            ]

            for idx, todo in enumerate(todos, 1):
                status = todo.get("status", "pending")
                content = todo.get("content") or todo.get("title") or "(untitled)"
                extra = []
                if todo.get("due_date"):
                    extra.append(f"due {todo['due_date']}")
                if todo.get("priority"):
                    extra.append(f"priority {todo['priority']}")
                meta = f" ({'; '.join(extra)})" if extra else ""

                lines.append(f"{status_icon.get(status, '○')} {idx}. {content}{meta}")

                if todo.get("details"):
                    lines.append(f"   - {todo['details']}")

            return "\n".join(lines)
        return "🔧 Using tool: TodoWrite - clearing todo list"

    # BashOutput - monitor background shell execution
    elif tool_name == "BashOutput":
        bash_id = tool_input.get("bash_id", "unknown")
        filter_pattern = tool_input.get("filter")
        if filter_pattern:
            return (
                f"🔧 Using tool: BashOutput - `{bash_id}` (filter: `{filter_pattern}`)"
            )
        return f"🔧 Using tool: BashOutput - `{bash_id}`"

    # KillShell - terminate background processes
    elif tool_name == "KillShell":
        shell_id = tool_input.get("shell_id", "unknown")
        return f"🔧 Using tool: KillShell - `{shell_id}`"

    # ListMcpResources - enumerate MCP server resources
    elif tool_name == "ListMcpResources":
        server = tool_input.get("server")
        if server:
            return f"🔧 Using tool: ListMcpResources - server: `{server}`"
        return "🔧 Using tool: ListMcpResources"

    # ReadMcpResource - access MCP server resource content
    elif tool_name == "ReadMcpResource":
        server = tool_input.get("server", "unknown")
        uri = tool_input.get("uri", "unknown")
        return f"🔧 Using tool: ReadMcpResource - `{uri}` from `{server}`"

    # ExitPlanMode - submit execution plans
    elif tool_name == "ExitPlanMode":
        return "🔧 Using tool: ExitPlanMode - submitting plan for approval"

    # Skill - execute a skill
    elif tool_name == "Skill":
        command = tool_input.get("command", "unknown")
        return f"🔧 Using tool: Skill - `{command}`"

    # SlashCommand - execute a slash command
    elif tool_name == "SlashCommand":
        command = tool_input.get("command", "unknown")
        return f"🔧 Using tool: SlashCommand - `{command}`"

    # AskUserQuestion - ask the user questions
    elif tool_name == "AskUserQuestion":
        questions = tool_input.get("questions", [])
        if questions:
            question_count = len(questions)
            return f"🔧 Using tool: AskUserQuestion - asking {question_count} question{'s' if question_count != 1 else ''}"
        return "🔧 Using tool: AskUserQuestion"

    # Generic fallback for unknown tools or MCP tools
    else:
        # Try to extract a common parameter
        for param in [
            "file_path",
            "notebook_path",
            "command",
            "pattern",
            "path",
            "url",
            "query",
        ]:
            if param in tool_input:
                return f"🔧 Using tool: {tool_name} - `{tool_input[param]}`"

        # No recognizable parameter, just return tool name
        return f"🔧 Using tool: {tool_name}"
