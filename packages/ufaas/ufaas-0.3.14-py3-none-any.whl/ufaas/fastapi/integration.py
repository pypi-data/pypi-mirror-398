"""FastAPI integration utilities for UFaaS."""

from fastapi import Request
from fastapi.responses import JSONResponse

from ..exceptions import UFaaSException


def ufaas_exception_handler(
    request: Request, exc: UFaaSException
) -> JSONResponse:
    """
    Handle UFaaS exceptions in FastAPI.

    Args:
        request: FastAPI request object
        exc: UFaaS exception to handle

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "error": exc.error},
    )


EXCEPTION_HANDLERS = {UFaaSException: ufaas_exception_handler}
