"""Exception classes for UFaaS application."""

error_messages: dict[str, str] = {}


class UFaaSError(Exception):
    """UFaaSError is a base exception for all UFaaS exceptions."""

    def __init__(
        self,
        status_code: int,
        error: str,
        detail: str | None = None,
        message: dict | None = None,
        **kwargs: dict,
    ) -> None:
        """
        Initialize UFaaS error.

        Args:
            status_code: HTTP status code
            error: Error code string
            detail: Optional detail message
            message: Optional message dictionary
            **kwargs: Additional keyword arguments
        """
        self.status_code = status_code
        self.error = error
        msg: dict = {}
        if message is None:
            if detail:
                msg["en"] = detail
            else:
                msg["en"] = error_messages.get(error, error)
        else:
            msg = message

        self.message = msg
        self.detail = detail or str(self.message)
        self.data = kwargs
        super().__init__(detail)


class InsufficientFundsError(UFaaSError):
    """Exception raised for insufficient funds."""

    def __init__(self, detail: str | None = None) -> None:
        """
        Initialize InsufficientFundsError.

        Args:
            detail: Optional detail message
        """
        super().__init__(
            status_code=402, error="insufficient_funds", detail=detail
        )


class InvalidRequestError(UFaaSError):
    """Exception raised for invalid requests."""

    def __init__(self, detail: str | None = None) -> None:
        """
        Initialize InvalidRequestError.

        Args:
            detail: Optional detail message
        """
        super().__init__(
            status_code=400, error="invalid_request", detail=detail
        )


class UnauthorizedError(UFaaSError):
    """Exception raised for unauthorized access."""

    def __init__(self, detail: str | None = None) -> None:
        """
        Initialize UnauthorizedError.

        Args:
            detail: Optional detail message
        """
        super().__init__(status_code=401, error="unauthorized", detail=detail)


class ForbiddenError(UFaaSError):
    """Exception raised for forbidden access."""

    def __init__(self, detail: str | None = None) -> None:
        """
        Initialize ForbiddenError.

        Args:
            detail: Optional detail message
        """
        super().__init__(status_code=403, error="forbidden", detail=detail)


class NotFoundError(UFaaSError):
    """Exception raised for resources not found."""

    def __init__(self, detail: str | None = None) -> None:
        """
        Initialize NotFoundError.

        Args:
            detail: Optional detail message
        """
        super().__init__(status_code=404, error="not_found", detail=detail)
