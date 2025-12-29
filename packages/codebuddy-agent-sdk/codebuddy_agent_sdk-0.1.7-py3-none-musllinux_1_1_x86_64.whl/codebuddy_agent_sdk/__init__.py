"""CodeBuddy Agent SDK for Python."""

from ._errors import (
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    CodeBuddySDKError,
    ProcessError,
)
from ._version import __version__
from .client import CodeBuddySDKClient
from .query import query
from .transport import Transport
from .types import (
    AgentDefinition,
    AppendSystemPrompt,
    AskUserQuestionInput,
    AskUserQuestionOption,
    AskUserQuestionQuestion,
    AssistantMessage,
    CanUseTool,
    CanUseToolOptions,
    CodeBuddyAgentOptions,
    ContentBlock,
    HookCallback,
    HookContext,
    HookEvent,
    HookJSONOutput,
    HookMatcher,
    McpServerConfig,
    Message,
    PermissionMode,
    PermissionResult,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    SettingSource,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

__all__ = [
    # Main API
    "query",
    "CodeBuddySDKClient",
    "Transport",
    "__version__",
    # Types - Permission
    "PermissionMode",
    # Types - Messages
    "Message",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "StreamEvent",
    # Types - Content blocks
    "ContentBlock",
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    # Types - Configuration
    "CodeBuddyAgentOptions",
    "AgentDefinition",
    "AppendSystemPrompt",
    "SettingSource",
    # Types - Permission
    "CanUseTool",
    "CanUseToolOptions",
    "PermissionResult",
    "PermissionResultAllow",
    "PermissionResultDeny",
    # Types - AskUserQuestion
    "AskUserQuestionOption",
    "AskUserQuestionQuestion",
    "AskUserQuestionInput",
    # Types - Hooks
    "HookEvent",
    "HookCallback",
    "HookMatcher",
    "HookJSONOutput",
    "HookContext",
    # Types - MCP
    "McpServerConfig",
    # Errors
    "CodeBuddySDKError",
    "CLIConnectionError",
    "CLINotFoundError",
    "CLIJSONDecodeError",
    "ProcessError",
]
