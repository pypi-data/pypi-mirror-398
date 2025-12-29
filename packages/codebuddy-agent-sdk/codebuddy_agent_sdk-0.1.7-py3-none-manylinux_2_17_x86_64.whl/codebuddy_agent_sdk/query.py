"""Query function for one-shot interactions with CodeBuddy."""

import json
import os
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import asdict
from typing import Any

from ._message_parser import parse_message
from .transport import SubprocessTransport, Transport
from .types import (
    AppendSystemPrompt,
    CanUseToolOptions,
    CodeBuddyAgentOptions,
    HookMatcher,
    Message,
    ResultMessage,
)


async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: CodeBuddyAgentOptions | None = None,
    transport: Transport | None = None,
) -> AsyncIterator[Message]:
    """
    Query CodeBuddy for one-shot or unidirectional streaming interactions.

    This function is ideal for simple, stateless queries where you don't need
    bidirectional communication or conversation management. For interactive,
    stateful conversations, use CodeBuddySDKClient instead.

    Args:
        prompt: The prompt to send to CodeBuddy. Can be a string for single-shot
                queries or an AsyncIterable[dict] for streaming mode.
        options: Optional configuration (defaults to CodeBuddyAgentOptions() if None).
        transport: Optional transport implementation. If provided, this will be used
                  instead of the default subprocess transport.

    Yields:
        Messages from the conversation.

    Example:
        ```python
        async for message in query(prompt="What is 2+2?"):
            print(message)
        ```
    """
    if options is None:
        options = CodeBuddyAgentOptions()

    os.environ["CODEBUDDY_CODE_ENTRYPOINT"] = "sdk-py"

    if transport is None:
        transport = SubprocessTransport(options=options, prompt=prompt)

    await transport.connect()

    try:
        await _send_initialize(transport, options)
        await _send_prompt(transport, prompt)

        async for line in transport.read():
            if not line:
                continue

            try:
                data = json.loads(line)

                # Handle control requests (hooks)
                if data.get("type") == "control_request":
                    await _handle_control_request(transport, data, options)
                    continue

                message = parse_message(data)
                if message:
                    yield message

                    if isinstance(message, ResultMessage):
                        break

            except json.JSONDecodeError:
                continue  # Ignore non-JSON lines

    finally:
        await transport.close()


async def _send_initialize(transport: Transport, options: CodeBuddyAgentOptions) -> None:
    """Send initialization control request."""
    hooks_config = _build_hooks_config(options.hooks) if options.hooks else None
    agents_config = (
        {name: asdict(agent) for name, agent in options.agents.items()}
        if options.agents
        else None
    )

    # 解析 system_prompt 配置
    system_prompt: str | None = None
    append_system_prompt: str | None = None
    if isinstance(options.system_prompt, str):
        system_prompt = options.system_prompt
    elif isinstance(options.system_prompt, AppendSystemPrompt):
        append_system_prompt = options.system_prompt.append

    request = {
        "type": "control_request",
        "request_id": f"init_{id(options)}",
        "request": {
            "subtype": "initialize",
            "hooks": hooks_config,
            "systemPrompt": system_prompt,
            "appendSystemPrompt": append_system_prompt,
            "agents": agents_config,
        },
    }
    await transport.write(json.dumps(request))


async def _send_prompt(
    transport: Transport, prompt: str | AsyncIterable[dict[str, Any]]
) -> None:
    """Send user prompt."""
    if isinstance(prompt, str):
        message = {
            "type": "user",
            "session_id": "",
            "message": {"role": "user", "content": prompt},
            "parent_tool_use_id": None,
        }
        await transport.write(json.dumps(message))
    else:
        async for msg in prompt:
            await transport.write(json.dumps(msg))


async def _handle_control_request(
    transport: Transport,
    data: dict[str, Any],
    options: CodeBuddyAgentOptions,
) -> None:
    """Handle control request from CLI."""
    request_id = data.get("request_id", "")
    request = data.get("request", {})
    subtype = request.get("subtype", "")

    if subtype == "hook_callback":
        # Handle hook callback
        callback_id = request.get("callback_id", "")
        hook_input = request.get("input", {})
        tool_use_id = request.get("tool_use_id")

        # Find and execute the hook
        response = await _execute_hook(callback_id, hook_input, tool_use_id, options)

        # Send response
        control_response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": response,
            },
        }
        await transport.write(json.dumps(control_response))

    elif subtype == "can_use_tool":
        await _handle_permission_request(transport, request_id, request, options)


async def _handle_permission_request(
    transport: Transport,
    request_id: str,
    request: dict[str, Any],
    options: CodeBuddyAgentOptions,
) -> None:
    """Handle permission request from CLI."""
    tool_name = request.get("tool_name", "")
    input_data = request.get("input", {})
    tool_use_id = request.get("tool_use_id", "")
    agent_id = request.get("agent_id")

    can_use_tool = options.can_use_tool

    # Default deny if no callback provided
    if not can_use_tool:
        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": {
                    "allowed": False,
                    "reason": "No permission handler provided",
                    "tool_use_id": tool_use_id,
                },
            },
        }
        await transport.write(json.dumps(response))
        return

    try:
        callback_options = CanUseToolOptions(
            tool_use_id=tool_use_id,
            signal=None,
            agent_id=agent_id,
            suggestions=request.get("permission_suggestions"),
            blocked_path=request.get("blocked_path"),
            decision_reason=request.get("decision_reason"),
        )

        result = await can_use_tool(tool_name, input_data, callback_options)

        if result.behavior == "allow":
            response_data = {
                "allowed": True,
                "updatedInput": result.updated_input,
                "tool_use_id": tool_use_id,
            }
        else:
            response_data = {
                "allowed": False,
                "reason": result.message,
                "interrupt": result.interrupt,
                "tool_use_id": tool_use_id,
            }

        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": response_data,
            },
        }
        await transport.write(json.dumps(response))

    except Exception as e:
        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": {
                    "allowed": False,
                    "reason": str(e),
                    "tool_use_id": tool_use_id,
                },
            },
        }
        await transport.write(json.dumps(response))


async def _execute_hook(
    callback_id: str,
    hook_input: dict[str, Any],
    tool_use_id: str | None,
    options: CodeBuddyAgentOptions,
) -> dict[str, Any]:
    """Execute a hook callback."""
    if not options.hooks:
        return {"continue_": True}

    # Parse callback_id: hook_{event}_{matcherIndex}_{hookIndex}
    parts = callback_id.split("_")
    if len(parts) < 4:
        return {"continue_": True}

    event = parts[1]
    try:
        matcher_idx = int(parts[2])
        hook_idx = int(parts[3])
    except ValueError:
        return {"continue_": True}

    # Find the hook
    matchers = options.hooks.get(event)  # type: ignore[arg-type]
    if not matchers or matcher_idx >= len(matchers):
        return {"continue_": True}

    matcher = matchers[matcher_idx]
    if hook_idx >= len(matcher.hooks):
        return {"continue_": True}

    hook = matcher.hooks[hook_idx]

    try:
        result = await hook(hook_input, tool_use_id, {"signal": None})
        return dict(result)
    except Exception as e:
        return {"continue_": False, "stopReason": str(e)}


def _build_hooks_config(
    hooks: dict[Any, list[HookMatcher]] | None,
) -> dict[str, list[dict[str, Any]]] | None:
    """Build hooks configuration for CLI."""
    if not hooks:
        return None

    config: dict[str, list[dict[str, Any]]] = {}

    for event, matchers in hooks.items():
        config[str(event)] = [
            {
                "matcher": m.matcher,
                "hookCallbackIds": [
                    f"hook_{event}_{i}_{j}" for j, _ in enumerate(m.hooks)
                ],
                "timeout": m.timeout,
            }
            for i, m in enumerate(matchers)
        ]

    return config if config else None
