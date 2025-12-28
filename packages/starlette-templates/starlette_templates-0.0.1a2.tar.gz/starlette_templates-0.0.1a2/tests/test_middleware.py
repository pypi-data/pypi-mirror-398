"""Tests for starlette_templates.middleware module.

This test module demonstrates middleware features including:
- JinjaMiddleware: Injects Jinja2 environment into request.state
- Template loader configuration (FileSystemLoader, PackageLoader, etc.)
- Multiple template loaders with fallback (ChoiceLoader)
- Custom state keys for the jinja environment
- Global function and filter registration
- Async template rendering support
- HTML autoescape for security
"""
import pytest
from jinja2 import FileSystemLoader, PackageLoader
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette_templates.middleware import JinjaMiddleware


def test_jinjamiddleware_injects_jinja_env():
    """Test that JinjaMiddleware injects jinja_env into request.state."""
    async def check_jinja_env(request):
        assert hasattr(request.state, "jinja_env")
        assert request.state.jinja_env is not None
        return PlainTextResponse("OK")

    app = Starlette(
        routes=[Route("/", check_jinja_env)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[],
                include_default_loader=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_jinjaenvmiddleware_with_file_system_loader(templates_dir):
    """Test that JinjaMiddleware works with FileSystemLoader."""
    async def render_template(request):
        template = request.state.jinja_env.get_template("about.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", render_template)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[FileSystemLoader(str(templates_dir))],
                include_default_loader=False,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert b"About Page" in response.content


def test_jinjaenvmiddleware_with_package_loader():
    """Test that JinjaMiddleware works with PackageLoader."""
    async def check_loader(request):
        # Default loader should include starlette_templates package
        loader = request.state.jinja_env.loader
        assert loader is not None
        return PlainTextResponse("OK")

    app = Starlette(
        routes=[Route("/", check_loader)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[],
                include_default_loader=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_jinjaenvmiddleware_multiple_loaders(templates_dir):
    """Test that JinjaMiddleware supports multiple template loaders."""
    async def check_loaders(request):
        # Should have ChoiceLoader with multiple loaders
        loader = request.state.jinja_env.loader
        assert loader is not None
        # ChoiceLoader has loaders attribute
        assert hasattr(loader, "loaders")
        return PlainTextResponse("OK")

    app = Starlette(
        routes=[Route("/", check_loaders)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[FileSystemLoader(str(templates_dir))],
                include_default_loader=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_jinjaenvmiddleware_registers_globals():
    """Test that JinjaMiddleware registers global functions."""
    async def check_globals(request):
        env = request.state.jinja_env
        # Check that url_for, url, absurl, jsonify are registered
        assert "url_for" in env.globals
        assert "url" in env.globals
        assert "absurl" in env.globals
        assert "jsonify" in env.globals
        return PlainTextResponse("OK")

    app = Starlette(
        routes=[Route("/", check_globals)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[],
                include_default_loader=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_jinjaenvmiddleware_enables_async():
    """Test that JinjaMiddleware enables async template rendering."""
    async def check_async(request):
        env = request.state.jinja_env
        # Check that environment is configured for async
        assert env.is_async is True
        return PlainTextResponse("OK")

    app = Starlette(
        routes=[Route("/", check_async)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[],
                include_default_loader=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_jinjaenvmiddleware_autoescape():
    """Test that JinjaMiddleware enables autoescape for HTML."""
    from jinja2 import DictLoader

    templates = {
        "test.html": "<div>{{ content }}</div>",
    }

    async def render_with_autoescape(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({"content": "<script>alert('xss')</script>"})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", render_with_autoescape)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[DictLoader(templates)],
                include_default_loader=False,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    # Script should be escaped
    assert b"&lt;script&gt;" in response.content
    assert b"<script>" not in response.content


def test_jinjaenvmiddleware_exclude_websocket():
    """Test that JinjaMiddleware can exclude WebSocket connections."""
    # This is harder to test without WebSocket support, but we can at least
    # verify the middleware accepts the parameter
    app = Starlette(
        middleware=[
            Middleware(
                JinjaMiddleware,
                include_websocket=False,
                template_loaders=[],
                include_default_loader=True,
            )
        ],
    )
    assert app is not None


def test_jinjaenvmiddleware_without_default_loader():
    """Test that JinjaMiddleware can work without default loader."""
    from jinja2 import DictLoader

    templates = {"test.html": "<div>Test</div>"}

    async def render_template(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", render_template)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[DictLoader(templates)],
                include_default_loader=False,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Test" in response.content


def test_jinjaenvmiddleware_loader_order(templates_dir):
    """Test that JinjaMiddleware respects loader order."""
    from jinja2 import DictLoader

    # Override template in DictLoader
    templates = {"about.html": "<div>Overridden</div>"}

    async def render_template(request):
        template = request.state.jinja_env.get_template("about.html")
        html = await template.render_async({})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", render_template)],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[
                    DictLoader(templates),  # First loader takes priority
                    FileSystemLoader(str(templates_dir)),
                ],
                include_default_loader=False,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    # Should use DictLoader version (first in list)
    assert b"Overridden" in response.content
    assert b"About Page" not in response.content
