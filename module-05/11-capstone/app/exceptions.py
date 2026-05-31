"""
exceptions.py

Custom exception classes for Caduceus decision-app API.
Every endpoint raises these -- never raw HTTPException.
Global handlers registered in main.py produce consistent JSON error format.
"""
from fastapi import Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class NotFoundException(Exception):
    """Resource not found (404)."""
    def __init__(self, resource: str, identifier: str | int):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' not found")


class DuplicateException(Exception):
    """Unique constraint violation (409)."""
    def __init__(self, resource: str, field: str, value: str):
        self.resource = resource
        self.field = field
        self.value = value
        super().__init__(f"{resource} with {field}='{value}' already exists")


class ForbiddenException(Exception):
    """
    Authorization failure (403).
    Analyst can read all decisions; only the author can modify.
    """
    def __init__(self, action: str = "perform this action"):
        self.action = action
        super().__init__(f"You do not have permission to {action}")


class BadRequestException(Exception):
    """Invalid business logic (400)."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": str(exc),
            "resource": exc.resource,
            "identifier": str(exc.identifier),
        },
    )


async def duplicate_handler(request: Request, exc: DuplicateException) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "duplicate",
            "message": str(exc),
            "resource": exc.resource,
            "field": exc.field,
            "value": exc.value,
        },
    )


async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": "forbidden",
            "message": str(exc),
        },
    )


async def bad_request_handler(request: Request, exc: BadRequestException) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "bad_request",
            "message": exc.detail,
        },
    )
