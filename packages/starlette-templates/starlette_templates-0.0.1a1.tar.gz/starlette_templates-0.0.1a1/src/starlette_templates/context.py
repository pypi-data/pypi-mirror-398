"""
Jinja2 context builders and custom filters for starlette_templates templates.
"""

import json
import typing as t
from markupsafe import Markup
from jinja2 import Environment, pass_context
from pydantic_core import to_jsonable_python


def jsonify(data: t.Any, indent: t.Optional[int] = None) -> Markup:
    """Convert data to a JSON string for embedding in HTML templates.

    Uses Pydantic's built-in JSON serialization to handle complex data types
    like datetime, Decimal, and BaseModel instances.

    Args:
        data: The data to serialize to JSON

    Returns:
        A Markup-safe JSON string representation of the data
    """
    jsonable_data = to_jsonable_python(data)
    return Markup(json.dumps(jsonable_data, ensure_ascii=False, indent=indent, separators=(",", ":"), default=str))


@pass_context
def url_for(context: dict, name: str, **path_params: t.Any) -> str:
    """Generate URL for a named route.

    This function uses @pass_context to access the request from the template context.
    The request must be added to the context by TemplateRouter or TemplateResponse.

    Args:
        context: Jinja2 context (automatically passed by Jinja2)
        name: Route name
        **path_params: Path parameters for the route

    Returns:
        URL path for the named route

    Example:
        Assuming a route defined as:

        ```python
        async def user_profile(request: Request):
            ...

        app = Starlette(routes=[
            Route("/users/{user_id}/profile", user_profile, name="user_profile"),
        ])
        ```

        You can generate the URL by name in a template like this:

        ```jinja
        {{ url_for('user_profile', user_id=123) }}
        <!-- Outputs: 'http://example.com/users/123/profile' -->
        ```

    Note:
        This is registered as a Jinja2 global by register_jinja_globals_filters()
        and can be used directly in templates without importing.
    """
    # Extract request from context - this is why we need {"request": request} in context
    request = context["request"]
    return request.url_for(name, **path_params)


@pass_context
def url(context: dict, name: str, path: str = "/") -> str:
    """Generate URL for a mounted application.

    This function builds URLs for Starlette Mount instances by name.
    It's a convenience wrapper around url_for specifically for mounts.

    Args:
        context: Jinja2 context (automatically passed by Jinja2)
        name: Mount name
        path: Path within the mount (default: "/")

    Returns:
        URL path for the mounted application

    Example:
        Assuming a mount defined as:

        ```python
        app = Starlette(routes=[
            Mount("/static", StaticFiles(directory="static"), name="static_files"),
        ])
        ```

        You can generate URLs for files within the mount in a template like this:

        ```jinja
        {{ url('static_files', '/css/style.css') }}
        <!-- Outputs: 'http://example.com/static/css/style.css' -->
        ```

    Note:
        For named routes, use url_for instead. This is specifically for Mount instances.
    """
    request = context["request"]
    return request.url_for(name, path=path)


@pass_context
def absurl(context: dict, path: str) -> str:
    """Build absolute URL from path.

    Converts a relative path to an absolute URL by combining it with the
    request's base URL (scheme + host).

    Args:
        context: Jinja2 context (automatically passed by Jinja2)
        path: URL path (relative or absolute)

    Returns:
        Full absolute URL with scheme and host

    Example:
        Creates an absolute URL for the given path:

        ```jinja
        {{ absurl('/path/to/resource') }}
        <!-- Outputs: 'http://example.com/path/to/resource' -->
        ```

    Note:
        Different from url_for which uses named routes. This takes a literal path.
    """
    request = context["request"]
    # Combine base URL with path, ensuring no double slashes
    return str(request.base_url.replace(path="")) + "/" + path.lstrip("/")


@pass_context
async def markdown_file(context: dict, file_path: str) -> Markup:
    """Load and render a Markdown file to HTML.

    This function reads a Markdown file from the given path, which is always
    relative to any template directories configured in Jinja2 loaders.

    It converts the Markdown content to HTML and marks it safe for inclusion
    in Jinja2 templates. The markdown file can include Jinja2 template syntax
    and has access to the same context variables as the parent template.

    Args:
        context: Jinja2 context (automatically passed by Jinja2)
        file_path: Path to the Markdown file relative to template directories

    Returns:
        Markup-safe HTML content rendered from the Markdown file

    Example:
        In a Jinja2 template:

        ```jinja
        {{ markdown('content/docs/getting-started.md') }}
        ```

        This will load the Markdown file, process it with all configured
        PyMdown extensions, render any Jinja2 syntax within it, and return
        safe HTML markup.
    """
    # Get the request from context to access the markdown processor
    request = context["request"]

    # Get the Jinja2 environment to load the template
    jinja_env = request.state.jinja_env

    # Get the markdown processor from request state
    markdown_processor = request.state.markdown_processor

    # Load the markdown file as a Jinja2 template (this handles template syntax in markdown)
    template = jinja_env.get_template(file_path)

    # Render the template with the current context (so it has access to all template variables)
    # Use render_async since we're in an async environment
    markdown_content = await template.render_async(context)

    # Convert markdown to HTML using the configured markdown processor
    html_content = markdown_processor.convert(markdown_content)

    # Reset the markdown processor state for next use (important for reusability)
    markdown_processor.reset()

    # Return as Markup to mark it safe for HTML rendering
    return Markup(html_content)


def register_jinja_globals_filters(
    jinja_env: Environment,
    jinja_globals: dict[str, t.Any] | None = None,
    jinja_filters: dict[str, t.Callable] | None = None,
) -> None:
    """Register global functions and filters in the Jinja2 environment.

    This function adds commonly used utilities to the Jinja2 environment
    so they can be accessed directly in templates without importing.

    Called by JinjaMiddleware during initialization to set up the environment.

    Uses setdefault to avoid overriding any custom globals that may have been set,
    following the same pattern as Starlette's built-in template functions.

    Args:
        jinja_env: The Jinja2 Environment instance

    Flow:
        1. JinjaMiddleware creates jinja_env with template loaders
        2. Calls this function to register globals/filters
        3. Stores jinja_env in request.state.jinja_env
        4. Templates can use these functions: {{ url_for(...) }}, {{ data|jsonify }}, etc.
        5. @pass_context functions access request from context["request"]
    """
    # Add URL helper functions to Jinja2 globals
    # These use @pass_context to access request from the template context
    # Use setdefault to allow custom implementations to override (same as Starlette)
    jinja_env.globals.setdefault("url_for", url_for)  # {{ url_for('route_name') }}
    jinja_env.globals.setdefault("url", url)  # {{ url('mount_name', '/path') }}
    jinja_env.globals.setdefault("absurl", absurl)  # {{ absurl('/path') }}

    # Add markdown file rendering function
    jinja_env.globals.setdefault("markdown", markdown_file)  # {{ markdown('docs/page.md') }}

    # Add jsonify to both globals and filters for flexibility
    # Can be used as {{ jsonify(data) }} or {{ data|jsonify }}
    jinja_env.globals.setdefault("jsonify", jsonify)  # {{ jsonify(data) }}
    jinja_env.filters.setdefault("jsonify", jsonify)  # {{ data|jsonify }}

    # Register any additional user-provided globals
    if jinja_globals:
        for key, value in jinja_globals.items():
            jinja_env.globals[key] = value
    if jinja_filters:
        for key, func in jinja_filters.items():
            jinja_env.filters[key] = func


__all__ = [
    "jsonify",
    "url_for",
    "url",
    "absurl",
    "markdown_file",
    "register_jinja_globals_filters",
]
