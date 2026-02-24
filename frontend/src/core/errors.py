class FrontendError(Exception):
    """Base frontend error."""


class BackendConnectionError(FrontendError):
    """Raised when backend is unreachable."""


class BackendResponseError(FrontendError):
    """Raised when backend returns an invalid payload."""


class InputValidationError(FrontendError):
    """Raised when user input is invalid."""