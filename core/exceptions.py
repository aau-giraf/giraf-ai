class GirafAIError(Exception):
    pass


class ProviderError(GirafAIError):
    """Raised when an AI provider call fails."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class AuthenticationError(GirafAIError):
    """Raised when JWT validation fails."""


class MalformedClaimError(GirafAIError):
    """Raised when a JWT claim has an unexpected format."""
