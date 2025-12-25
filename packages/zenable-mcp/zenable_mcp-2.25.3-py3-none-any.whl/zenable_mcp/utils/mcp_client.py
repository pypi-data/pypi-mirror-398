"""MCP client for communicating with the Zenable MCP server."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import click
import git
import httpx
from fastmcp import Client as FastMCPClient
from fastmcp.client.auth import OAuth
from fastmcp.client.transports import StreamableHttpTransport
from key_value.aio.stores.disk import DiskStore

from zenable_mcp.constants import OAUTH_TOKEN_CACHE_DIR
from zenable_mcp.exceptions import APIError
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.utils.conformance_parser import ConformanceParser
from zenable_mcp.utils.conformance_status import ConformanceReport
from zenable_mcp.utils.retries import is_transient_error, retry_on_error

# Suppress noisy MCP library error logs that show full stack traces to users
# These errors are already handled by our retry logic with user-friendly messages
# The "mcp" logger produces "[ERROR] Error reading SSE stream" with full tracebacks
logging.getLogger("mcp").setLevel(logging.CRITICAL)


class ZenableMCPClient:
    """Client for communicating with the Zenable MCP server."""

    def __init__(
        self, base_url: Optional[str] = None, token_cache_dir: Optional[Path] = None
    ):
        """
        Initialize the Zenable MCP client with OAuth authentication.

        Args:
            base_url: Optional base URL for the MCP server
            token_cache_dir: Directory to cache OAuth tokens
        """
        # Get base URL from parameter, env var, or default
        self.base_url = (
            base_url
            or os.environ.get("ZENABLE_MCP_ENDPOINT")
            or "https://mcp.zenable.app"
        ).rstrip("/")  # Remove trailing slash for consistency

        # Use persistent cache directory
        self.token_cache_dir = token_cache_dir or OAUTH_TOKEN_CACHE_DIR
        self.token_cache_dir.mkdir(parents=True, exist_ok=True)

        # Create OAuth instance - let FastMCP handle everything
        # Use DiskStore for token persistence
        self.oauth = OAuth(
            mcp_url=self.base_url,
            scopes=["openid", "profile", "email"],
            client_name="Zenable MCP Client",
            token_storage=DiskStore(directory=str(self.token_cache_dir)),
            callback_port=23014,  # Fixed port for consistency
        )

        self.client = None
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._successful_operations = 0  # Track operations since last reconnect

    async def _create_connection(self) -> None:
        """
        Create and establish a connection to the MCP server.

        This method is shared between initial connection and reconnection.

        Raises:
            APIError: If connection fails
        """
        # Use StreamableHttpTransport with SSE read timeout
        # Per FastMCP/MCP SDK research and production requirements:
        # - Conformance checks normally complete in <10 seconds
        # - 90 seconds provides buffer for OAuth, slow networks, edge cases
        # - Combined with 3x retry for transient failures
        transport = StreamableHttpTransport(
            self.base_url,
            sse_read_timeout=90.0,  # 90 second timeout for SSE streaming
        )

        # Initialize client with OAuth and timeouts
        # - init_timeout: Covers OAuth flow + connection establishment
        # - timeout: Individual RPC call timeout (conformance_check can be slow with many files)
        # OAuth can take 30-60s with user interaction (clicking, MFA, SSO redirects)
        self.client = FastMCPClient(
            transport=transport,
            auth=self.oauth,
            init_timeout=120.0,  # 2 minutes for OAuth + connection establishment
            timeout=75.0,  # 75 seconds for RPC calls (conformance checks can be slow)
        )

        # Connect with a generous timeout for OAuth flow
        # OAuth requires user interaction (clicking auth button, MFA, SSO)
        # Very generous timeout (5 minutes) to handle:
        # - User stepping away during auth
        # - Slow SSO redirects
        # - MFA delays
        # Better to wait longer than to cancel mid-auth and corrupt state
        try:
            await asyncio.wait_for(self.client.__aenter__(), timeout=300.0)
        except asyncio.TimeoutError:
            echo(f"Connection to {self.base_url} timed out after 5 minutes", err=True)
            echo(
                "This may be due to waiting for OAuth authentication.",
                persona=Persona.DEVELOPER,
                err=True,
            )
            raise APIError(
                f"Timeout connecting to MCP server at {self.base_url} - OAuth flow may have stalled"
            )
        except Exception as e:
            # Handle connection errors more gracefully
            error_msg = self._format_user_error(e)

            # Check if this is a transient error that might succeed on retry
            if is_transient_error(e):
                echo(f"Connection issue: {error_msg}", err=True)
                echo(
                    "The server may be experiencing temporary issues. Please try again in a moment.",
                    err=True,
                )
            else:
                echo(f"Unable to connect to {self.base_url}", err=True)
                echo(error_msg, err=True)

            # Show technical details for developers
            echo(
                f"Technical error: {type(e).__name__}: {e}",
                persona=Persona.DEVELOPER,
                err=True,
            )

            raise APIError(f"Failed to connect to MCP server at {self.base_url}")

    async def __aenter__(self):
        """Enter async context manager."""
        echo(f"Connecting to MCP server at {self.base_url}", persona=Persona.POWER_USER)
        await self._create_connection()
        echo("Successfully connected!", persona=Persona.DEVELOPER)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect to the MCP server.

        Returns:
            True if reconnection succeeded, False otherwise
        """
        self._connection_attempts += 1

        if self._connection_attempts > self._max_connection_attempts:
            echo(
                f"Maximum reconnection attempts ({self._max_connection_attempts}) reached",
                persona=Persona.DEVELOPER,
                err=True,
            )
            return False

        echo(
            f"Attempting to reconnect to MCP server (attempt {self._connection_attempts}/{self._max_connection_attempts})...",
            persona=Persona.POWER_USER,
        )

        # Close existing connection if present
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                echo(
                    f"Error closing old connection: {e}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )

        # Try to create new connection
        try:
            await self._create_connection()
            # Don't reset counter immediately - it will be reset after stable operations
            echo(
                "Successfully reconnected!",
                persona=Persona.DEVELOPER,
            )
            return True
        except Exception as e:
            echo(
                f"Reconnection failed: {type(e).__name__}",
                persona=Persona.DEVELOPER,
                err=True,
            )
            return False

    def _is_connection_error(self, e: Exception) -> bool:
        """
        Check if an exception represents a connection-level error that might be fixed by reconnecting.

        Args:
            e: The exception to check

        Returns:
            True if this appears to be a connection error
        """
        return isinstance(
            e,
            (
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ConnectError,
                httpx.NetworkError,
            ),
        )

    @retry_on_error(
        max_retries=3,
        initial_delay=0.1,
        max_delay=3.0,
        backoff_factor=5.0,
        retryable_conditions=is_transient_error,
    )
    async def _call_tool_with_retry(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool with automatic retry on transient errors.

        This wraps the underlying client.call_tool() with retry logic to handle
        transient network errors like httpx.RemoteProtocolError.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            The tool result

        Raises:
            APIError: If the tool call fails after all retries
        """
        if not self.client:
            raise APIError("Client not initialized. Use async with statement.")

        result = await self.client.call_tool(tool_name, arguments)

        # Track successful operations and reset connection attempts after stability
        self._successful_operations += 1
        if self._successful_operations >= 3:
            # After 3 successful operations, consider connection stable
            self._connection_attempts = 0
            self._successful_operations = 0

        return result

    def _format_user_error(self, error: Exception) -> str:
        """
        Format an exception into a user-friendly error message.

        Args:
            error: The exception to format

        Returns:
            A user-friendly error message
        """
        error_type = type(error).__name__
        error_str = str(error)

        # Handle timeout errors
        if "timeout" in error_type.lower() or "Timeout" in error_str.lower():
            return "The server is taking longer than expected. Please try again in a moment."

        # Handle connection errors
        if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
            return "Unable to reach the server. Please check your internet connection and try again."

        # Handle protocol errors
        if isinstance(error, httpx.RemoteProtocolError):
            return (
                "The server connection was interrupted. Please try again in a moment."
            )

        # Handle HTTP status errors
        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            if status == 429:
                return "Rate limit reached. Please wait a moment before trying again."
            elif 500 <= status < 600:
                # All 5xx errors get the same message
                return "The server is temporarily unavailable. Please try again in a moment."
            else:
                return f"Server returned error {status}. Please try again."

        # Handle MCP-specific errors and generic errors with same message
        # This covers ClientRequest timeouts and any other unexpected errors
        return "The server is temporarily unavailable. Please try again in a moment."

    async def check_conformance(
        self,
        files: list[dict[str, str]],
        batch_size: int = 5,
        show_progress: bool = True,
        ctx: Optional[click.Context] = None,
    ) -> list[dict[str, Any]]:
        """
        Call the conformance_check tool with the list of files.

        Args:
            files: List of file dictionaries with 'path' and 'content'
            batch_size: Maximum number of files to send at once (default 5, max 5)
            show_progress: Whether to show progress messages (default True)
            ctx: Optional Click context object containing configuration

        Returns:
            List of results for each batch with files
        """
        if not self.client:
            raise APIError("Client not initialized. Use async with statement.")

        # Enforce maximum batch size of 5
        if batch_size > 5:
            batch_size = 5

        all_results = []
        total_files = len(files)

        # Single file doesn't need batching
        if total_files == 1:
            echo("Processing single file", persona=Persona.DEVELOPER)
            try:
                result = await self._call_tool_with_retry(
                    "conformance_check", {"list_of_files": files}
                )
                echo("Received response from MCP server", persona=Persona.DEVELOPER)

                batch_results = {
                    "batch": 1,
                    "files": files,
                    "result": result,
                    "error": None,
                }
                all_results.append(batch_results)
            except Exception as e:
                # Log technical details for developers
                echo(
                    f"Technical error: {type(e).__name__}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )
                # Show user-friendly message
                error_msg = self._format_user_error(e)
                echo(f"✗ {error_msg}", err=True, log=False)
                batch_results = {
                    "batch": 1,
                    "files": files,
                    "result": None,
                    "error": error_msg,
                }
                all_results.append(batch_results)

            return all_results

        # Process multiple files in batches
        files_processed = 0
        files_with_issues = 0

        echo(
            f"Processing {total_files} files in batches of {batch_size}",
            persona=Persona.DEVELOPER,
        )
        i = 0
        batch_retry_attempted = {}  # Track which batches have been retried after reconnection
        while i < total_files:
            batch = files[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            echo(
                f"Processing batch {batch_num} with {len(batch)} files",
                persona=Persona.DEVELOPER,
            )

            if show_progress:
                # Show progress
                echo(
                    f"\nChecking files {i + 1}-{min(i + len(batch), total_files)} of {total_files}...",
                    log=False,
                )

                # Show which files are in this batch
                for file_dict in batch:
                    file_path = Path(file_dict["path"])
                    # Try to make path relative to working directory
                    try:
                        rel_path = file_path.relative_to(Path.cwd())
                    except ValueError:
                        # If not relative to cwd, try relative to git root
                        try:
                            repo = git.Repo(search_parent_directories=True)
                            rel_path = file_path.relative_to(repo.working_dir)
                        except Exception:
                            rel_path = file_path
                    echo(f"  - {rel_path}", persona=Persona.POWER_USER)

            try:
                echo(
                    f"Calling conformance_check tool for batch {batch_num}",
                    persona=Persona.DEVELOPER,
                )
                result = await self._call_tool_with_retry(
                    "conformance_check", {"list_of_files": batch}
                )
                echo(
                    f"Received response for batch {batch_num}",
                    persona=Persona.DEVELOPER,
                )

                # Store batch with its files for later processing
                batch_results = {
                    "batch": batch_num,
                    "files": batch,
                    "result": result,
                    "error": None,
                }
                all_results.append(batch_results)

                if show_progress:
                    # Parse and show interim results
                    if (
                        hasattr(result, "content")
                        and result.content
                        and len(result.content) > 0
                    ):
                        content_text = (
                            result.content[0].text
                            if hasattr(result.content[0], "text")
                            else str(result.content[0])
                        ) or ""

                        # Try to parse the result to get file-specific information
                        try:
                            parsed_result = json.loads(content_text)
                            # Assume the result contains information about each file
                            if isinstance(parsed_result, dict):
                                # Count files with issues in this batch
                                batch_issues = 0
                                if "files" in parsed_result and parsed_result["files"]:
                                    for file_result in parsed_result["files"]:
                                        if file_result.get("issues", []):
                                            batch_issues += 1
                                elif (
                                    "issues" in parsed_result
                                    and parsed_result["issues"]
                                ):
                                    batch_issues = len(batch)

                                files_with_issues += batch_issues
                                files_processed += len(batch)

                                # Show running total
                                echo(
                                    f"Progress: {files_processed}/{total_files} files checked, {files_with_issues} with issues",
                                    log=False,
                                )
                        except (json.JSONDecodeError, KeyError):
                            files_processed += len(batch)
                            echo(
                                f"Progress: {files_processed}/{total_files} files checked",
                                log=False,
                            )
                    else:
                        files_processed += len(batch)
                        echo(
                            f"Progress: {files_processed}/{total_files} files checked",
                            log=False,
                        )

                # Move to next batch after successful processing
                i += batch_size

            except Exception as e:
                # Handle errors per batch
                # Log technical details for developers
                echo(
                    f"Technical error in batch {batch_num}: {type(e).__name__}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )

                # Check if this is a connection error that we can try to recover from
                if self._is_connection_error(e):
                    # Check if we've already retried this batch after reconnection
                    if batch_num in batch_retry_attempted:
                        echo(
                            f"Batch {batch_num} already retried after reconnection. Recording error...",
                            persona=Persona.DEVELOPER,
                            err=True,
                        )
                    else:
                        echo(
                            "Connection error detected. Attempting to reconnect...",
                            persona=Persona.POWER_USER,
                        )

                        # Try to reconnect
                        reconnected = await self._reconnect()

                        if reconnected:
                            # Successfully reconnected - mark this batch as retried and retry once
                            batch_retry_attempted[batch_num] = True
                            echo(
                                f"Retrying batch {batch_num} after reconnection...",
                                persona=Persona.POWER_USER,
                            )
                            continue  # Retry the same batch
                        else:
                            # Couldn't reconnect - record error and move on
                            echo(
                                "Unable to reconnect. Recording error and continuing...",
                                persona=Persona.DEVELOPER,
                                err=True,
                            )

                # Show user-friendly message
                error_msg = self._format_user_error(e)
                if show_progress:
                    echo(f"✗ {error_msg}", err=True, log=False)

                batch_results = {
                    "batch": batch_num,
                    "files": batch,
                    "result": None,
                    "error": error_msg,
                }
                all_results.append(batch_results)
                files_processed += len(batch)
                files_with_issues += len(batch)  # Count errored files as having issues

                # Move to next batch after error
                i += batch_size

        return all_results

    def has_findings(self, result_text: str) -> bool:
        """
        Check if the conformance result has any findings (issues).

        MCP server returns markdown format only, so we parse that directly.

        Args:
            result_text: Markdown result from conformance check

        Returns:
            True if there are findings/issues, False otherwise
        """
        # Check for overall result status
        if "Result: FAIL" in result_text:
            return True
        # Also check for check-level failures, warnings, or findings
        if any(
            indicator in result_text
            for indicator in [
                ": `fail`",
                "ERROR",
                "WARNING",
                "Finding:",
            ]
        ):
            return True
        return False


def parse_conformance_results(
    results: list[dict[str, Any]],
    file_metadata: dict[str, dict[str, Any]] | None = None,
) -> ConformanceReport:
    """
    Parse conformance check results into structured data models.

    Args:
        results: List of batch results from check_conformance
        file_metadata: Optional file metadata for LOC tracking

    Returns:
        ConformanceReport with parsed and aggregated results
    """
    return ConformanceParser.parse_all_batches(results, file_metadata)
