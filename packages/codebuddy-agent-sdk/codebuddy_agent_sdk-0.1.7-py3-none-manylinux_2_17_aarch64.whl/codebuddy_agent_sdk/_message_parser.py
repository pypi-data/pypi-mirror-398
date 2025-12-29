"""Message parser for CLI output."""

from typing import Any

from .types import (
    AssistantMessage,
    ContentBlock,
    Message,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def parse_content_block(data: dict[str, Any]) -> ContentBlock | None:
    """Parse a content block from raw data."""
    block_type = data.get("type")

    if block_type == "text":
        return TextBlock(text=data.get("text", ""))

    if block_type == "thinking":
        return ThinkingBlock(
            thinking=data.get("thinking", ""),
            signature=data.get("signature", ""),
        )

    if block_type == "tool_use":
        return ToolUseBlock(
            id=data.get("id", ""),
            name=data.get("name", ""),
            input=data.get("input", {}),
        )

    if block_type == "tool_result":
        return ToolResultBlock(
            tool_use_id=data.get("tool_use_id", ""),
            content=data.get("content"),
            is_error=data.get("is_error"),
        )

    return None


def parse_content_blocks(content: list[dict[str, Any]]) -> list[ContentBlock]:
    """Parse a list of content blocks."""
    blocks: list[ContentBlock] = []
    for item in content:
        block = parse_content_block(item)
        if block:
            blocks.append(block)
    return blocks


def parse_message(data: dict[str, Any]) -> Message | None:
    """Parse a message from raw JSON data."""
    msg_type = data.get("type")

    if msg_type == "user":
        message_data = data.get("message", {})
        content = message_data.get("content", "")
        if isinstance(content, list):
            content = parse_content_blocks(content)
        return UserMessage(
            content=content,
            uuid=data.get("uuid"),
            parent_tool_use_id=data.get("parent_tool_use_id"),
        )

    if msg_type == "assistant":
        message_data = data.get("message", {})
        content = message_data.get("content", [])
        return AssistantMessage(
            content=parse_content_blocks(content) if isinstance(content, list) else [],
            model=data.get("model", ""),
            parent_tool_use_id=data.get("parent_tool_use_id"),
            error=data.get("error"),
        )

    if msg_type == "system":
        return SystemMessage(
            subtype=data.get("subtype", ""),
            data=data,
        )

    if msg_type == "result":
        return ResultMessage(
            subtype=data.get("subtype", ""),
            duration_ms=data.get("duration_ms", 0),
            duration_api_ms=data.get("duration_api_ms", 0),
            is_error=data.get("is_error", False),
            num_turns=data.get("num_turns", 0),
            session_id=data.get("session_id", ""),
            total_cost_usd=data.get("total_cost_usd"),
            usage=data.get("usage"),
            result=data.get("result"),
        )

    if msg_type == "stream_event":
        return StreamEvent(
            uuid=data.get("uuid", ""),
            session_id=data.get("session_id", ""),
            event=data.get("event", {}),
            parent_tool_use_id=data.get("parent_tool_use_id"),
        )

    return None
