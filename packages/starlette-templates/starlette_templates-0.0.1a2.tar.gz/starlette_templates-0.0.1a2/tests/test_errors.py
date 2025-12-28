"""Tests for starlette_templates.errors module.

This test module demonstrates error handling features including:
- AppException: Custom application exceptions with JSON:API compliance
- ErrorCode: Standardized error code enumeration
- ErrorSource: Indicates where errors originated (pointer, parameter, header)
- JSON:API error responses for API clients
- HTML error pages for browser clients
- Validation error handling with detailed feedback
- HTTP exception handling (404, 500, etc.)
"""
import pytest
from jinja2 import Environment, DictLoader
from pydantic import BaseModel, ValidationError, Field
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.middleware import Middleware
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse
from starlette_templates.middleware import JinjaMiddleware
from starlette_templates.errors import (
    ErrorCode,
    ErrorSource,
    AppException,
    JSONAPIError,
    JSONAPIErrorResponse,
    get_error_title,
    create_error_response,
    create_validation_error_response,
    get_frame_info,
    extract_traceback_frames,
    get_error_context,
    wants_json,
    render_error_page,
    httpexception_handler,
    exception_handler,
)


def test_error_code_enum():
    """Test that ErrorCode enum has expected values."""
    assert ErrorCode.INTERNAL_ERROR == "internal_error"
    assert ErrorCode.INVALID_REQUEST == "invalid_request"
    assert ErrorCode.NOT_FOUND == "not_found"
    assert ErrorCode.VALIDATION_ERROR == "validation_error"
    assert ErrorCode.UNAUTHORIZED == "unauthorized"


def test_error_source():
    """Test ErrorSource model."""
    source = ErrorSource(pointer="/data/attributes/email")
    assert source.pointer == "/data/attributes/email"

    source = ErrorSource(parameter="email")
    assert source.parameter == "email"


def test_app_exception_basic():
    """Test basic AppException creation."""
    exc = AppException("Something went wrong", status_code=400)
    assert exc.detail == "Something went wrong"
    assert exc.status_code == 400
    assert str(exc) == "Something went wrong"


def test_app_exception_with_code():
    """Test AppException with ErrorCode."""
    exc = AppException(
        "Not found",
        status_code=404,
        code=ErrorCode.NOT_FOUND,
    )
    assert exc.code == "not_found"


def test_app_exception_with_source():
    """Test AppException with ErrorSource."""
    source = ErrorSource(parameter="email")
    exc = AppException(
        "Invalid email",
        status_code=400,
        code=ErrorCode.INVALID_PARAMETER,
        source=source,
    )
    assert exc.source.parameter == "email"


def test_app_exception_with_meta():
    """Test AppException with metadata."""
    exc = AppException(
        "Duplicate email",
        status_code=409,
        meta={"email": "test@example.com"},
    )
    assert exc.meta["email"] == "test@example.com"


def test_get_error_title():
    """Test get_error_title function."""
    assert get_error_title(404) == "Page Not Found"
    assert get_error_title(500) == "Internal Server Error"
    assert get_error_title(400) == "Bad Request"
    assert get_error_title(999) == "Error"


def test_create_error_response():
    """Test create_error_response function."""
    response = create_error_response(
        status=404,
        title="Not Found",
        detail="Resource not found",
        code=ErrorCode.NOT_FOUND,
    )

    assert response.status_code == 404
    data = response.body.decode()
    assert "Not Found" in data
    assert "Resource not found" in data


def test_create_error_response_with_source():
    """Test create_error_response with ErrorSource."""
    source = ErrorSource(parameter="id")
    response = create_error_response(
        status=400,
        title="Invalid Parameter",
        detail="ID must be a positive integer",
        code=ErrorCode.INVALID_PARAMETER,
        source=source,
    )

    assert response.status_code == 400
    import json
    data = json.loads(response.body)
    assert data["errors"][0]["source"]["parameter"] == "id"


def test_create_validation_error_response():
    """Test create_validation_error_response function."""
    class User(BaseModel):
        email: str = Field(min_length=5)
        age: int

    try:
        User(email="abc", age="not_an_int")
    except ValidationError as e:
        response = create_validation_error_response(e)

        assert response.status_code == 400
        import json
        data = json.loads(response.body)
        assert "errors" in data
        assert len(data["errors"]) > 0


def test_validation_error_response_structure():
    """Test that validation error response has correct structure."""
    class User(BaseModel):
        name: str
        age: int

    try:
        User(name=123, age="invalid")
    except ValidationError as e:
        response = create_validation_error_response(e)

        import json
        data = json.loads(response.body)
        errors = data["errors"]

        # Check structure
        for error in errors:
            assert "status" in error
            assert error["status"] == "400"
            assert "title" in error
            assert "detail" in error


def test_get_frame_info():
    """Test get_frame_info function."""
    try:
        raise ValueError("Test error")
    except ValueError as e:
        tb = e.__traceback__
        frame_info = get_frame_info(tb.tb_frame, tb.tb_lineno)

        assert "filename" in frame_info
        assert "lineno" in frame_info
        assert "function" in frame_info
        assert "code_context" in frame_info
        assert "locals" in frame_info


def test_extract_traceback_frames():
    """Test extract_traceback_frames function."""
    try:
        raise ValueError("Test error")
    except ValueError as e:
        frames = extract_traceback_frames(e)

        assert len(frames) > 0
        assert "filename" in frames[0]
        assert "lineno" in frames[0]


def test_get_error_context():
    """Test get_error_context function."""
    from starlette.requests import Request
    from starlette.datastructures import Headers

    # Mock request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    }
    request = Request(scope)

    try:
        raise ValueError("Test error")
    except ValueError as e:
        context = get_error_context(request, e, 500)

        assert context["status_code"] == 500
        assert context["exc_type"] == "ValueError"
        assert context["exc_value"] == "Test error"
        assert "frames" in context
        assert "traceback_text" in context


def test_wants_json_with_json_accept():
    """Test wants_json returns True for JSON Accept header."""
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept", b"application/json")],
    }
    request = Request(scope)

    assert wants_json(request) is True


def test_wants_json_without_json_accept():
    """Test wants_json returns False for HTML Accept header."""
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept", b"text/html")],
    }
    request = Request(scope)

    assert wants_json(request) is False


async def test_render_error_page():
    """Test render_error_page function."""
    from starlette.requests import Request

    templates = {
        "error.html": "<h1>{{ status_code }}</h1><p>{{ error_message }}</p>",
    }
    env = Environment(loader=DictLoader(templates), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    request = Request(scope)

    response = await render_error_page(
        request,
        status_code=404,
        error_title="Not Found",
        error_message="Page not found",
        jinja_env=env,
    )

    assert response.status_code == 404
    body = response.body.decode()
    assert "404" in body
    assert "Page not found" in body


async def test_render_error_page_with_custom_template():
    """Test render_error_page uses custom status code template."""
    from starlette.requests import Request

    templates = {
        "404.html": "<h1>Custom 404</h1>",
        "error.html": "<h1>Generic Error</h1>",
    }
    env = Environment(loader=DictLoader(templates), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    request = Request(scope)

    response = await render_error_page(
        request,
        status_code=404,
        error_title="Not Found",
        error_message="Page not found",
        jinja_env=env,
    )

    assert response.status_code == 404
    body = response.body.decode()
    assert "Custom 404" in body


async def test_httpexception_handler_json():
    """Test httpexception_handler returns JSON for API requests."""
    from starlette.requests import Request

    env = Environment(loader=DictLoader({}), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [(b"accept", b"application/json")],
    }
    request = Request(scope)

    exc = HTTPException(status_code=404, detail="Not found")
    response = await httpexception_handler(request, exc, env)

    assert response.status_code == 404
    import json
    data = json.loads(response.body)
    assert "errors" in data


async def test_httpexception_handler_html():
    """Test httpexception_handler returns HTML for browser requests."""
    from starlette.requests import Request

    templates = {
        "error.html": "<h1>{{ status_code }}</h1>",
    }
    env = Environment(loader=DictLoader(templates), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept", b"text/html")],
    }
    request = Request(scope)

    exc = HTTPException(status_code=404)
    response = await httpexception_handler(request, exc, env)

    assert response.status_code == 404
    assert b"404" in response.body


async def test_exception_handler_validation_error_json():
    """Test exception_handler handles ValidationError with JSON response."""
    from starlette.requests import Request

    class User(BaseModel):
        email: str
        age: int

    env = Environment(loader=DictLoader({}), enable_async=True)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/users",
        "headers": [(b"accept", b"application/json")],
    }
    request = Request(scope)

    try:
        User(email="invalid", age="not_int")
    except ValidationError as exc:
        response = await exception_handler(request, exc, env)

        assert response.status_code == 400
        import json
        data = json.loads(response.body)
        assert "errors" in data


async def test_exception_handler_app_exception_json():
    """Test exception_handler handles AppException with JSON response."""
    from starlette.requests import Request

    env = Environment(loader=DictLoader({}), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [(b"accept", b"application/json")],
    }
    request = Request(scope)

    exc = AppException("Test error", status_code=400, code=ErrorCode.INVALID_REQUEST)
    response = await exception_handler(request, exc, env)

    assert response.status_code == 400
    import json
    data = json.loads(response.body)
    assert "errors" in data


async def test_exception_handler_generic_exception_json():
    """Test exception_handler handles generic exceptions with JSON response."""
    from starlette.requests import Request

    env = Environment(loader=DictLoader({}), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [(b"accept", b"application/json")],
    }
    request = Request(scope)

    exc = ValueError("Something went wrong")
    response = await exception_handler(request, exc, env)

    assert response.status_code == 500
    import json
    data = json.loads(response.body)
    assert "errors" in data


async def test_exception_handler_generic_exception_html():
    """Test exception_handler handles generic exceptions with HTML response."""
    from starlette.requests import Request

    templates = {
        "error.html": "<h1>{{ status_code }}</h1><p>{{ error_message }}</p>",
    }
    env = Environment(loader=DictLoader(templates), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept", b"text/html")],
        "query_string": b"",
    }
    request = Request(scope)

    exc = ValueError("Something went wrong")
    response = await exception_handler(request, exc, env, debug=True)

    assert response.status_code == 500
    body = response.body.decode()
    assert "500" in body


async def test_exception_handler_debug_mode():
    """Test exception_handler includes debug info when debug=True."""
    from starlette.requests import Request

    templates = {
        "error.html": "<div>{{ traceback_text }}</div>",
    }
    env = Environment(loader=DictLoader(templates), enable_async=True)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept", b"text/html")],
        "query_string": b"",
    }
    request = Request(scope)

    exc = ValueError("Debug error")
    response = await exception_handler(request, exc, env, debug=True)

    assert response.status_code == 500
    body = response.body.decode()
    # Should include traceback in debug mode
    assert "Traceback" in body or "ValueError" in body


def test_jsonapi_error_model():
    """Test JSONAPIError model."""
    error = JSONAPIError(
        status="400",
        code="invalid_parameter",
        title="Invalid Parameter",
        detail="Email is required",
    )

    assert error.status == "400"
    assert error.code == "invalid_parameter"
    assert error.title == "Invalid Parameter"
    assert error.detail == "Email is required"


def test_jsonapi_error_response_model():
    """Test JSONAPIErrorResponse model."""
    error1 = JSONAPIError(status="400", title="Error 1", detail="Detail 1")
    error2 = JSONAPIError(status="400", title="Error 2", detail="Detail 2")

    response = JSONAPIErrorResponse(errors=[error1, error2])

    assert len(response.errors) == 2
    assert response.errors[0].title == "Error 1"
    assert response.errors[1].title == "Error 2"
