"""Tests for starlette_templates.context module.

This test module demonstrates how to use Jinja2 context helpers including:
- jsonify: Convert Python objects to JSON for templates
- url_for: Generate URLs for named routes
- url: Generate URLs for mounted applications
- absurl: Build absolute URLs from paths
- register_jinja_globals_filters: Register custom globals and filters
"""
import pytest
import json
from datetime import datetime, date
from decimal import Decimal
from jinja2 import Environment, DictLoader
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.testclient import TestClient
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette_templates.middleware import JinjaMiddleware
from starlette_templates.context import (
    jsonify,
    url_for,
    url,
    absurl,
    markdown_file,
    register_jinja_globals_filters,
)


def test_jsonify_basic_types():
    """Test that jsonify handles basic Python types."""
    data = {"name": "John", "age": 30, "active": True}
    result = jsonify(data)

    # Should return Markup-safe JSON string
    assert isinstance(result, str)
    parsed = json.loads(str(result))
    assert parsed["name"] == "John"
    assert parsed["age"] == 30
    assert parsed["active"] is True


def test_jsonify_datetime():
    """Test that jsonify handles datetime objects."""
    data = {"timestamp": datetime(2024, 1, 1, 12, 0, 0)}
    result = jsonify(data)

    parsed = json.loads(str(result))
    assert "timestamp" in parsed
    # Datetime should be serialized to ISO format
    assert "2024-01-01" in parsed["timestamp"]


def test_jsonify_date():
    """Test that jsonify handles date objects."""
    data = {"birth_date": date(2024, 1, 1)}
    result = jsonify(data)

    parsed = json.loads(str(result))
    assert "birth_date" in parsed


def test_jsonify_decimal():
    """Test that jsonify handles Decimal objects."""
    data = {"price": Decimal("19.99")}
    result = jsonify(data)

    # jsonify uses pydantic's to_jsonable_python which converts Decimal to string
    parsed = json.loads(str(result))
    # Decimal might be serialized as string or float depending on pydantic version
    price_value = parsed["price"]
    if isinstance(price_value, str):
        assert price_value == "19.99"
    else:
        assert abs(price_value - 19.99) < 0.01


def test_jsonify_nested():
    """Test that jsonify handles nested structures."""
    data = {
        "user": {
            "name": "John",
            "contacts": ["email@example.com", "phone"],
            "metadata": {"verified": True},
        }
    }
    result = jsonify(data)

    parsed = json.loads(str(result))
    assert parsed["user"]["name"] == "John"
    assert len(parsed["user"]["contacts"]) == 2
    assert parsed["user"]["metadata"]["verified"] is True


def test_jsonify_with_indent():
    """Test that jsonify supports indentation."""
    data = {"name": "John"}
    result = jsonify(data, indent=2)

    assert "\n" in str(result)  # Should have newlines with indentation


def test_jsonify_markup_safe():
    """Test that jsonify returns Markup-safe strings."""
    from markupsafe import Markup

    data = {"name": "John"}
    result = jsonify(data)

    assert isinstance(result, Markup)


def test_url_for_in_template():
    """Test that url_for works in Jinja2 templates."""
    templates = {
        "test.html": '<a href="{{ url_for(\'user\', user_id=123) }}">User</a>',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    async def user(request):
        return PlainTextResponse("User Page")

    app = Starlette(
        routes=[
            Route("/", home, name="home"),
            Route("/users/{user_id}", user, name="user"),
        ],
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
    assert b"/users/123" in response.content


def test_url_in_template():
    """Test that url() works in Jinja2 templates for mounts.

    The url() function generates URLs for mounted applications. It's useful
    for generating links to static files or other mounted sub-applications.
    """
    templates = {
        "test.html": '<link rel="stylesheet" href="{{ url(\'static\', \'/css/style.css\') }}">',
    }

    async def home(request):
        # Get template from jinja_env that was injected by JinjaMiddleware
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    from starlette_templates.staticfiles import StaticFiles

    app = Starlette(
        routes=[
            Route("/", home, name="home"),
            Mount("/static", StaticFiles(check_dir=False), name="static"),
        ],
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
    assert b"/static/css/style.css" in response.content


def test_absurl_in_template():
    """Test that absurl() works in Jinja2 templates."""
    templates = {
        "test.html": '<a href="{{ absurl(\'/path/to/page\') }}">Link</a>',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
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
    # Should include scheme and host
    assert b"http://testserver/path/to/page" in response.content


def test_jsonify_as_filter():
    """Test that jsonify works as a Jinja2 filter."""
    templates = {
        "test.html": '<script>var data = {{ data|jsonify }};</script>',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({
            "request": request,
            "data": {"name": "John", "age": 30},
        })
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
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
    assert b'"name":"John"' in response.content
    assert b'"age":30' in response.content


def test_jsonify_as_function():
    """Test that jsonify works as a Jinja2 function."""
    templates = {
        "test.html": '<script>var data = {{ jsonify(data) }};</script>',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({
            "request": request,
            "data": {"name": "John", "age": 30},
        })
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
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
    assert b'"name":"John"' in response.content


def test_register_jinja_globals_filters():
    """Test that register_jinja_globals_filters registers all functions."""
    env = Environment(loader=DictLoader({}))
    register_jinja_globals_filters(env)

    # Check globals
    assert "url_for" in env.globals
    assert "url" in env.globals
    assert "absurl" in env.globals
    assert "jsonify" in env.globals

    # Check filters
    assert "jsonify" in env.filters


def test_register_jinja_globals_filters_uses_setdefault():
    """Test that register_jinja_globals_filters doesn't override existing."""
    env = Environment(loader=DictLoader({}))

    # Set custom url_for
    def custom_url_for(*args, **kwargs):
        return "/custom"

    env.globals["url_for"] = custom_url_for

    register_jinja_globals_filters(env)

    # Should keep custom implementation
    assert env.globals["url_for"] == custom_url_for


def test_url_for_requires_request_in_context():
    """Test that url_for requires request in context."""
    env = Environment(loader=DictLoader({}))
    register_jinja_globals_filters(env)

    # Try to call url_for without request in context
    with pytest.raises(KeyError):
        url_for({}, "route_name")


def test_absurl_handles_leading_slash():
    """Test that absurl handles paths with and without leading slash."""
    templates = {
        "test.html": '{{ absurl("path/to/page") }} {{ absurl("/path/to/page") }}',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
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
    # Both should produce the same absolute URL
    content = response.content.decode()
    assert content.count("http://testserver/path/to/page") == 2


def test_jsonify_pydantic_model():
    """Test that jsonify handles Pydantic models."""
    from pydantic import BaseModel

    class User(BaseModel):
        name: str
        age: int

    user = User(name="John", age=30)
    result = jsonify(user)

    parsed = json.loads(str(result))
    assert parsed["name"] == "John"
    assert parsed["age"] == 30


def test_jsonify_list():
    """Test that jsonify handles lists."""
    data = [1, 2, 3, "four", True]
    result = jsonify(data)

    parsed = json.loads(str(result))
    assert parsed == [1, 2, 3, "four", True]


def test_url_for_with_multiple_params():
    """Test that url_for handles multiple path parameters."""
    templates = {
        "test.html": '{{ url_for("article", category="tech", slug="hello-world") }}',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("test.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    async def article(request):
        return PlainTextResponse("Article")

    app = Starlette(
        routes=[
            Route("/", home, name="home"),
            Route("/{category}/{slug}", article, name="article"),
        ],
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
    assert b"/tech/hello-world" in response.content


def test_markdown_file_basic():
    """Test that markdown_file renders basic markdown to HTML."""
    markdown_content = """# Hello World

This is a **bold** statement and this is *italic*.

- Item 1
- Item 2
- Item 3
"""

    templates = {
        "content.md": markdown_content,
        "page.html": '<div class="content">{{ markdown("content.md") }}</div>',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("page.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[DictLoader(templates)],
                include_default_loader=False,
                include_markdown_processor=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    # Check that markdown was converted to HTML
    # Note: TOC extension adds id attributes to headers
    assert b"Hello World</h1>" in response.content
    assert b"<strong>bold</strong>" in response.content
    assert b"<em>italic</em>" in response.content
    assert b"<li>Item 1</li>" in response.content


def test_markdown_file_with_jinja_variables():
    """Test that markdown_file processes Jinja2 variables within markdown."""
    markdown_content = """# Welcome {{ user_name }}!

You have **{{ count }}** new messages.

Visit your profile at {{ url_for('profile', user_id=user_id) }}.
"""

    templates = {
        "message.md": markdown_content,
        "page.html": '{{ markdown("message.md") }}',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("page.html")
        html = await template.render_async({
            "request": request,
            "user_name": "John Doe",
            "count": 5,
            "user_id": 123,
        })
        return PlainTextResponse(html)

    async def profile(request):
        return PlainTextResponse("Profile")

    app = Starlette(
        routes=[
            Route("/", home, name="home"),
            Route("/profile/{user_id}", profile, name="profile"),
        ],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[DictLoader(templates)],
                include_default_loader=False,
                include_markdown_processor=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    # Check that Jinja2 variables were processed
    assert b"Welcome John Doe!" in response.content
    assert b"<strong>5</strong>" in response.content
    # Check that url_for worked in markdown
    assert b"/profile/123" in response.content


def test_markdown_file_with_pymdown_extensions():
    """Test that markdown_file uses pymdown extensions correctly."""
    markdown_content = """# PyMdown Extensions Test

## Task Lists
- [x] Completed task
- [ ] Incomplete task

## Code Highlighting
```python
def hello_world():
    print("Hello, World!")
```

## Admonition
!!! warning "Important Note"
    This is a warning admonition block.

## Superscript and Subscript
H~2~O and E=mc^2^

## Highlighting
==This text is highlighted==

## Smart Symbols
(c) (tm) (r)
"""

    templates = {
        "content.md": markdown_content,
        "page.html": '{{ markdown("content.md") }}',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("page.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[DictLoader(templates)],
                include_default_loader=False,
                include_markdown_processor=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()

    # Check task lists
    assert 'type="checkbox"' in content
    assert 'checked' in content

    # Check code blocks (highlight wraps in span tags)
    assert "hello_world" in content
    assert "print" in content

    # Check subscript and superscript (tilde extension)
    assert "<sub>2</sub>" in content
    assert "<sup>2</sup>" in content

    # Check highlighting (mark extension)
    assert "<mark>This text is highlighted</mark>" in content


def test_markdown_file_markup_safe():
    """Test that markdown_file returns Markup-safe HTML."""
    from markupsafe import Markup

    markdown_content = "# Test\n\nThis is **bold**."

    templates = {
        "content.md": markdown_content,
        "page.html": '{{ markdown("content.md") }}',
    }

    async def home(request):
        template = request.state.jinja_env.get_template("page.html")
        html = await template.render_async({"request": request})
        return PlainTextResponse(html)

    app = Starlette(
        routes=[Route("/", home, name="home")],
        middleware=[
            Middleware(
                JinjaMiddleware,
                template_loaders=[DictLoader(templates)],
                include_default_loader=False,
                include_markdown_processor=True,
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    # HTML tags should not be escaped (proves it's Markup-safe)
    # Note: TOC extension adds id attributes to headers
    assert b"<h1" in response.content and b">Test</h1>" in response.content
    assert b"&lt;h1&gt;" not in response.content


def test_markdown_file_in_register_globals():
    """Test that markdown is registered as a Jinja2 global."""
    env = Environment(loader=DictLoader({}))
    register_jinja_globals_filters(env)

    # Check that markdown is registered
    assert "markdown" in env.globals
