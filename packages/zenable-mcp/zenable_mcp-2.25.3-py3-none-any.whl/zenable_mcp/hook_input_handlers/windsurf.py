"""Windsurf hook input handler.

See: https://docs.windsurf.com/windsurf/cascade/hooks
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


class WindsurfInputHandler(InputHandler):
    """Handler for Windsurf hook inputs.

    See: https://docs.windsurf.com/windsurf/cascade/hooks

    Windsurf sends hook data as JSON to stdin with the following schema for post_write_code:
    {
        "agent_action_name": "post_write_code",
        "trajectory_id": "string",
        "execution_id": "string",
        "timestamp": "ISO 8601 timestamp",
        "tool_info": {
            "file_path": "<absolute path>",
            "edits": [
                {
                    "old_string": "<search text>",
                    "new_string": "<replacement text>"
                }
            ]
        }
    }

    Exit codes:
    - 0: Success, no conformance issues found
    - 2: Conformance issues found
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
        return "Windsurf"

    @property
    def format(self) -> HookInputFormat:
        return HookInputFormat.WINDSURF_HOOK

    def can_handle(self) -> bool:
        """Check if we're running as a Windsurf hook.

        Checks for:
        1. Non-TTY stdin with JSON data
        2. JSON contains expected Windsurf hook fields (agent_action_name, tool_info)
        3. agent_action_name is "post_write_code"
        4. tool_info contains file_path
        """
        # Check stdin for Windsurf JSON
        stdin_data = self._read_stdin()
        if not stdin_data:
            return False

        # Check for Windsurf-specific fields
        # Windsurf uses agent_action_name and tool_info structure
        has_agent_action = "agent_action_name" in stdin_data
        has_tool_info = "tool_info" in stdin_data

        if not (has_agent_action and has_tool_info):
            return False

        # Must be post_write_code hook (we only support post-write for conformance checking)
        hook_event = stdin_data.get("agent_action_name", "")
        if hook_event != "post_write_code":
            echo(
                f"Windsurf hook event '{hook_event}' is not supported (only post_write_code)",
                persona=Persona.DEVELOPER,
            )
            return False

        # tool_info must contain file_path
        tool_info = stdin_data.get("tool_info", {})
        if not isinstance(tool_info, dict) or "file_path" not in tool_info:
            return False

        echo(
            "Detected Windsurf post_write_code hook format in stdin",
            persona=Persona.DEVELOPER,
        )
        return True

    def parse_input(self) -> HookInputContext:
        """Parse Windsurf hook input from stdin."""
        stdin_data = self._read_stdin()
        if not stdin_data:
            raise HandlerEnvironmentError("Windsurf", "No Windsurf input available")

        # Extract relevant information
        agent_action_name = stdin_data.get("agent_action_name", "")
        tool_info = stdin_data.get("tool_info", {})
        file_path_str = tool_info.get("file_path", "")
        edits = tool_info.get("edits", [])

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
                "WINDSURF_HOOK_EVENT_NAME": agent_action_name,
                "WINDSURF_TRAJECTORY_ID": stdin_data.get("trajectory_id", ""),
                "WINDSURF_EXECUTION_ID": stdin_data.get("execution_id", ""),
            },
            metadata={
                "agent_action_name": agent_action_name,
                "edits": edits,
                "trajectory_id": stdin_data.get("trajectory_id"),
                "execution_id": stdin_data.get("execution_id"),
                "timestamp": stdin_data.get("timestamp"),
            },
        )

        return context

    def get_files(self) -> list[Path]:
        """Extract file paths from Windsurf input."""
        context = self.parse_input()
        return context.files

    def build_response_to_hook_call(
        self, has_findings: bool, findings_text: str = ""
    ) -> str | None:
        """Build JSON response for Windsurf post_write_code hook.

        Returns JSON output for Windsurf's hook output (shown when show_output: true).
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
        """Get the appropriate exit code for Windsurf handler.

        Args:
            has_findings: Whether conformance issues were found

        Returns:
            CONFORMANCE_ISSUES_FOUND (2) if findings, SUCCESS (0) otherwise
        """
        if has_findings:
            return ExitCode.CONFORMANCE_ISSUES_FOUND
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
