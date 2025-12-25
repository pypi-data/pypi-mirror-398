"""Utilities for parsing and formatting log entries."""

import json


def parse_log_line(
    line: str, raw: bool = False, command_completion_logs: bool = True
) -> str | None:
    """Parse a log line and extract the message field unless raw mode is enabled.

    Args:
        line: Raw log line from the log file
        raw: If True, return the raw line; if False, extract message field
        command_completion_logs: If True, include command completion logs; if False, hide them

    Returns:
        Formatted log line or None if parsing fails
    """
    if raw:
        return line.strip()

    try:
        log_entry = json.loads(line)
        # Try to extract message from different log types
        if "args" in log_entry and isinstance(log_entry["args"], dict):
            # For echo/click_echo commands, get the message directly
            if log_entry.get("command") in ["echo", "click_echo", "raw_log"]:
                return log_entry["args"].get("message", "")
            # For python_log entries, also get the message
            elif log_entry.get("command") == "python_log":
                return log_entry["args"].get("message", "")
            # For other commands, optionally hide them
            elif not command_completion_logs:
                return None
            # For other commands, show a summary
            else:
                cmd = log_entry.get("command", "unknown")
                duration = log_entry.get("duration_ms")
                if duration is not None:
                    return f"[{cmd}] completed in {duration:.2f}ms"
                return f"[{cmd}] executed"
        return None
    except (json.JSONDecodeError, KeyError):
        return None
