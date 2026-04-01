class GirafAIError(Exception):
    pass


class ProviderError(GirafAIError):
    """Raised when an AI provider call fails."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class AuthenticationError(GirafAIError):
    """Raised when JWT validation fails."""


class UnsupportedFormatError(GirafAIError):
    """Raised when a requested format is not supported by the active provider."""
