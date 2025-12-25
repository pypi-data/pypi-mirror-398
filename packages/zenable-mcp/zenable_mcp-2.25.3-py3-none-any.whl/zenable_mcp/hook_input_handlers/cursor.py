"""Cursor hook input handler.

See: https://cursor.com/docs/agent/hooks
"""

import json
import sys
from pathlib import Path
from typing import Any

from zenable_mcp.exceptions import HandlerEnvironmentError
from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.hook_input_handlers.base import (
    HookInputContext,
    HookInputFormat,
    InputHandler,
)
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona


class CursorInputHandler(InputHandler):
    """Handler for Cursor hook inputs.

    See: https://cursor.com/docs/agent/hooks

    Cursor sends hook data as JSON to stdin with the following schema for afterFileEdit:
    {
        "conversation_id": "string",
        "generation_id": "string",
        "hook_event_name": "afterFileEdit",
        "workspace_roots": ["<path>"],
        "file_path": "<absolute path>",
        "edits": [
            {
                "old_string": "<search text>",
                "new_string": "<replacement text>"
            }
        ]
    }

    Limitations (see https://cursor.com/docs/agent/hooks):
    - Cursor agents don't use exit codes from hooks
    - "after" hooks cannot send output back to Cursor to influence agent behavior
    - We print human-readable output to stdout and always exit 0

    Future: Enhanced Cursor hook support may allow blocking edits or providing feedback.
    """

    def __init__(self):
        self._stdin_data: dict[str, Any] | None = None
        self._stdin_read: bool = False
        self._shared_stdin_provided: bool = False

    def set_shared_stdin_data(self, data: dict[str, Any] | None) -> None:
        """Set shared stdin data from the registry."""
        self._stdin_data = data
        self._stdin_read = True
        self._shared_stdin_provided = True

    @property
    def name(self) -> str:
        return "Cursor"

    @property
    def format(self) -> HookInputFormat:
        return HookInputFormat.CURSOR_HOOK

    def can_handle(self) -> bool:
        """Check if we're running as a Cursor hook.

        Checks for:
        1. Non-TTY stdin with JSON data
        2. JSON contains expected Cursor hook fields (hook_event_name, file_path, edits)
        3. hook_event_name is "afterFileEdit"
        """
        # Check stdin for Cursor JSON
        stdin_data = self._read_stdin()
        if not stdin_data:
            return False

        # Check for Cursor-specific fields
        required_fields = {"hook_event_name", "file_path", "edits"}
        has_required = all(field in stdin_data for field in required_fields)

        if not has_required:
            return False

        # Must be afterFileEdit hook
        hook_event = stdin_data.get("hook_event_name", "")
        if hook_event != "afterFileEdit":
            echo(
                f"Cursor hook event '{hook_event}' is not supported (only afterFileEdit)",
                persona=Persona.DEVELOPER,
            )
            return False

        # edits must be a non-empty list
        edits = stdin_data.get("edits")
        if not isinstance(edits, list) or len(edits) == 0:
            return False

        echo(
            "Detected Cursor afterFileEdit hook format in stdin",
            persona=Persona.DEVELOPER,
        )
        return True

    def parse_input(self) -> HookInputContext:
        """Parse Cursor hook input from stdin."""
        stdin_data = self._read_stdin()
        if not stdin_data:
            raise HandlerEnvironmentError("Cursor", "No Cursor input available")

        # Extract relevant information
        hook_event_name = stdin_data.get("hook_event_name", "")
        file_path_str = stdin_data.get("file_path", "")
        edits = stdin_data.get("edits", [])
        workspace_roots = stdin_data.get("workspace_roots", [])

        # Extract file path
        files = []
        if file_path_str:
            file_path = Path(file_path_str)
            files.append(file_path)

        # Build context
        context = HookInputContext(
            format=self.format,
            raw_data=stdin_data,
            files=files,
            environment={
                "CURSOR_HOOK_EVENT_NAME": hook_event_name,
                "CURSOR_CONVERSATION_ID": stdin_data.get("conversation_id", ""),
                "CURSOR_GENERATION_ID": stdin_data.get("generation_id", ""),
            },
            metadata={
                "hook_event_name": hook_event_name,
                "edits": edits,
                "workspace_roots": workspace_roots,
                "conversation_id": stdin_data.get("conversation_id"),
                "generation_id": stdin_data.get("generation_id"),
            },
        )

        return context

    def get_files(self) -> list[Path]:
        """Extract file paths from Cursor input."""
        context = self.parse_input()
        return context.files

    def build_response_to_hook_call(
        self, has_findings: bool, findings_text: str = ""
    ) -> str | None:
        """Build JSON response for Cursor afterFileEdit hook.

        Returns JSON output for Cursor's hook output panel. Note that Cursor
        "after" hooks cannot send output back to the agent to influence behavior.
        See https://cursor.com/docs/agent/hooks for current capabilities.
        """
        if has_findings:
            result = {
                "conformance_check": "FAIL",
                "details": findings_text,
            }
        else:
            result = {
                "conformance_check": "PASS",
            }
        return json.dumps(result)

    def get_exit_code(self, has_findings: bool) -> int:
        """Get the appropriate exit code for Cursor handler.

        Cursor agents don't use exit codes from hooks, so we always return 0.
        See https://cursor.com/docs/agent/hooks for current capabilities.

        Args:
            has_findings: Whether conformance issues were found (ignored for Cursor)

        Returns:
            Always SUCCESS (exit code 0)
        """
        # Cursor ignores exit codes - always return success
        return ExitCode.SUCCESS

    def _read_stdin(self) -> dict[str, Any] | None:
        """Read and parse JSON from stdin if available.

        Returns:
            Parsed JSON data or None if stdin is a tty or can't be read
        """
        if self._stdin_read:
            return self._stdin_data

        self._stdin_read = True

        if sys.stdin.isatty():
            echo(
                "Error: stdin is a tty, not reading input",
                persona=Persona.DEVELOPER,
                err=True,
            )
            return None

        try:
            # Try to parse as JSON
            self._stdin_data = json.load(sys.stdin)
            if isinstance(self._stdin_data, dict):
                return self._stdin_data
        except (json.JSONDecodeError, IOError, OSError) as e:
            echo(
                f"Error: Failed to parse stdin as JSON: {e}",
                persona=Persona.DEVELOPER,
                err=True,
            )
            self._stdin_data = None

        return None
