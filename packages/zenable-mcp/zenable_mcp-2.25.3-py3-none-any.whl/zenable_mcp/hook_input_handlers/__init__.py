"""Hook input handlers for processing different input sources and formats."""

from zenable_mcp.hook_input_handlers.base import (
    HookInputContext,
    HookInputFormat,
    HookOutputConfig,
    InputHandler,
)
from zenable_mcp.hook_input_handlers.claude_code import ClaudeCodeInputHandler
from zenable_mcp.hook_input_handlers.cursor import CursorInputHandler
from zenable_mcp.hook_input_handlers.registry import InputHandlerRegistry
from zenable_mcp.hook_input_handlers.windsurf import WindsurfInputHandler

__all__ = [
    "InputHandler",
    "InputHandlerRegistry",
    "HookInputContext",
    "HookInputFormat",
    "HookOutputConfig",
    "ClaudeCodeInputHandler",
    "CursorInputHandler",
    "WindsurfInputHandler",
]
