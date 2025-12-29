"""Subprocess transport for CLI communication."""

import asyncio
import json
import os
from collections.abc import AsyncIterable, AsyncIterator
from typing import Any

from .._binary import get_cli_path
from ..types import AppendSystemPrompt, CodeBuddyAgentOptions
from .base import Transport


class SubprocessTransport(Transport):
    """Transport that communicates with CLI via subprocess."""

    def __init__(
        self,
        options: CodeBuddyAgentOptions,
        prompt: str | AsyncIterable[dict[str, Any]] | None = None,
    ):
        self.options = options
        self.prompt = prompt
        self._process: asyncio.subprocess.Process | None = None
        self._closed = False

    def _get_cli_path(self) -> str:
        """Get the path to CLI executable."""
        # User-specified path takes highest precedence
        if self.options.codebuddy_code_path:
            return str(self.options.codebuddy_code_path)

        # Use the binary resolver (env var -> package binary -> monorepo)
        return get_cli_path()

    def _build_args(self) -> list[str]:
        """Build CLI arguments from options."""
        args = [
            "--input-format",
            "stream-json",
            "--verbose",
            "--output-format",
            "stream-json",
        ]
        opts = self.options

        # Model options
        if opts.model:
            args.extend(["--model", opts.model])
        if opts.fallback_model:
            args.extend(["--fallback-model", opts.fallback_model])

        # Permission options
        if opts.permission_mode:
            args.extend(["--permission-mode", opts.permission_mode])

        # Turn limits
        if opts.max_turns:
            args.extend(["--max-turns", str(opts.max_turns)])

        # Session options
        if opts.continue_conversation:
            args.append("--continue")
        if opts.resume:
            args.extend(["--resume", opts.resume])
        if opts.fork_session:
            args.append("--fork-session")

        # Tool options
        if opts.allowed_tools:
            args.extend(["--allowedTools", ",".join(opts.allowed_tools)])
        if opts.disallowed_tools:
            args.extend(["--disallowedTools", ",".join(opts.disallowed_tools)])

        # MCP options
        if opts.mcp_servers and isinstance(opts.mcp_servers, dict):
            args.extend(["--mcp-config", json.dumps({"mcpServers": opts.mcp_servers})])

        # Settings
        # SDK default: don't load any filesystem settings for clean environment isolation
        # When setting_sources is explicitly provided (including empty list), use it
        # When not provided (None), default to 'none' for SDK isolation
        if opts.setting_sources is not None:
            value = "none" if len(opts.setting_sources) == 0 else ",".join(opts.setting_sources)
            args.extend(["--setting-sources", value])
        else:
            # SDK default behavior: no filesystem settings loaded
            args.extend(["--setting-sources", "none"])

        # Output options
        if opts.include_partial_messages:
            args.append("--include-partial-messages")

        # System prompt options
        if opts.system_prompt is not None:
            if isinstance(opts.system_prompt, str):
                args.extend(["--system-prompt", opts.system_prompt])
            elif isinstance(opts.system_prompt, AppendSystemPrompt):
                args.extend(["--append-system-prompt", opts.system_prompt.append])

        # Extra args (custom flags)
        for flag, value in opts.extra_args.items():
            if value is None:
                args.append(f"--{flag}")
            else:
                args.extend([f"--{flag}", value])

        return args

    async def connect(self) -> None:
        """Start the subprocess."""
        cli_path = self._get_cli_path()
        args = self._build_args()
        cwd = str(self.options.cwd) if self.options.cwd else os.getcwd()

        env = {
            **os.environ,
            **self.options.env,
            "CODEBUDDY_CODE_ENTRYPOINT": "sdk-py",
        }

        self._process = await asyncio.create_subprocess_exec(
            cli_path,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        # Start stderr reader if callback provided
        if self.options.stderr and self._process.stderr:
            asyncio.create_task(self._read_stderr())

    async def _read_stderr(self) -> None:
        """Read stderr and call callback."""
        if self._process and self._process.stderr and self.options.stderr:
            async for line in self._process.stderr:
                self.options.stderr(line.decode())

    async def read(self) -> AsyncIterator[str]:
        """Read lines from stdout."""
        if not self._process or not self._process.stdout:
            return

        async for line in self._process.stdout:
            if self._closed:
                break
            yield line.decode().strip()

    async def write(self, data: str) -> None:
        """Write data to stdin."""
        if self._process and self._process.stdin:
            self._process.stdin.write((data + "\n").encode())
            await self._process.stdin.drain()

    async def close(self) -> None:
        """Close the subprocess."""
        if self._closed:
            return

        self._closed = True

        if self._process:
            self._process.kill()
            await self._process.wait()
