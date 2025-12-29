"""Error definitions for CodeBuddy Agent SDK."""


class CodeBuddySDKError(Exception):
    """Base exception for CodeBuddy SDK errors."""

    pass


class CLIConnectionError(CodeBuddySDKError):
    """Raised when connection to CLI fails or is not established."""

    pass


class CLINotFoundError(CodeBuddySDKError):
    """Raised when CLI executable is not found."""

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        arch: str | None = None,
    ):
        super().__init__(message)
        self.platform = platform
        self.arch = arch


class CLIJSONDecodeError(CodeBuddySDKError):
    """Raised when JSON decoding from CLI output fails."""

    pass


class ProcessError(CodeBuddySDKError):
    """Raised when CLI process encounters an error."""

    pass
