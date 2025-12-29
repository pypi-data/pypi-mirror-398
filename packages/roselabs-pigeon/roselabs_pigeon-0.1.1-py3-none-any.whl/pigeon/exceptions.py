"""Exception classes for the Pigeon SDK."""


class PigeonError(Exception):
    """Base exception for Pigeon SDK."""

    pass


class PigeonAPIError(PigeonError):
    """API returned an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class PigeonValidationError(PigeonError):
    """Invalid request parameters."""

    pass


class PigeonConfigError(PigeonError):
    """Invalid SDK configuration."""

    pass
