import os
import stat
import errno
import logging
import aiofiles
import typing as t
from pathlib import Path
from jinja2 import Environment
from email.utils import parsedate
from starlette.types import Scope
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Send
from starlette.routing import Route, Match
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.datastructures import Headers, URL
from starlette_templates.errors import exception_handler
from starlette_templates.responses import NotModifiedResponse, ContentResponse

PathLike = t.Union[str, "os.PathLike[str]", Path]

logger = logging.getLogger("starlette_templates.routing")


async def render_file(
    file_path: str,
    context: dict[str, t.Any],
    jinja_env: Environment,
    templates_dir: Path,
) -> str:
    """Render HTML file using Jinja2.

    HTML files use get_template() to support {% extends %} inheritance.
    Jinja2 automatically handles template inheritance if present.

    Args:
        file_path: Absolute path to the HTML file
        context: Template context dictionary
        jinja_env: Jinja2 environment for template rendering
        templates_dir: Path to templates directory

    Returns:
        Rendered HTML content as string

    Example:
        >>> context = {"request": request}
        >>> html = await render_file(file_path, context, jinja_env, templates_dir)
    """
    # Get relative path for Jinja2 template loading
    rel_path = os.path.relpath(file_path, templates_dir)
    template = jinja_env.get_template(rel_path)
    content = await template.render_async(context)
    return content


class TemplateRouter:
    """
    ASGI app for routing HTTP requests to Jinja2 templates with automatic resolution.

    Routes incoming requests to templates with Jinja2 rendering, HTTP caching, gzip
    compression, and automatic file resolution (extension fallbacks, index files).

    Architecture with two modes of operation: The system supports two distinct operational modes.
    When initialized with a directory parameter, it uses filesystem lookups to find templates
    through direct file access with stat and permissions checking, which is useful when templates
    are in a known directory. Alternatively, when initialized without a directory parameter
    (directory=None), it uses jinja_env loaders such as PackageLoader or FileSystemLoader,
    allowing templates to be served from locations defined in JinjaMiddleware, providing a
    single source of truth for template locations without configuration duplication.

    Flow:
        1. JinjaMiddleware defines template loaders
        2. Mount TemplateRouter() without directory parameter
        3. Request comes in: /forms
        4. TemplateRouter.get_response() called
        5. Delegates to render_template_from_loaders()
        6. Gets jinja_env from request.state
        7. Tries candidates: forms.html, forms.htm, etc.
        8. Finds template using jinja_env.loader.get_source()
        9. Renders template with context {"request": request}
        10. Returns ContentResponse with caching headers

    Context processors are callables that accept a Request and return a dict
    of additional context variables to be merged into the template context.

    Args:
        directory: Optional path to templates directory (None = use jinja_env loaders)
        extensions: List of allowed file extensions (default: [".html", ".htm", ".jinja", ".jinja2"])
        index_files: List of index filenames to search for (default: ["index.html", "index.htm"])
        check_dir: Whether to check if directory exists on init
        follow_symlink: Whether to follow symlinks in directory
        cache_max_age: Max age for HTTP caching (in seconds)
        gzip_min_size: Minimum size (in bytes) to apply gzip compression
        context_processors: List of async callables to add to template context
        jinja_env: Optional Jinja2 Environment (falls back to request.state.jinja_env)
        debug: Whether to enable debug mode (shows detailed error pages)
        error_handler: Callable to handle exceptions and return custom responses (uses built-in handler if None)

    Example:
        ```python
        app = Starlette(
            routes=[
                # Override specific paths, like / which would map to index.html
                Route("/", homepage, name="home"),
                # Catch-all for templates
                Mount("/", TemplateRouter()),
            ],
            middleware=[
                Middleware(
                    JinjaMiddleware,
                    template_loaders=[PackageLoader("myapp", "templates")]
                )
            ]
        )
        ```
    """

    def __init__(
        self,
        *,
        directory: PathLike | None = None,
        extensions: list[str] | None = None,
        index_files: list[str] | None = None,
        check_dir: bool = True,
        follow_symlink: bool = False,
        cache_max_age: int = 3600,
        gzip_min_size: int = 500,
        context_processors: list[t.Callable[[Request], t.Awaitable[dict[str, t.Any]]] | Route] | None = None,
        jinja_env: Environment | None = None,
        debug: bool = False,
        error_handler: t.Callable[[Request, Exception], t.Awaitable[Response]] | None = None,
    ) -> None:
        self.directory = Path(directory) if directory else None
        self.extensions = extensions or [".html", ".htm", ".jinja", ".jinja2"]
        self.index_files = index_files or ["index.html", "index.htm"]
        self.follow_symlink = follow_symlink
        self.cache_max_age = cache_max_age
        self.gzip_min_size = gzip_min_size
        self.context_processors = context_processors or []
        self.config_checked = False
        self.jinja_env = jinja_env
        self.debug = debug

        # If no error_handler provided, use the built-in error handler
        if error_handler is None:
            self.error_handler = self._create_default_error_handler()
        else:
            self.error_handler = error_handler

        if check_dir and directory is not None and not os.path.isdir(directory):
            raise RuntimeError(f"Directory '{directory}' does not exist")

    def _create_default_error_handler(self) -> t.Callable[[Request, Exception], t.Awaitable[Response]]:
        """Create the default error handler that uses the built-in error page.

        Returns:
            An async callable that handles exceptions using the error page from errors.py
        """

        async def default_handler(request: Request, exc: Exception) -> Response:
            """Default error handler using the built-in error page."""
            # Get jinja_env from request state (set by JinjaMiddleware)
            # Fall back to self.jinja_env if provided during initialization
            jinja_env = getattr(request.state, "jinja_env", None) or self.jinja_env

            if not jinja_env:
                # If no jinja_env available, re-raise the exception
                # This shouldn't happen in normal usage
                raise exc

            # Use the exception_handler from errors.py with debug mode
            return await exception_handler(
                request=request,
                exc=exc,
                jinja_env=jinja_env,
                debug=self.debug,
            )

        return default_handler

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entry point."""
        assert scope["type"] == "http"

        if not self.config_checked:
            await self.check_config()
            self.config_checked = True

        path = self.get_path(scope)
        request = Request(scope, receive, send)

        try:
            response = await self.get_response(path, scope, receive, send, request)
        except HTTPException:
            raise
        except Exception as exc:
            # Log the exception before handling
            logger.error(
                f"Exception in TemplateRouter: {type(exc).__name__}: {exc}",
                exc_info=exc,
                extra={
                    "path": path,
                    "request_method": request.method if hasattr(request, "method") else None,
                    "request_url": str(request.url) if hasattr(request, "url") else None,
                }
            )
            # Use error_handler (always available - either custom or default)
            response = await self.error_handler(request, exc)

        await response(scope, receive, send)

    def get_path(self, scope: Scope) -> str:
        """Extract and normalize the path from the ASGI scope.

        Handles both standalone and mounted cases by respecting root_path.
        """
        # Get the route path, handling root_path for mounted apps
        path = scope["path"]
        root_path = scope.get("root_path", "")

        if root_path:
            # Remove root_path prefix if present (for mounted apps)
            if path.startswith(root_path):
                if path == root_path:
                    route_path = ""
                elif len(path) > len(root_path) and path[len(root_path)] == "/":
                    route_path = path[len(root_path) :]
                else:
                    route_path = path
            else:
                route_path = path
        else:
            route_path = path

        # Strip leading slash and normalize
        if route_path.startswith("/"):
            route_path = route_path[1:]
        return os.path.normpath(os.path.join(*route_path.split("/"))) if route_path else ""

    async def _apply_context_processors(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        base_context: dict[str, t.Any],
    ) -> None:
        """Apply context processors (both global and route-specific).

        Context processors can be either:
        - Regular async callables: Run for all templates
        - Route instances: Only run when route pattern matches current request

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
            request: Starlette Request object
            base_context: Dictionary to update with processor results
        """
        for processor in self.context_processors:
            # Check if processor is a Route instance (route-specific processor)
            if isinstance(processor, Route):
                # Use Route's matches() method to check if it matches current request
                match, matched_scope = processor.matches(scope)

                if match == Match.FULL:
                    # Route matched! Merge matched_scope (contains path_params) with original scope
                    # matched_scope only contains path_params, need to merge with original scope
                    full_scope = {**scope, **matched_scope}
                    # Create new request with full scope including path_params
                    matched_request = Request(full_scope, receive, send)
                    # Call the route's endpoint with matched request
                    processor_context = await processor.endpoint(matched_request)
                    if processor_context:
                        base_context.update(processor_context)
            else:
                # Regular callable processor - runs for all templates
                processor_context = await processor(request)
                if processor_context:
                    base_context.update(processor_context)

    async def get_response(self, path: str, scope: Scope, receive: Receive, send: Send, request: Request) -> Response:
        """Returns an HTTP response for the given path.

        Supports all HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.) to allow
        template files to handle form submissions and other HTTP operations.

        Two modes of operation:
            1. With directory: Uses filesystem lookups to find templates
               - Checks file existence, permissions, symlinks
               - Returns 401 for permission errors, 404 for missing files
               - Handles directory index files and redirects

            2. Without directory (directory=None): Uses jinja_env loaders
               - Delegates to render_template_from_loaders()
               - Templates found via PackageLoader, FileSystemLoader, etc.
               - No filesystem checks - relies on loader.get_source()
        """

        # If directory is None, use jinja_env loaders to find template
        # This allows templates to be served from locations defined in JinjaMiddleware
        if self.directory is None:
            return await self.render_template_from_loaders(path, scope, receive, send, request)

        try:
            result = self.lookup_path(path)
        except PermissionError:
            raise HTTPException(status_code=401)
        except OSError as exc:
            if exc.errno == errno.ENAMETOOLONG:
                raise HTTPException(status_code=404)
            raise exc

        if result is not None:
            full_path, stat_result, needs_redirect = result

            if needs_redirect:
                url = URL(scope=scope)
                url = url.replace(path=url.path + "/")
                return RedirectResponse(url=url)

            return await self.render_response(full_path, stat_result, scope, receive, send, request)

        return await self.get_404_response(scope, receive, send, request)

    def lookup_path(self, path: str) -> tuple[str, os.stat_result, bool] | None:
        """Look up a file path with fallback resolution.

        If directory is None, returns None and template lookup will be handled
        by jinja_env loaders in render_response.
        """
        if self.directory is None:
            return None

        directory = self.resolve_directory(self.directory)

        if not path or path == ".":
            return self.lookup_index(directory, "")

        _, ext = os.path.splitext(path)
        if ext.lower() in self.extensions:
            result = self.try_path(directory, path)
            if result:
                return (*result, False)
            return None

        for ext in self.extensions:
            result = self.try_path(directory, path + ext)
            if result:
                return (*result, False)

        result = self.lookup_index(directory, path)
        if result:
            return result

        return None

    def lookup_index(self, directory: str, path: str) -> tuple[str, os.stat_result, bool] | None:
        """Look for index files in a directory."""
        dir_path = os.path.join(directory, path) if path else directory

        try:
            dir_stat = os.stat(dir_path)
            if not stat.S_ISDIR(dir_stat.st_mode):
                return None
        except (FileNotFoundError, NotADirectoryError):
            return None

        for index_file in self.index_files:
            result = self.try_path(directory, os.path.join(path, index_file))
            if result:
                return (*result, False)

        return None

    def try_path(self, directory: str, path: str) -> tuple[str, os.stat_result] | None:
        """Try to find and stat a specific path."""
        joined_path = os.path.join(directory, path)

        if self.follow_symlink:
            full_path = os.path.abspath(joined_path)
            resolved_dir = os.path.abspath(directory)
        else:
            full_path = os.path.realpath(joined_path)
            resolved_dir = os.path.realpath(directory)

        if os.path.commonpath([full_path, resolved_dir]) != resolved_dir:
            return None

        try:
            stat_result = os.stat(full_path)
            if stat.S_ISREG(stat_result.st_mode):
                return (full_path, stat_result)
        except (FileNotFoundError, NotADirectoryError):
            pass

        return None

    def resolve_directory(self, directory: Path) -> str:
        """Resolve directory path based on symlink settings."""
        if self.follow_symlink:
            return os.path.abspath(directory)
        return os.path.realpath(directory)

    async def render_template_from_loaders(
        self,
        path: str,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        status_code: int = 200,
    ) -> Response:
        """Render template using jinja_env loaders without requiring a directory.

        This method is used when TemplateRouter is initialized without a directory parameter.
        Instead of doing filesystem lookups, it relies on the jinja_env's configured loaders
        (PackageLoader, FileSystemLoader, etc.) to find templates.

        This allows templates to be served from locations defined in JinjaMiddleware,
        avoiding duplication of template location configuration.

        Flow:
            1. Get jinja_env from request.state (set by JinjaMiddleware)
            2. Build template context with request + context processors
            3. Generate list of template candidates (with extension fallbacks)
            4. Try each candidate using jinja_env loaders
            5. Render found template and return response with caching headers

        Args:
            path: URL path (e.g., "forms", "about", "")
            scope: ASGI scope
            request: Starlette Request object
            status_code: HTTP status code for response

        Returns:
            ContentResponse with rendered HTML and caching headers
        """
        # Get jinja_env from request state (set by JinjaMiddleware)
        # Falls back to self.jinja_env if set during __init__ (for backwards compatibility)
        jinja_env = getattr(request.state, "jinja_env", None) or self.jinja_env

        if not jinja_env:
            raise HTTPException(status_code=500, detail="No Jinja2 environment available")

        # Build base context - MUST include request for @pass_context functions
        base_context = {"request": request}

        # Apply context processors (both global and route-specific)
        await self._apply_context_processors(scope, receive, send, request, base_context)

        # Generate list of template candidates to try
        # Path "" or "." -> try index files
        if not path or path == ".":
            template_candidates = self.index_files  # ["index.html", "index.htm"]
        else:
            # Check if path already has an extension
            _, ext = os.path.splitext(path)
            if ext.lower() in self.extensions:
                # Path has extension (e.g., "forms.html") - use as-is
                template_candidates = [path]
            else:
                # Path has no extension (e.g., "forms") - try adding extensions
                # Tries: forms.html, forms.htm, forms.jinja, forms.jinja2
                template_candidates = [path + ext for ext in self.extensions]
                # Also try index files in case path is a directory
                # Tries: forms/index.html, forms/index.htm
                template_candidates.extend([os.path.join(path, idx) for idx in self.index_files])

        # Try each candidate template using jinja_env loaders
        template = None
        source_path = None
        template_errors = []

        for candidate in template_candidates:
            try:
                # Use loader.get_source to check if template exists
                # Returns (source, filename, uptodate_func)
                # We need the loader method, not environment method
                _, source_path, _ = jinja_env.loader.get_source(jinja_env, candidate)
                # Load the template for rendering
                template = jinja_env.get_template(candidate)
                break  # Found it! Stop searching
            except Exception as e:
                # Template not found with this candidate, try next one
                template_errors.append((candidate, str(e)))
                continue

        if not template:
            # None of the candidates were found - return 404
            raise HTTPException(status_code=404)

        # Render template asynchronously with context
        html_content = await template.render_async(base_context)
        content_bytes = html_content.encode("utf-8")

        # Try to get mtime from source file for HTTP caching headers
        # source_path comes from loader.get_source() - it's the actual file path
        mtime = None
        if source_path:
            try:
                stat_result = os.stat(source_path)
                mtime = stat_result.st_mtime  # Last modified time for Last-Modified header
            except (OSError, FileNotFoundError):
                # File might not have a filesystem path (e.g., from a custom loader)
                pass

        # Create response with gzip compression and caching headers
        response = ContentResponse(
            content=content_bytes,
            status_code=status_code,
            media_type="text/html; charset=utf-8",
            mtime=mtime,  # Used for Last-Modified header
            max_age=self.cache_max_age,  # Cache-Control max-age
            min_size=self.gzip_min_size,  # Minimum size to apply gzip
        )

        # Check for 304 Not Modified based on ETag or If-Modified-Since
        if mtime:
            request_headers = Headers(scope=scope)
            if self.is_not_modified(response.headers, request_headers):
                # Client has cached version - send 304 instead of full response
                return NotModifiedResponse(response.headers)

        return response

    def validate_file_extension(self, full_path: str) -> None:
        """Validate that the file has an allowed extension.

        Args:
            full_path: Absolute path to the file

        Raises:
            ValueError: If file extension is not in allowed extensions
        """
        _, ext = os.path.splitext(full_path)
        if ext.lower() not in self.extensions:
            allowed = ", ".join(self.extensions)
            raise ValueError(f"Unsupported file extension: {ext}. Allowed extensions: {allowed}")

    async def render_response(
        self,
        full_path: str,
        stat_result: os.stat_result,
        scope: Scope,
        receive: Receive,
        send: Send,
        request: Request,
        status_code: int = 200,
    ) -> Response:
        """Render a file as an HTTP response using simplified pipeline."""
        request_headers = Headers(scope=scope)

        # Validate file extension
        self.validate_file_extension(full_path)

        # Build base context - must include request for @pass_context functions
        base_context = {"request": request}

        # Apply context processors (both global and route-specific)
        await self._apply_context_processors(scope, receive, send, request, base_context)

        # Render file using Jinja2
        # Try to get jinja_env from request state (set by JinjaMiddleware)
        # Fall back to self.jinja_env if provided during initialization
        jinja_env = getattr(request.state, "jinja_env", None) or self.jinja_env

        if jinja_env and self.directory:
            # Use resolved directory path to match what try_path uses
            resolved_dir = Path(self.resolve_directory(self.directory))
            content = await render_file(
                full_path,
                base_context,
                jinja_env,
                resolved_dir,
            )
        else:
            # Fallback if no jinja_env (shouldn't happen in normal usage)
            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                content = await f.read()

        content_bytes = content.encode("utf-8")

        response = ContentResponse(
            content=content_bytes,
            status_code=status_code,
            media_type="text/html; charset=utf-8",
            mtime=stat_result.st_mtime,
            max_age=self.cache_max_age,
            min_size=self.gzip_min_size,
        )

        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)

        return response

    async def get_404_response(self, scope: Scope, receive: Receive, send: Send, request: Request) -> Response:
        """Get a 404 response, using custom 404 page if available."""
        if self.directory is None:
            raise HTTPException(status_code=404)

        result = self.try_path(self.resolve_directory(self.directory), "404.html")
        if result:
            full_path, stat_result = result
            return await self.render_response(full_path, stat_result, scope, receive, send, request, status_code=404)

        raise HTTPException(status_code=404)

    def is_not_modified(self, response_headers: Headers, request_headers: Headers) -> bool:
        """Check if a 304 Not Modified response can be returned."""
        try:
            if_none_match = request_headers["if-none-match"]
            etag = response_headers["etag"]
            etag_value = etag.strip('"')
            for tag in if_none_match.split(","):
                tag = tag.strip().strip('"').strip(" W/")
                if tag == etag_value:
                    return True
        except KeyError:
            pass

        try:
            if_modified_since = parsedate(request_headers["if-modified-since"])
            last_modified = parsedate(response_headers["last-modified"])
            if if_modified_since is not None and last_modified is not None and if_modified_since >= last_modified:
                return True
        except KeyError:
            pass

        return False

    async def check_config(self) -> None:
        """Verify that the directory configuration is valid."""
        if self.directory is None:
            return

        try:
            stat_result = os.stat(self.directory)
        except FileNotFoundError:
            raise RuntimeError(f"TemplateRouter directory '{self.directory}' does not exist.")

        if not (stat.S_ISDIR(stat_result.st_mode) or stat.S_ISLNK(stat_result.st_mode)):
            raise RuntimeError(f"TemplateRouter path '{self.directory}' is not a directory.")
