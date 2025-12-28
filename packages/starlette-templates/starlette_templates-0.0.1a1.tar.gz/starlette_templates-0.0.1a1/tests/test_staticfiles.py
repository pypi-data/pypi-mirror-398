"""Tests for starlette_templates.staticfiles module.

This test module demonstrates static file serving features including:
- StaticFiles: Enhanced static file serving with gzip and caching
- Gzip compression for .gz files with proper Content-Encoding headers
- HTTP caching with ETag, Cache-Control, and Last-Modified headers
- 304 Not Modified responses for cached requests
"""
import gzip
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient
from starlette_templates.staticfiles import StaticFiles


def test_staticfiles_serves_regular_files(static_dir):
    """Test that StaticFiles serves regular static files.

    StaticFiles should serve CSS, JS, and other static assets with
    appropriate MIME types and caching headers.
    """
    app = Starlette(
        routes=[
            Mount("/static", StaticFiles(directories=[static_dir]), name="static"),
        ]
    )
    client = TestClient(app)

    # Request CSS file
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
    assert b"color: red" in response.content


def test_staticfiles_serves_gz_with_encoding(static_dir):
    """Test that StaticFiles serves .gz files with correct Content-Encoding header.

    When a .gz file is requested directly, StaticFiles should:
    1. Set Content-Encoding: gzip
    2. Determine correct MIME type from the base filename (before .gz)
    3. Set Vary: accept-encoding for caching proxies
    """
    app = Starlette(
        routes=[
            Mount("/static", StaticFiles(directories=[static_dir]), name="static"),
        ]
    )
    client = TestClient(app)

    response = client.get("/static/compressed.css.gz")
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    # Should detect CSS MIME type from .css extension
    assert "text/css" in response.headers.get("content-type", "")
    assert response.headers.get("vary") == "accept-encoding"


def test_staticfiles_adds_cache_headers(static_dir):
    """Test that StaticFiles adds strong caching headers.

    Static files should have aggressive caching headers:
    - Cache-Control: public, max-age=31536000, immutable
    - ETag for cache validation
    """
    app = Starlette(
        routes=[
            Mount("/static", StaticFiles(directories=[static_dir]), name="static"),
        ]
    )
    client = TestClient(app)

    response = client.get("/static/style.css")
    assert response.status_code == 200

    # Check cache headers
    assert "cache-control" in response.headers
    cache_control = response.headers["cache-control"]
    assert "public" in cache_control
    assert "max-age" in cache_control

    # Should have ETag for validation
    assert "etag" in response.headers


def test_staticfiles_returns_304_not_modified(static_dir):
    """Test that StaticFiles returns 304 for cached requests.

    When a client sends If-None-Match with a matching ETag,
    the server should return 304 Not Modified to save bandwidth.
    """
    app = Starlette(
        routes=[
            Mount("/static", StaticFiles(directories=[static_dir]), name="static"),
        ]
    )
    client = TestClient(app)

    # First request to get ETag
    response1 = client.get("/static/style.css")
    assert response1.status_code == 200
    etag = response1.headers.get("etag")
    assert etag is not None

    # Second request with If-None-Match should return 304
    response2 = client.get("/static/style.css", headers={"if-none-match": etag})
    assert response2.status_code == 304


def test_staticfiles_serves_js_files(static_dir):
    """Test that StaticFiles serves JavaScript files with correct MIME type."""
    app = Starlette(
        routes=[
            Mount("/static", StaticFiles(directories=[static_dir]), name="static"),
        ]
    )
    client = TestClient(app)

    response = client.get("/static/script.js")
    assert response.status_code == 200
    # JavaScript MIME type
    assert "javascript" in response.headers.get("content-type", "").lower() or \
           "application/javascript" in response.headers.get("content-type", "") or \
           "text/javascript" in response.headers.get("content-type", "")


def test_staticfiles_returns_404_for_missing(static_dir):
    """Test that StaticFiles returns 404 for non-existent files."""
    app = Starlette(
        routes=[
            Mount("/static", StaticFiles(directories=[static_dir]), name="static"),
        ]
    )
    client = TestClient(app)

    response = client.get("/static/nonexistent.css")
    assert response.status_code == 404
