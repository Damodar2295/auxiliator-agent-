"""Safe domain errors for governed intelligence operations."""


class IntelligenceError(Exception):
    """Base error that may be translated to a controlled API response."""


class RegistryValidationError(IntelligenceError):
    """A registry definition is invalid or references an unknown dependency."""


class IntentAmbiguousError(IntelligenceError):
    """A request cannot be routed to one Skill deterministically."""

    def __init__(self, candidates: list[str]):
        super().__init__("Intent is ambiguous; specify a Skill or clarify the request")
        self.candidates = candidates


class AuthorizationDeniedError(IntelligenceError):
    """The current identity lacks the required permission."""
