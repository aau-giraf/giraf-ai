class GirafAIError(Exception):
    pass


class ProviderError(GirafAIError):
    """Raised when an AI provider call fails."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class InvalidRequestError(GirafAIError):
    """Raised for invalid generation parameters."""

    pass
