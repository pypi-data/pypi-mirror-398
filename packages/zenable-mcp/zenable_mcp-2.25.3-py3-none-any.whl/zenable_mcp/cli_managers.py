"""CLI managers for IDEs that support native MCP management commands.

This module provides CLI-based configuration management for IDEs that have
native CLIs for managing MCP servers (e.g., Claude Code, Amazon Q, Codex).
This is cleaner and more reliable than directly managing configuration files.
"""

import json
import re
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.platform_strategies import _find_all_commands


class IDEManagementStrategy(Enum):
    """How an IDE's MCP configuration is managed."""

    FILE_MANAGED = "file"  # Direct file I/O (current/fallback approach)
    CLI_MANAGED = "cli"  # Via IDE's native CLI


class IDECLIManager(ABC):
    """Base class for IDE CLI-based MCP management.

    Subclasses implement IDE-specific CLI commands for managing MCP servers.
    This provides a cleaner alternative to directly managing config files.
    """

    def __init__(self, cli_command: str, ide_display_name: str):
        """Initialize CLI manager.

        Args:
            cli_command: Name of CLI command (e.g., 'claude', 'q', 'codex')
            ide_display_name: Human-readable IDE name for error messages
        """
        self.cli_command = cli_command
        self.ide_display_name = ide_display_name
        self._cli_path: Optional[Path] = None
        self._cli_checked = False

    def get_cli_path(self) -> Optional[Path]:
        """Get path to IDE's CLI binary.

        Uses _find_all_commands() from platform_strategies to safely find
        the command in PATH. Caches result for performance.

        Returns:
            Path to CLI binary if found, None otherwise
        """
        if self._cli_checked:
            return self._cli_path

        self._cli_checked = True

        # Find all instances of command in PATH
        cmd_paths = _find_all_commands(self.cli_command)

        if not cmd_paths:
            echo(
                f"{self.ide_display_name} CLI '{self.cli_command}' not found in PATH",
                persona=Persona.DEVELOPER,
            )
            return None

        # Take the first match (usually the one earliest in PATH)
        # Subclasses can override for verification if needed
        cli_path = cmd_paths[0]

        # Validate absolute path (required by subprocess pattern)
        if not cli_path.is_absolute():
            raise ValueError(f"Command path must be absolute: {cli_path}")

        echo(
            f"Found {self.ide_display_name} CLI at: {cli_path}",
            persona=Persona.DEVELOPER,
        )
        self._cli_path = cli_path
        return cli_path

    def is_cli_available(self) -> bool:
        """Check if CLI is installed and accessible.

        Returns:
            True if CLI is available, False otherwise
        """
        cli_path = self.get_cli_path()
        if not cli_path:
            return False

        # Verify CLI actually works by running a simple command
        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            echo(
                f"CLI check failed for {self.ide_display_name}: {e}",
                persona=Persona.DEVELOPER,
                err=True,
            )
            return False

    @abstractmethod
    def add_server(
        self,
        name: str,
        url: str,
        scope: str,
        transport: str = "http",
        env: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> tuple[bool, str]:
        """Add MCP server via CLI.

        Args:
            name: Server name (e.g., 'zenable')
            url: Server URL
            scope: Configuration scope (e.g., 'project', 'user', 'local')
            transport: Transport type (e.g., 'http', 'stdio', 'sse')
            env: Environment variables to set
            headers: HTTP headers to set
            dry_run: If True, return what would be done without executing

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    def list_servers(self) -> list[dict[str, Any]]:
        """List all configured MCP servers.

        Returns:
            List of server info dicts with at least 'name' and 'url' keys
        """
        pass

    @abstractmethod
    def get_server(self, name: str) -> Optional[dict[str, Any]]:
        """Get details for a specific server.

        Args:
            name: Server name to look up

        Returns:
            Server info dict or None if not found
        """
        pass

    @abstractmethod
    def remove_server(
        self, name: str, scope: str, dry_run: bool = False
    ) -> tuple[bool, str]:
        """Remove MCP server via CLI.

        Args:
            name: Server name to remove
            scope: Configuration scope
            dry_run: If True, return what would be done without executing

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass


class AmazonQCLIManager(IDECLIManager):
    """CLI manager for Amazon Q Developer.

    Uses the 'q mcp' CLI commands if available. Falls back to file management
    since the Q CLI is optional and not always installed with Amazon Q.

    Example CLI usage:
        q mcp add -s project -t http zenable https://mcp.zenable.app/
        q mcp list
        q mcp get zenable
        q mcp remove zenable -s project
    """

    def __init__(self):
        super().__init__(cli_command="q", ide_display_name="Amazon Q")

    def add_server(
        self,
        name: str,
        url: str,
        scope: str = "project",
        transport: str = "http",
        env: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> tuple[bool, str]:
        """Add MCP server via Amazon Q CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        cmd = [
            "mcp",
            "add",
            "-s",
            scope,
            "-t",
            transport,
            name,
            url,
        ]

        if env:
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])

        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server added successfully"
            else:
                return (
                    False,
                    result.stderr
                    or result.stdout
                    or f"CLI returned {result.returncode}",
                )
        except subprocess.TimeoutExpired:
            return False, "CLI command timed out"
        except Exception as e:
            return False, f"Failed to run CLI: {e}"

    def list_servers(self) -> list[dict[str, Any]]:
        """List all MCP servers via Amazon Q CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return []

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                return []

            servers = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                parts = line.split(":", 1)
                name = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""

                server = {"name": name, "raw_output": rest}

                url_match = re.search(r"(https?://[^\s]+)", rest)
                if url_match:
                    server["url"] = url_match.group(1)

                servers.append(server)

            return servers
        except Exception:
            return []

    def get_server(self, name: str) -> Optional[dict[str, Any]]:
        """Get server details via Amazon Q CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return None

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "mcp", "get", name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return None

            server_info = {"name": name, "raw_output": result.stdout}

            for line in result.stdout.splitlines():
                line = line.strip()
                if "URL:" in line:
                    server_info["url"] = line.split("URL:", 1)[1].strip()
                if "Scope:" in line:
                    scope_text = line.split("Scope:", 1)[1].strip()
                    server_info["scope"] = scope_text
                    if "project" in scope_text.lower():
                        server_info["scope_simple"] = "project"
                    elif "user" in scope_text.lower():
                        server_info["scope_simple"] = "user"

            return server_info
        except Exception:
            return None

    def remove_server(
        self, name: str, scope: str = "project", dry_run: bool = False
    ) -> tuple[bool, str]:
        """Remove server via Amazon Q CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        cmd = ["mcp", "remove", name, "-s", scope]

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server removed successfully"
            else:
                return (
                    False,
                    result.stderr or f"CLI returned {result.returncode}",
                )
        except Exception as e:
            return False, f"Failed to remove server: {e}"


class CodexCLIManager(IDECLIManager):
    """CLI manager for OpenAI Codex IDE.

    Uses the 'codex mcp' CLI commands to manage MCP server configuration.

    Example CLI usage:
        codex mcp add -t http zenable https://mcp.zenable.app/
        codex mcp list
        codex mcp get zenable
        codex mcp remove zenable
    """

    def __init__(self):
        super().__init__(cli_command="codex", ide_display_name="Codex")

    def add_server(
        self,
        name: str,
        url: str,
        scope: str = "user",
        transport: str = "http",
        env: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> tuple[bool, str]:
        """Add MCP server via Codex CLI.

        Note: Codex only supports user/global scope (no project scope).
        """
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        # Codex CLI syntax: codex mcp add --url <URL> <NAME>
        # For HTTP servers, use --url flag
        cmd = [
            "mcp",
            "add",
            "--url",
            url,
            name,
        ]

        # Codex uses --env instead of -e
        if env:
            for key, value in env.items():
                cmd.extend(["--env", f"{key}={value}"])

        # Note: Codex doesn't support custom headers for HTTP servers
        if headers:
            echo(
                f"Warning: {self.ide_display_name} CLI does not support custom headers",
                persona=Persona.DEVELOPER,
            )

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server added successfully"
            else:
                return (
                    False,
                    result.stderr
                    or result.stdout
                    or f"CLI returned {result.returncode}",
                )
        except subprocess.TimeoutExpired:
            return False, "CLI command timed out"
        except Exception as e:
            return False, f"Failed to run CLI: {e}"

    def list_servers(self) -> list[dict[str, Any]]:
        """List all MCP servers via Codex CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return []

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                return []

            servers = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                parts = line.split(":", 1)
                name = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""

                server = {"name": name, "raw_output": rest}

                url_match = re.search(r"(https?://[^\s]+)", rest)
                if url_match:
                    server["url"] = url_match.group(1)

                servers.append(server)

            return servers
        except Exception:
            return []

    def get_server(self, name: str) -> Optional[dict[str, Any]]:
        """Get server details via Codex CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return None

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "mcp", "get", name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return None

            server_info = {
                "name": name,
                "raw_output": result.stdout,
                "scope_simple": "user",  # Codex is always user/global
            }

            for line in result.stdout.splitlines():
                line = line.strip()
                # Handle both "URL:" and "url:" formats
                if "url:" in line.lower():
                    # Split on either "URL:" or "url:"
                    if "URL:" in line:
                        server_info["url"] = line.split("URL:", 1)[1].strip()
                    elif "url:" in line:
                        server_info["url"] = line.split("url:", 1)[1].strip()

            return server_info
        except Exception:
            return None

    def remove_server(
        self, name: str, scope: str = "user", dry_run: bool = False
    ) -> tuple[bool, str]:
        """Remove server via Codex CLI.

        Note: scope parameter is ignored as Codex doesn't need it.
        """
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        # Codex doesn't need scope parameter
        cmd = ["mcp", "remove", name]

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server removed successfully"
            else:
                return (
                    False,
                    result.stderr or f"CLI returned {result.returncode}",
                )
        except Exception as e:
            return False, f"Failed to remove server: {e}"


class ClaudeCodeCLIManager(IDECLIManager):
    """CLI manager for Claude Code.

    Uses the 'claude mcp' CLI commands to manage MCP server configuration.

    Example CLI usage:
        claude mcp add -s project -t http zenable https://mcp.zenable.app/
        claude mcp list
        claude mcp get zenable
        claude mcp remove zenable -s project
    """

    def __init__(self):
        super().__init__(cli_command="claude", ide_display_name="Claude Code")

    def add_server(
        self,
        name: str,
        url: str,
        scope: str = "project",
        transport: str = "http",
        env: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> tuple[bool, str]:
        """Add MCP server via Claude CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        cmd = [
            "mcp",
            "add",
            "-s",
            scope,
            "-t",
            transport,
            name,
            url,
        ]

        # Add environment variables if provided
        if env:
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])

        # Add headers if provided
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server added successfully"
            else:
                error_msg = (
                    result.stderr
                    or result.stdout
                    or f"CLI returned {result.returncode}"
                )
                return False, error_msg
        except subprocess.TimeoutExpired:
            return False, "CLI command timed out"
        except Exception as e:
            return False, f"Failed to run CLI: {e}"

    def list_servers(self) -> list[dict[str, Any]]:
        """List all MCP servers via Claude CLI.

        Parses output like:
            Checking MCP server health...

            zenable: https://mcp.zenable.app/ (HTTP) - ⚠ Needs authentication
        """
        cli_path = self.get_cli_path()
        if not cli_path:
            return []

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                echo(
                    f"Failed to list servers: {result.stderr}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )
                return []

            servers = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or "Checking" in line or "MCP" in line and ":" not in line:
                    continue

                # Parse lines like: "zenable: https://mcp.zenable.app/ (HTTP) - ⚠ Needs authentication"
                if ":" in line:
                    parts = line.split(":", 1)
                    name = parts[0].strip()
                    rest = parts[1].strip() if len(parts) > 1 else ""

                    server = {"name": name, "raw_output": rest}

                    # Extract URL (look for http/https)
                    url_match = re.search(r"(https?://[^\s]+)", rest)
                    if url_match:
                        server["url"] = url_match.group(1)

                    # Extract transport type
                    transport_match = re.search(r"\(([A-Z]+)\)", rest)
                    if transport_match:
                        server["transport"] = transport_match.group(1).lower()

                    # Extract status
                    if "Needs authentication" in rest or "⚠" in rest:
                        server["status"] = "needs_auth"
                    elif "✓" in rest or "healthy" in rest.lower():
                        server["status"] = "healthy"
                    else:
                        server["status"] = "unknown"

                    servers.append(server)

            return servers
        except Exception as e:
            echo(
                f"Failed to list servers: {e}",
                persona=Persona.DEVELOPER,
                err=True,
            )
            return []

    def get_server(self, name: str) -> Optional[dict[str, Any]]:
        """Get server details via Claude CLI.

        Parses output like:
            zenable:
              Scope: Project config (shared via .mcp.json)
              Status: ⚠ Needs authentication
              Type: http
              URL: https://mcp.zenable.app/
        """
        cli_path = self.get_cli_path()
        if not cli_path:
            return None

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, "mcp", "get", name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return None

            server_info = {"name": name, "raw_output": result.stdout}

            for line in result.stdout.splitlines():
                line = line.strip()
                if "Scope:" in line:
                    scope_text = line.split("Scope:", 1)[1].strip()
                    server_info["scope"] = scope_text
                    # Extract simple scope (project/user/local)
                    if "project" in scope_text.lower():
                        server_info["scope_simple"] = "project"
                    elif "user" in scope_text.lower():
                        server_info["scope_simple"] = "user"
                    else:
                        server_info["scope_simple"] = "local"
                elif "Status:" in line:
                    server_info["status"] = line.split("Status:", 1)[1].strip()
                elif "Type:" in line:
                    server_info["type"] = line.split("Type:", 1)[1].strip()
                elif "URL:" in line:
                    server_info["url"] = line.split("URL:", 1)[1].strip()

            return server_info
        except Exception as e:
            echo(
                f"Failed to get server {name}: {e}",
                persona=Persona.DEVELOPER,
                err=True,
            )
            return None

    def remove_server(
        self, name: str, scope: str = "project", dry_run: bool = False
    ) -> tuple[bool, str]:
        """Remove server via Claude CLI."""
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        cmd = ["mcp", "remove", name, "-s", scope]

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server removed successfully"
            else:
                return False, result.stderr or f"CLI returned {result.returncode}"
        except Exception as e:
            return False, f"Failed to remove server: {e}"


class AntigravityCLIManager(IDECLIManager):
    """CLI manager for Antigravity IDE.

    Uses the 'antigravity --add-mcp' command which accepts a JSON blob.

    Example CLI usage:
        antigravity --add-mcp '{"name":"zenable","url":"https://mcp.zenable.app/","type":"http"}'
    """

    def __init__(self):
        super().__init__(cli_command="antigravity", ide_display_name="Antigravity")

    def add_server(
        self,
        name: str,
        url: str,
        scope: str = "user",
        transport: str = "http",
        env: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        dry_run: bool = False,
    ) -> tuple[bool, str]:
        """Add MCP server via Antigravity CLI.

        Antigravity uses --add-mcp with a JSON blob containing the server config.
        The JSON structure is: {"name": "zenable", "url": "...", "type": "http"}
        """
        cli_path = self.get_cli_path()
        if not cli_path:
            return False, f"{self.ide_display_name} CLI not found"

        # Build JSON config for the server
        json_blob = {
            "name": name,
            "url": url,
            "type": transport,
        }

        # Add env/headers if provided (though Antigravity may not support these)
        if env:
            json_blob["env"] = env
        if headers:
            json_blob["headers"] = headers

        # Use compact JSON format (no spaces, no newlines)
        json_str = json.dumps(json_blob, separators=(",", ":"))

        cmd = ["--add-mcp", json_str]

        if dry_run:
            return True, f"Would run: {cli_path} {' '.join(cmd)}"

        try:
            if not cli_path.is_absolute():
                raise ValueError(f"CLI path must be absolute: {cli_path}")

            result = subprocess.run(
                [cli_path, *cmd],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True, result.stdout or "Server added successfully"
            else:
                return (
                    False,
                    result.stderr
                    or result.stdout
                    or f"CLI returned {result.returncode}",
                )
        except subprocess.TimeoutExpired:
            return False, "CLI command timed out"
        except Exception as e:
            return False, f"Failed to run CLI: {e}"

    def list_servers(self) -> list[dict[str, Any]]:
        """List all MCP servers.

        Note: Antigravity may not have a list command, so this returns empty.
        """
        return []

    def get_server(self, name: str) -> Optional[dict[str, Any]]:
        """Get details for a specific server.

        Note: Antigravity may not have a get command, so this returns None.
        """
        return None

    def remove_server(
        self, name: str, scope: str = "user", dry_run: bool = False
    ) -> tuple[bool, str]:
        """Remove server via Antigravity CLI.

        Note: Antigravity may not have a remove command.
        """
        return (
            False,
            f"{self.ide_display_name} does not support removing servers via CLI",
        )
