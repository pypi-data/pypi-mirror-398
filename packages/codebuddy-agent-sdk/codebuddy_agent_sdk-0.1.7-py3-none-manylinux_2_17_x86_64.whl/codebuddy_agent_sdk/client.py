"""CodeBuddy SDK Client for interactive conversations."""

import json
import os
from collections.abc import AsyncIterable, AsyncIterator
from typing import Any

from ._errors import CLIConnectionError
from ._message_parser import parse_message
from .transport import SubprocessTransport, Transport
from .types import CanUseToolOptions, CodeBuddyAgentOptions, Message, ResultMessage


class CodeBuddySDKClient:
    """
    Client for bidirectional, interactive conversations with CodeBuddy.

    This client provides full control over the conversation flow with support
    for streaming, interrupts, and dynamic message sending. For simple one-shot
    queries, consider using the query() function instead.

    Key features:
    - Bidirectional: Send and receive messages at any time
    - Stateful: Maintains conversation context across messages
    - Interactive: Send follow-ups based on responses
    - Control flow: Support for interrupts and session management

    Example:
        ```python
        async with CodeBuddySDKClient() as client:
            await client.query("Hello!")
            async for msg in client.receive_response():
                print(msg)
        ```
    """

    def __init__(
        self,
        options: CodeBuddyAgentOptions | None = None,
        transport: Transport | None = None,
    ):
        """Initialize CodeBuddy SDK client."""
        self.options = options or CodeBuddyAgentOptions()
        self._custom_transport = transport
        self._transport: Transport | None = None
        self._connected = False

        os.environ["CODEBUDDY_CODE_ENTRYPOINT"] = "sdk-py-client"

    async def connect(
        self, prompt: str | AsyncIterable[dict[str, Any]] | None = None
    ) -> None:
        """Connect to CodeBuddy with an optional initial prompt."""
        if self._custom_transport:
            self._transport = self._custom_transport
        else:
            self._transport = SubprocessTransport(
                options=self.options,
                prompt=prompt,
            )

        await self._transport.connect()
        self._connected = True
        await self._send_initialize()

    async def _send_initialize(self) -> None:
        """Send initialization control request."""
        if not self._transport:
            return

        request = {
            "type": "control_request",
            "request_id": f"init_{id(self)}",
            "request": {"subtype": "initialize"},
        }
        await self._transport.write(json.dumps(request))

    async def query(
        self,
        prompt: str | AsyncIterable[dict[str, Any]],
        session_id: str = "default",
    ) -> None:
        """
        Send a new request.

        Args:
            prompt: Either a string message or an async iterable of message dicts
            session_id: Session identifier for the conversation
        """
        if not self._connected or not self._transport:
            raise CLIConnectionError("Not connected. Call connect() first.")

        if isinstance(prompt, str):
            message = {
                "type": "user",
                "message": {"role": "user", "content": prompt},
                "parent_tool_use_id": None,
                "session_id": session_id,
            }
            await self._transport.write(json.dumps(message))
        else:
            async for msg in prompt:
                if "session_id" not in msg:
                    msg["session_id"] = session_id
                await self._transport.write(json.dumps(msg))

    async def receive_messages(self) -> AsyncIterator[Message]:
        """Receive all messages from CodeBuddy."""
        if not self._transport:
            raise CLIConnectionError("Not connected.")

        async for line in self._transport.read():
            if not line:
                continue

            try:
                data = json.loads(line)

                # Handle control requests (permissions, hooks)
                if data.get("type") == "control_request":
                    await self._handle_control_request(data)
                    continue

                message = parse_message(data)
                if message:
                    yield message
            except json.JSONDecodeError:
                continue

    async def _handle_control_request(self, data: dict[str, Any]) -> None:
        """Handle control request from CLI."""
        if not self._transport:
            return

        request_id = data.get("request_id", "")
        request = data.get("request", {})
        subtype = request.get("subtype", "")

        if subtype == "can_use_tool":
            await self._handle_permission_request(request_id, request)
        elif subtype == "hook_callback":
            # Default: continue
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": request_id,
                    "response": {"continue": True},
                },
            }
            await self._transport.write(json.dumps(response))

    async def _handle_permission_request(
        self, request_id: str, request: dict[str, Any]
    ) -> None:
        """Handle permission request from CLI."""
        if not self._transport:
            return

        tool_name = request.get("tool_name", "")
        input_data = request.get("input", {})
        tool_use_id = request.get("tool_use_id", "")
        agent_id = request.get("agent_id")

        can_use_tool = self.options.can_use_tool

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
            await self._transport.write(json.dumps(response))
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
            await self._transport.write(json.dumps(response))

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
            await self._transport.write(json.dumps(response))

    async def receive_response(self) -> AsyncIterator[Message]:
        """
        Receive messages until and including a ResultMessage.

        Yields each message as it's received and terminates after
        yielding a ResultMessage.
        """
        async for message in self.receive_messages():
            yield message
            if isinstance(message, ResultMessage):
                return

    async def interrupt(self) -> None:
        """Send interrupt signal."""
        if not self._transport:
            raise CLIConnectionError("Not connected.")

        request = {
            "type": "control_request",
            "request_id": f"interrupt_{id(self)}",
            "request": {"subtype": "interrupt"},
        }
        await self._transport.write(json.dumps(request))

    async def set_permission_mode(self, mode: str) -> None:
        """Change permission mode during conversation."""
        if not self._transport:
            raise CLIConnectionError("Not connected.")

        request = {
            "type": "control_request",
            "request_id": f"perm_{id(self)}",
            "request": {"subtype": "set_permission_mode", "mode": mode},
        }
        await self._transport.write(json.dumps(request))

    async def set_model(self, model: str | None = None) -> None:
        """Change the AI model during conversation."""
        if not self._transport:
            raise CLIConnectionError("Not connected.")

        request = {
            "type": "control_request",
            "request_id": f"model_{id(self)}",
            "request": {"subtype": "set_model", "model": model},
        }
        await self._transport.write(json.dumps(request))

    async def disconnect(self) -> None:
        """Disconnect from CodeBuddy."""
        if self._transport:
            await self._transport.close()
            self._transport = None
        self._connected = False

    async def __aenter__(self) -> "CodeBuddySDKClient":
        """Enter async context - automatically connects."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> bool:
        """Exit async context - always disconnects."""
        await self.disconnect()
        return False
