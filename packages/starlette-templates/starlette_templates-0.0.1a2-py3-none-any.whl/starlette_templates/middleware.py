import types
import typing as t
from starlette.types import ASGIApp, Scope, Receive, Send
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader, select_autoescape
from markdown import Markdown

from starlette_templates import components
from starlette_templates.context import register_jinja_globals_filters
from starlette_templates.components.base import register_components, ComponentModel


class JinjaMiddleware:
    """Middleware to inject Jinja2 environment into request state.

    This middleware creates a Jinja2 environment with the provided template loaders
    and makes it available in the request scope under a specified key, by default
    "jinja_env". This allows downstream components to access the Jinja2 environment
    for template rendering.

    Args:
        app: The ASGI application
        include_websocket: Whether to include WebSocket connections for Jinja2 env injection
        template_loaders: List of Jinja2 template loaders to configure the environment
        include_default_loader: Include the default PackageLoader for "starlette_templates"
        include_markdown_processor: Whether to include a Markdown processor in request state
        component_modules: Optional module, ComponentModel class, or sequence of either to
            auto-register components from. Can be a single module, a single ComponentModel
            class, or a list containing any mix of modules and ComponentModel classes
        jinja_globals: Optional dict of additional global functions/variables to register
            in the Jinja2 environment
        jinja_filters: Optional dict of additional filter functions to register in the
            Jinja2 environment

    Example:
        ```python
        from starlette.applications import Starlette
        from starlette_templates.middleware import JinjaMiddleware
        from jinja2 import PackageLoader, FileSystemLoader

        from myapp import custom_components  # A module with custom components
        from myapp.components import CustomButton, CustomCard  # Individual component classes

        app = Starlette()
        app.add_middleware(
            JinjaMiddleware,
            template_loaders=[
                PackageLoader("myapp", "templates"),
                FileSystemLoader("custom/templates"),
            ],
            include_default_loader=True,
            # Can pass a single module, a single component, or a list of either
            component_modules=[custom_components, CustomButton, CustomCard],
        )
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        include_websocket: bool = True,
        template_loaders: list[t.Union[PackageLoader, FileSystemLoader]] | None = None,
        include_default_loader: bool = True,
        include_markdown_processor: bool = True,
        extra_components: types.ModuleType
        | type[ComponentModel]
        | t.Sequence[types.ModuleType | type[ComponentModel]]
        | None = None,
        jinja_globals: dict[str, t.Any] | None = None,
        jinja_filters: dict[str, t.Callable] | None = None,
    ) -> None:
        self.app = app
        self.include_websocket = include_websocket

        # Build list of template loaders
        self.template_loaders = list(template_loaders) if template_loaders is not None else []

        # Add default PackageLoader for starlette_templates built-in templates
        # This allows using built-in error pages and components
        if include_default_loader:
            self.template_loaders.append(PackageLoader("starlette_templates", "templates"))

        # Create Jinja2 Environment with combined loaders
        # ChoiceLoader tries each loader in order until one succeeds
        # This allows template override: user templates -> built-in templates
        self.jinja_env: Environment = Environment(
            loader=ChoiceLoader(self.template_loaders),
            autoescape=select_autoescape(["html", "xml"]),  # Auto-escape HTML/XML for security
            enable_async=True,  # Required for async template rendering
        )

        # Register global functions and filters (url_for, absurl, jsonify, etc.)
        register_jinja_globals_filters(self.jinja_env, jinja_globals, jinja_filters)

        # Autoregister all components in the environment
        # This makes components available as Jinja2 so you can use them in templates
        # like {{ Button(...) }} without manual registration
        register_components(jinja_env=self.jinja_env, module=components)

        # Register user-provided component modules and classes
        if extra_components:
            # Normalize to list if single module or class provided
            modules_list = (
                [extra_components] if isinstance(extra_components, (types.ModuleType, type)) else extra_components
            )

            for item in modules_list:
                register_components(jinja_env=self.jinja_env, module=item)

        # Optionally add Markdown processor component
        if include_markdown_processor:
            self.markdown_processor = Markdown(
                extensions=[
                    "markdown.extensions.extra",
                    # "markdown.extensions.admonition",  # Use PyMdown admonition instead, using both causes conflicts
                    "markdown.extensions.codehilite",
                    "markdown.extensions.nl2br",
                    "markdown.extensions.sane_lists",
                    "markdown.extensions.smarty",
                    "markdown.extensions.toc",  # TODO: configure class names and slugify function
                    # PyMdown Extensions
                    # https://facelessuser.github.io/pymdown-extensions/
                    "pymdownx.arithmatex",  # LaTeX math support
                    "pymdownx.betterem",  # Improved emphasis handling
                    "pymdownx.blocks.admonition",  # Advanced admonition blocks (::: warning ... :::)
                    "pymdownx.blocks.definition",  # Definition lists (Term: Definition)
                    "pymdownx.blocks.details",  # Details/summary blocks
                    "pymdownx.blocks.html",  # Raw HTML block support (<div>...</div>)
                    "pymdownx.blocks.tab",  # Tabbed content blocks (::: tab Tab Name ... :::)
                    "pymdownx.caret",  # Caret (^) for superscript
                    "pymdownx.details",  # Collapsible details blocks
                    "pymdownx.extra",  # Extra features from PyMdown
                    "pymdownx.highlight",  # syntax highlighting (```python ... ```)
                    "pymdownx.inlinehilite",  # inline code highlighting (`#!py3 import pymdownx; pymdownx.__version__`.)
                    "pymdownx.magiclink",  # Auto-linking URLs and emails
                    "pymdownx.mark",  # ==mark== highlight markup
                    "pymdownx.pathconverter",  # Convert file paths to links ([file.txt])
                    "pymdownx.progressbar",  # Progress bars ([===>     ] 60%)
                    "pymdownx.saneheaders",  # Better header handling
                    "pymdownx.superfences",  # Advanced fenced code blocks (```python ... ```)
                    "pymdownx.tabbed",  # Tabbed content
                    "pymdownx.tasklist",  # Task lists with checkboxes ([ ] Task 1, [x] Task 2)
                    "pymdownx.tilde",  # Subscript and strikethrough
                ],
                extension_configs={
                    "pymdownx.highlight": {
                        "use_pygments": True,
                        "linenums": False,
                        "css_class": "highlight",
                    },
                    "pymdownx.tasklist": {
                        "custom_checkbox": True,
                    },
                    "pymdownx.superfences": {
                        "custom_fences": [],
                    },
                },
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Inject jinja_env into request state for each request.

        Flow:
            1. Middleware receives ASGI scope for new request
            2. Adds jinja_env to scope["state"]["jinja_env"]
            3. Request object exposes this as request.state.jinja_env
            4. TemplateResponse and TemplateFiles access it via request.state.jinja_env
            5. Templates are rendered using this shared jinja_env
        """
        scope_type = scope.get("type")

        # Inject jinja_env for HTTP and optionally WebSocket connections
        if scope_type == "http" or (self.include_websocket and scope_type == "websocket"):
            # Get or create state dict in scope
            state = scope.setdefault("state", {})
            # Store jinja_env in state so it's accessible via request.state.jinja_env
            state["jinja_env"] = self.jinja_env
            # Store markdown processor if enabled
            if hasattr(self, "markdown_processor"):
                state["markdown_processor"] = self.markdown_processor

        # Pass request to next middleware/app
        await self.app(scope, receive, send)
