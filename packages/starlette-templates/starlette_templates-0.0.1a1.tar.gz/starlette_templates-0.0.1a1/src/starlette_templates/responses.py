import gzip
import xxhash
import typing as t
from functools import lru_cache
from email.utils import formatdate
from starlette.requests import Request
from starlette.datastructures import Headers
from starlette.responses import Response, HTMLResponse


# LRU cache for compressed content to avoid re-compressing the same data
@lru_cache(maxsize=256)
def compress_cached(content_hash: str, content: bytes, level: int) -> bytes:
    """Cache compressed content by hash to avoid redundant compression."""
    return gzip.compress(content, compresslevel=level)


class GzipResponse(Response):
    """Response class that supports gzip compression with caching."""

    def __init__(
        self,
        content: bytes,
        status_code: int = 200,
        headers: t.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: t.Any = None,
        compress: bool = True,
        min_size: int = 500,
        compresslevel: int = 6,
    ) -> None:
        self.original_content = content
        self.compress = compress and len(content) >= min_size

        if self.compress:
            # Use cached compression based on content hash
            content_hash = xxhash.xxh64(content).hexdigest()
            compressed = compress_cached(content_hash, content, compresslevel)
            if len(compressed) < len(content):
                content = compressed
            else:
                self.compress = False

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

        if self.compress:
            self.headers["content-encoding"] = "gzip"
            self.headers["vary"] = "accept-encoding"


class ContentResponse(GzipResponse):
    """Response for serving HTML content with caching headers.

    Adds ETag and Last-Modified headers for caching. ETag is computed on the
    final content (after compression if applicable) using xxhash for speed.

    Args:
        content: The response content as bytes
        status_code: The HTTP status code for the response
        headers: Additional headers for the response
        media_type: The media type for the response
        mtime: Optional last modified time (as a timestamp)
        max_age: Max age for caching in seconds (default: 3600)
    """

    def __init__(
        self,
        content: bytes,
        status_code: int = 200,
        headers: t.Mapping[str, str] | None = None,
        media_type: str = "text/html",
        mtime: float | None = None,
        max_age: int = 3600,  # seconds
        **kwargs: t.Any,
    ) -> None:
        # First, call parent to handle compression
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            **kwargs,
        )

        # Generate ETag from the final content (after compression)
        # Use xxhash for faster hashing than MD5
        etag = xxhash.xxh64(self.body).hexdigest()

        # Add caching headers
        self.headers["etag"] = f'"{etag}"'
        self.headers["cache-control"] = f"public, max-age={max_age}"

        if mtime is not None:
            self.headers["last-modified"] = formatdate(mtime, usegmt=True)


class NotModifiedResponse(Response):
    """304 Not Modified response."""

    def __init__(self, headers: Headers) -> None:
        super().__init__(status_code=304, headers=dict(headers))


class TemplateResponse(HTMLResponse):
    """HTMLResponse subclass that renders Jinja2 templates.

    This class provides a convenient way to render Jinja2 templates from
    route handlers without manually accessing the Jinja2 environment.

    The template will have access to standard context variables:

    - request: The Starlette Request object
    - url_for: Function to generate URLs for named routes
    - absurl: Function to generate absolute URLs
    - base_url: The base URL of the application
    - url: Function to build full URLs from paths
    - jsonify: Function to serialize data to JSON for embedding in HTML
    - Plus any custom context variables provided

    Args:
        template_name: The name of the Jinja2 template to render
        request: The Starlette Request object (required for accessing app's Jinja2 env)
        context: The context data to pass to the template
        status_code: The HTTP status code for the response
        headers: Additional headers for the response
        media_type: The media type for the response
        background: A background task to run after the response is sent

    Example:
        ```python
        from starlette_templates import Application, TemplateResponse, route, model_from_request
        from starlette.requests import Request
        from pydantic import BaseModel

        class UserModel(BaseModel):
            id: int
            name: str

        @route("/users/{user_id}")
        async def user_profile(request: Request) -> TemplateResponse:
            user  = model_from_request(request, UserModel)

            return TemplateResponse(
                "user_profile.html",
                context={"user": user},
            )

        app = Application(
            routes=[user_profile],
            package_name="myapp",
        )
        ```
    """

    def __init__(
        self,
        template_name: str,
        context: dict[str, t.Any] | None = None,
        status_code: int = 200,
        headers: t.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: t.Any = None,
    ):
        self.template_name = template_name
        self.context = context or {}

        super().__init__(
            content="",
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    async def __call__(
        self,
        scope: t.Dict[str, t.Any],
        receive: t.Callable[[], t.Awaitable[t.Dict[str, t.Any]]],
        send: t.Callable[[t.Dict[str, t.Any]], t.Awaitable[None]],
    ) -> None:
        """Render template when response is called as ASGI app.

        Flow:
            1. Create Request object from ASGI scope
            2. Build context with request + user-provided context
            3. Get jinja_env from request.state (set by JinjaMiddleware)
            4. Load and render template asynchronously
            5. Send rendered HTML as response

        Note:
            Context must include "request" for @pass_context functions (url_for, absurl)
            to work properly. These functions extract request from context["request"].
        """
        # Create Request object to access request.state.jinja_env
        request = Request(scope, receive, send)

        # Build context - MUST include request for @pass_context functions to work
        # @pass_context functions like url_for and absurl need context["request"]
        context = {"request": request, **self.context}

        # Get Jinja2 environment from request state (set by JinjaMiddleware)
        jinja_env = request.state.jinja_env
        # Load template by name - loaders will find it (PackageLoader, FileSystemLoader, etc.)
        template = jinja_env.get_template(self.template_name)

        # Render template asynchronously with context
        html_content = await template.render_async(context)

        # Set body and initialize headers for HTMLResponse
        self.body = self.render(html_content)
        self.init_headers()

        # Call parent HTMLResponse to send the response
        await super().__call__(scope, receive, send)
