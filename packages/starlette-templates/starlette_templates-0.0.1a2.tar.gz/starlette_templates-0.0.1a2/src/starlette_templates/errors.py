"""
Error handling, custom exceptions, and JSON:API compliant error responses for starlette_templates framework.

Routes should raise `AppException` for application-specific errors, with the appropriate HTTP status code
and error details. The framework will handle rendering JSON or HTML error responses based on the request type.

Example:
```python
from starlette.requests import Request
from starlette_templates.errors import AppException, ErrorCode

async def example(request: Request):
    raise AppException(
        detail="Custom resource not found",
        status_code=404,
        code=ErrorCode.NOT_FOUND,
    )
```
"""

import logging
import traceback
import linecache
import typing as t
from enum import Enum
from jinja2 import Environment
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from pydantic import BaseModel, ValidationError
from starlette.responses import Response, HTMLResponse

logger = logging.getLogger("starlette_templates.errors")

# HTTP error messages mapping
HTTP_ERROR_MESSAGES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Page Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


def get_error_title(status_code: int) -> str:
    """Get human-readable error title for status code.

    Args:
        status_code: HTTP status code

    Returns:
        Human-readable error title, or "Error" if status code not recognized

    Example:
        >>> get_error_title(404)
        'Page Not Found'
        >>> get_error_title(999)
        'Error'
    """
    return HTTP_ERROR_MESSAGES.get(status_code, "Error")


class ErrorCode(str, Enum):
    """Error codes for API responses following JSON:API specification."""

    INTERNAL_ERROR = "internal_error"
    """Internal server error not caused by client request."""
    INVALID_REQUEST = "invalid_request"
    """The request is malformed or contains invalid parameters."""
    INVALID_PARAMETER = "invalid_parameter"
    """A specific parameter in the request is invalid."""
    NOT_FOUND = "not_found"
    """The requested resource could not be found."""
    VALIDATION_ERROR = "validation_error"
    """The request data failed validation checks."""
    UNAUTHORIZED = "unauthorized"
    """Authentication is required and has failed or not been provided."""
    FORBIDDEN = "forbidden"
    """Access to the requested resource is forbidden."""
    METHOD_NOT_ALLOWED = "method_not_allowed"
    """The HTTP method used is not allowed for the requested resource."""


class ErrorSource(BaseModel):
    """JSON:API error source object indicating where the error originated."""

    pointer: str | None = None
    parameter: str | None = None
    header: str | None = None


class AppException(Exception):
    """Base exception for all application errors with JSON:API compliance.

    This exception provides structured error information that can be
    rendered as either JSON (for API requests) or HTML (for browser requests).

    Args:
        detail: Human-readable description of the error
        status_code: HTTP status code (default: 400)
        code: Machine-readable error code
        source: Location of the error (JSON pointer, parameter name, etc.)
        meta: Additional metadata about the error

    Example:
        ```python
        raise AppException(
            detail="User with email 'john@example.com' already exists",
            status_code=409,
            code=ErrorCode.DUPLICATE_RESOURCE,
            source=ErrorSource(parameter="email"),
            meta={"email": "john@example.com"}
        )
        ```
    """

    def __init__(
        self,
        detail: str,
        status_code: int = 400,
        code: ErrorCode | str | None = None,
        source: ErrorSource | None = None,
        meta: dict[str, t.Any] | None = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.code = code if isinstance(code, str) else (code.value if code else None)
        self.source = source
        self.meta = meta
        super().__init__(detail)


class JSONAPIError(BaseModel):
    """JSON:API compliant error object.

    Follows the JSON:API specification for error objects:
    https://jsonapi.org/format/#error-objects
    """

    id: str | None = None
    status: str
    code: str | None = None
    title: str
    detail: str | None = None
    source: ErrorSource | None = None
    meta: dict[str, t.Any] | None = None


class JSONAPIErrorResponse(BaseModel):
    """JSON:API compliant error response containing a list of errors."""

    errors: list[JSONAPIError]


def create_error_response(
    status: int,
    title: str,
    detail: str | None = None,
    code: ErrorCode | str | None = None,
    source: ErrorSource | None = None,
    meta: dict[str, t.Any] | None = None,
) -> JSONResponse:
    """Create a JSON:API compliant error response.

    Args:
        status: HTTP status code
        title: Short, human-readable summary of the error
        detail: Detailed human-readable explanation
        code: Machine-readable error code
        source: Where the error occurred
        meta: Additional metadata

    Returns:
        JSONResponse with JSON:API error format

    Example:
        ```python
        return create_error_response(
            status=404,
            title="Resource not found",
            detail="User with ID 123 does not exist",
            code=ErrorCode.NOT_FOUND,
            source=ErrorSource(parameter="user_id"),
        )
        ```
    """
    code_str = code.value if isinstance(code, ErrorCode) else code

    error = JSONAPIError(
        status=str(status),
        code=code_str,
        title=title,
        detail=detail,
        source=source,
        meta=meta,
    )
    response = JSONAPIErrorResponse(errors=[error])
    return JSONResponse(response.model_dump(exclude_none=True), status_code=status)


def create_validation_error_response(validation_error: ValidationError) -> JSONResponse:
    """Convert Pydantic ValidationError to JSON:API error response.

    This provides detailed information about each validation error including:
    - Which field caused the error
    - What type of validation failed
    - A human-readable description of the problem

    Args:
        validation_error: Pydantic ValidationError instance

    Returns:
        JSONResponse with JSON:API error format containing all validation errors

    Example:
        ```python
        try:
            user = UserModel(**data)
        except ValidationError as e:
            return create_validation_error_response(e)
        ```
    """
    errors = []

    for error in validation_error.errors():
        # Build JSON pointer from error location
        loc = error.get("loc", ())
        if loc:
            # Convert location tuple to JSON pointer format
            # e.g., ('body', 'title') -> '/body/title'
            pointer_parts = []
            for part in loc:
                if isinstance(part, str):
                    pointer_parts.append(part)
                elif isinstance(part, int):
                    pointer_parts.append(str(part))

            json_pointer = "/" + "/".join(pointer_parts) if pointer_parts else None
        else:
            json_pointer = None

        # Get error type and message
        error_type = error.get("type", "validation_error")
        error_msg = error.get("msg", "Validation error")
        error_input = error.get("input")

        # Create human-readable title based on error type
        title_map = {
            "missing": "Missing required field",
            "string_type": "Invalid type: expected string",
            "int_type": "Invalid type: expected integer",
            "bool_type": "Invalid type: expected boolean",
            "dict_type": "Invalid type: expected object",
            "list_type": "Invalid type: expected array",
            "value_error": "Invalid value",
            "type_error": "Invalid type",
        }

        title = title_map.get(error_type, "Validation error")

        # Build detailed message
        field_name = loc[-1] if loc else "field"

        if error_type == "missing":
            detail = f"The required field '{field_name}' is missing from the request."
        elif error_type in ("string_type", "int_type", "bool_type", "dict_type", "list_type"):
            expected_type = error_type.replace("_type", "")
            detail = f"The field '{field_name}' must be a {expected_type}"
            if error_input is not None:
                detail += f", but received: {type(error_input).__name__}"
        else:
            detail = f"The field '{field_name}' has an invalid value: {error_msg}"

        # Create error source
        source = ErrorSource(pointer=json_pointer) if json_pointer else None

        # Add to errors list
        api_error = JSONAPIError(
            status="400",
            code=error_type,
            title=title,
            detail=detail,
            source=source,
            meta={"input": error_input} if error_input is not None else None,
        )
        errors.append(api_error)

    response = JSONAPIErrorResponse(errors=errors)
    return JSONResponse(response.model_dump(exclude_none=True), status_code=400)


def get_frame_info(tb_frame: t.Any, lineno: int, context_lines: int = 5) -> dict[str, t.Any]:
    """Extract detailed information from a traceback frame."""
    filename = tb_frame.f_code.co_filename
    function = tb_frame.f_code.co_name

    code_context = []
    start_line = max(1, lineno - context_lines)
    end_line = lineno + context_lines + 1

    for line_num in range(start_line, end_line):
        line = linecache.getline(filename, line_num)
        if line:
            code_context.append((line_num, line.rstrip("\n")))

    locals_dict = {}
    for name, value in tb_frame.f_locals.items():
        try:
            repr_value = repr(value)
            # Truncate long representations
            if len(repr_value) > 2000:
                repr_value = repr_value[:2000] + "..."
            locals_dict[name] = repr_value
        except Exception:
            locals_dict[name] = "<unable to display>"

    return {
        "filename": filename,
        "lineno": lineno,
        "function": function,
        "code_context": code_context,
        "locals": locals_dict,
    }


def extract_traceback_frames(exc: BaseException, context_lines: int = 5) -> list[dict[str, t.Any]]:
    """Extract all frames from an exception's traceback."""
    frames = []
    tb = exc.__traceback__

    while tb is not None:
        frame_info = get_frame_info(tb.tb_frame, tb.tb_lineno, context_lines)
        frames.append(frame_info)
        tb = tb.tb_next

    return frames


def get_error_context(request: Request, exc: Exception, status_code: int = 500) -> dict[str, t.Any]:
    """Build the full context dictionary for error template rendering."""
    exc_type = type(exc).__name__
    exc_value = str(exc)

    frames = extract_traceback_frames(exc)
    traceback_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    request_headers = dict(request.headers) if hasattr(request, "headers") else {}
    query_params = dict(request.query_params) if hasattr(request, "query_params") else {}
    cookies = dict(request.cookies) if hasattr(request, "cookies") else {}

    client_host = None
    if hasattr(request, "client") and request.client:
        client_host = f"{request.client.host}:{request.client.port}"

    return {
        "status_code": status_code,
        "exc_type": exc_type,
        "exc_value": exc_value,
        "error_title": exc_type,
        "error_message": exc_value or "An unexpected error occurred.",
        "frames": frames,
        "traceback_text": traceback_text,
        "request_method": request.method if hasattr(request, "method") else None,
        "request_url": str(request.url) if hasattr(request, "url") else None,
        "request_path": request.url.path if hasattr(request, "url") else None,
        "client_host": client_host,
        "request_headers": request_headers,
        "query_params": query_params,
        "cookies": cookies,
    }


def wants_json(request: Request) -> bool:
    """Determine if the client prefers JSON response based on Accept header.

    Args:
        request: Starlette Request object

    Returns:
        True if client prefers JSON, False otherwise
    """
    accept = request.headers.get("accept", "")
    # Check if application/json is in Accept header
    return "application/json" in accept


async def render_error_page(
    request: Request,
    status_code: int,
    error_title: str,
    error_message: str,
    jinja_env: Environment,
    debug: bool = False,
    exc: Exception | None = None,
    structured_errors: list[JSONAPIError] | None = None,
) -> Response:
    """Render an error page using custom template or starlette_templates's error.html.

    This will first attempt to load a custom template named after the status code
    (e.g., 404.html, 500.html). If not found, it falls back to starlette_templates's built-in error.html.

    Args:
        request: The request that caused the error
        status_code: HTTP status code
        error_title: Brief error title
        error_message: Detailed error message
        jinja_env: Jinja2 environment for rendering templates
        debug: Whether to include debug information
        exc: The exception that was raised (if any)
        structured_errors: List of JSON:API errors for validation errors

    Returns:
        Response with rendered error page
    """
    # Build context - must include request for @pass_context functions
    context = {
        "request": request,
        "status_code": status_code,
        "error_title": error_title,
        "error_message": error_message,
        "structured_errors": structured_errors,
    }

    # Add debug info if in debug mode and we have an exception
    if debug and exc is not None:
        error_context = get_error_context(request, exc, status_code)
        context.update(error_context)

    # Try to use custom error template (e.g., 404.html, 500.html)
    template_name = f"{status_code}.html"
    try:
        template = jinja_env.get_template(template_name)
        html = await template.render_async(context)
        return HTMLResponse(html, status_code=status_code)
    except Exception:
        pass

    # Fall back to starlette_templates's built-in error.html template
    try:
        template = jinja_env.get_template("error.html")
        html = await template.render_async(context)
        return HTMLResponse(html, status_code=status_code)
    except Exception:
        # Last resort: simple HTML response
        html = f"<h1>{status_code}</h1><p>{error_message}</p>"
        return HTMLResponse(html, status_code=status_code)


async def httpexception_handler(
    request: Request,
    exc: HTTPException,
    jinja_env: Environment,
    debug: bool = False,
) -> Response:
    """Handle HTTP exceptions (404, 500, etc.) with JSON or HTML response.

    Returns JSON:API error format for API requests, HTML error page for browsers.

    Args:
        request: The request that caused the error
        exc: HTTPException that was raised
        jinja_env: Jinja2 environment for rendering templates
        debug: Whether to include debug information

    Returns:
        Response with error details
    """
    status_code = exc.status_code
    error_title = get_error_title(status_code)
    error_message = exc.detail if exc.detail else error_title

    # Log 5xx errors (server errors) - these indicate problems we need to fix
    if status_code >= 500:
        logger.error(
            f"HTTPException {status_code}: {error_message}",
            exc_info=exc,
            extra={
                "status_code": status_code,
                "request_method": request.method if hasattr(request, "method") else None,
                "request_url": str(request.url) if hasattr(request, "url") else None,
            }
        )

    # Map status codes to error codes
    code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        500: ErrorCode.INTERNAL_ERROR,
    }
    error_code = code_map.get(status_code, ErrorCode.INTERNAL_ERROR)

    # Return JSON for API requests
    if wants_json(request):
        return create_error_response(
            status=status_code,
            title=error_title,
            detail=error_message,
            code=error_code,
        )

    # Return HTML for browser requests
    return await render_error_page(
        request,
        status_code,
        error_title,
        error_message,
        jinja_env,
        debug,
        exc if debug else None,
    )


async def exception_handler(
    request: Request,
    exc: Exception,
    jinja_env: Environment,
    debug: bool = False,
) -> Response:
    """Handle uncaught exceptions with JSON or HTML response.

    Provides special handling for:
    - ValidationError: Detailed validation error messages
    - AppException: Custom application errors with structured data
    - General exceptions: Generic 500 error

    Returns JSON:API format for API requests, HTML for browsers.

    Args:
        request: The request that caused the error
        exc: Exception that was raised
        jinja_env: Jinja2 environment for rendering templates
        debug: Whether to include debug information

    Returns:
        Response with error details
    """
    # Log the exception with full traceback for debugging
    # Use different log levels based on exception type
    if isinstance(exc, ValidationError):
        # Validation errors are 400-level client errors, log as warning
        logger.warning(
            f"Validation error: {exc}",
            exc_info=exc if debug else None,
            extra={
                "request_method": request.method if hasattr(request, "method") else None,
                "request_url": str(request.url) if hasattr(request, "url") else None,
                "error_count": len(exc.errors()),
            }
        )
    elif isinstance(exc, AppException):
        # AppException may be client or server error depending on status code
        if exc.status_code >= 500:
            logger.error(
                f"AppException {exc.status_code}: {exc.detail}",
                exc_info=exc,
                extra={
                    "status_code": exc.status_code,
                    "error_code": exc.code,
                    "request_method": request.method if hasattr(request, "method") else None,
                    "request_url": str(request.url) if hasattr(request, "url") else None,
                }
            )
        else:
            logger.warning(
                f"AppException {exc.status_code}: {exc.detail}",
                exc_info=exc if debug else None,
                extra={
                    "status_code": exc.status_code,
                    "error_code": exc.code,
                    "request_method": request.method if hasattr(request, "method") else None,
                    "request_url": str(request.url) if hasattr(request, "url") else None,
                }
            )
    else:
        # All other exceptions are 500 server errors - log with full traceback
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=exc,
            extra={
                "request_method": request.method if hasattr(request, "method") else None,
                "request_url": str(request.url) if hasattr(request, "url") else None,
            }
        )

    # Handle Pydantic ValidationError
    if isinstance(exc, ValidationError):
        # Return JSON for API requests
        if wants_json(request):
            return create_validation_error_response(exc)

        # Return HTML with structured validation errors
        errors = []
        for error in exc.errors():
            loc = error.get("loc", ())
            field_name = loc[-1] if loc else "field"
            error_type = error.get("type", "validation_error")
            error_msg = error.get("msg", "Validation error")

            api_error = JSONAPIError(
                status="400",
                code=error_type,
                title="Validation Error",
                detail=f"Field '{field_name}': {error_msg}",
                source=ErrorSource(parameter=str(field_name)) if field_name else None,
            )
            errors.append(api_error)

        return await render_error_page(
            request,
            400,
            "Validation Error",
            "The request contains invalid data. Please check the fields below.",
            jinja_env,
            debug,
            exc if debug else None,
            structured_errors=errors,
        )

    # Handle custom AppException
    if isinstance(exc, AppException):
        # Return JSON for API requests
        if wants_json(request):
            return create_error_response(
                status=exc.status_code,
                title=exc.__class__.__name__,
                detail=exc.detail,
                code=exc.code,
                source=exc.source,
                meta=exc.meta,
            )

        # Return HTML with structured error
        structured_errors = None
        if exc.source or exc.meta:
            structured_errors = [
                JSONAPIError(
                    status=str(exc.status_code),
                    code=exc.code,
                    title=exc.__class__.__name__,
                    detail=exc.detail,
                    source=exc.source,
                    meta=exc.meta,
                )
            ]

        return await render_error_page(
            request=request,
            status_code=exc.status_code,
            error_title=exc.__class__.__name__,
            error_message=exc.detail,
            jinja_env=jinja_env,
            debug=debug,
            exc=exc if debug else None,
            structured_errors=structured_errors,
        )

    # Handle all other exceptions
    detail = str(exc) if debug else "An unexpected error occurred."

    # Return JSON for API requests
    if wants_json(request):
        return create_error_response(
            status=500,
            title="Internal Server Error",
            detail=detail,
            code=ErrorCode.INTERNAL_ERROR,
        )

    # Return HTML for browser requests
    return await render_error_page(
        request=request,
        status_code=500,
        error_title="Internal Server Error",
        error_message=detail,
        jinja_env=jinja_env,
        debug=debug,
        exc=exc,
    )
