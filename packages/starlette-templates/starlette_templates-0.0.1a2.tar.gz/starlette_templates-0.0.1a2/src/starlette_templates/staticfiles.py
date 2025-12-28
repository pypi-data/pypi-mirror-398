import os
import mimetypes
import typing as t
from pathlib import Path
from starlette.types import Scope
from starlette.responses import Response
from starlette.staticfiles import StaticFiles as StarletteStaticFiles

PathLike = t.Union[str, "os.PathLike[str]", Path]


class StaticFiles(StarletteStaticFiles):
    """Enhanced StaticFiles with gzip compression, caching, and multi-directory support.

    Features:
    - Automatic gzip handling for .gz files with proper Content-Encoding headers
    - Strong HTTP caching (ETag, Cache-Control, Last-Modified)
    - Multi-directory fallback support (searches directories in priority order)

    When a .gz file is requested directly, this class automatically:
    1. Strips the .gz extension from the Content-Type detection
    2. Sets Content-Encoding: gzip header
    3. Adds Vary: Accept-Encoding header
    4. Adds strong caching headers (Cache-Control: public, max-age=31536000, immutable)

    When multiple directories are provided, files are searched in priority order,
    allowing application static files to override framework static files.

    Args:
        directories: Directory paths to search (in priority order)
        packages: Package resources to serve
        html: Enable HTML mode
        check_dir: Whether to check if directories exist on initialization
        follow_symlink: Whether to follow symbolic links

    Example with single directory:
        ```python
        static = StaticFiles(directories=["static"])
        ```

    Example with multiple directories (priority-based override):
        ```python
        static = StaticFiles(
            directories=[Path("app/static"), Path("framework/static")],
            packages=[("myapp", "static")],
        )
        ```

    Example serving pre-compressed files:
        ```html
        <link rel="stylesheet" href="{{ url_for('static', path='vendor/bootstrap.css.gz') }}">
        ```

    The browser receives:
    - Content-Type: text/css
    - Content-Encoding: gzip
    - Cache-Control: public, max-age=31536000, immutable
    - And automatically decompresses the content
    """

    def __init__(
        self,
        *,
        directories: t.List[PathLike] | None = None,
        packages: list[str | tuple[str, str]] | None = None,
        html: bool = False,
        check_dir: bool = True,
        follow_symlink: bool = False,
    ) -> None:
        # Default to empty list if not provided
        if directories is None:
            directories = []

        # Check directories exist if requested
        if check_dir and directories:
            for dir_path in directories:
                if not os.path.isdir(dir_path):
                    raise RuntimeError(f"Directory '{dir_path}' does not exist")

        # Initialize parent with first directory (or None if no directories)
        # Starlette's StaticFiles will use all_directories for lookup
        directory = directories[0] if directories else None
        super().__init__(
            directory=directory,
            packages=packages,
            html=html,
            check_dir=False,  # We already checked above
            follow_symlink=follow_symlink,
        )

        # Override all_directories to include all our directories (if multiple provided)
        # Starlette's lookup_path method already iterates through all_directories
        if len(directories) > 1:
            self.all_directories = [Path(d) for d in directories]

    def file_response(
        self,
        full_path: PathLike,
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        """Override to add gzip and caching headers for .gz files."""
        # Call parent which handles ETag generation and 304 Not Modified checks
        response = super().file_response(full_path, stat_result, scope, status_code)

        # If it's a 304 Not Modified response, just return it
        if response.status_code == 304:
            return response

        # Check if the file path ends with .gz
        path_str = str(full_path)
        if path_str.endswith(".gz"):
            # Get the original filename without .gz extension
            original_path = path_str[:-3]

            # Determine the content type based on the original filename
            content_type, _ = mimetypes.guess_type(original_path)

            if content_type:
                response.headers["content-type"] = content_type

            # Set gzip encoding headers
            response.headers["content-encoding"] = "gzip"
            response.headers["vary"] = "accept-encoding"

        # Add strong caching headers for all static files
        # Starlette already added ETag and Last-Modified, we just enhance Cache-Control
        response.headers["cache-control"] = "public, max-age=31536000, immutable"

        return response
