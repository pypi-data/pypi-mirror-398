"""
FastDjango Templates.
Jinja2 template engine with Django-like features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastdjango.conf import settings

if TYPE_CHECKING:
    from starlette.responses import Response


# Global templates instance
_templates: Jinja2Templates | None = None


def configure_templates(directories: list[str | Path]) -> Jinja2Templates:
    """Configure Jinja2 templates with directories."""
    global _templates

    # Convert to strings
    dirs = [str(d) for d in directories if Path(d).exists()]

    if not dirs:
        # Add default template directory
        default_dir = Path(__file__).parent.parent / "contrib" / "admin" / "templates"
        if default_dir.exists():
            dirs.append(str(default_dir))

    _templates = Jinja2Templates(directory=dirs[0] if dirs else ".")

    # Add all directories to the loader
    if len(dirs) > 1:
        _templates.env.loader = FileSystemLoader(dirs)

    # Configure environment
    _configure_environment(_templates.env)

    return _templates


def _configure_environment(env: Environment) -> None:
    """Add custom filters, globals, and extensions."""
    # Add globals
    env.globals["settings"] = settings
    env.globals["static"] = static_url
    env.globals["url"] = url_for
    env.globals["csrf_token"] = csrf_token
    env.globals["csrf_input"] = csrf_input

    # Add filters
    env.filters["date"] = date_filter
    env.filters["time"] = time_filter
    env.filters["datetime"] = datetime_filter
    env.filters["truncate"] = truncate_filter
    env.filters["pluralize"] = pluralize_filter
    env.filters["yesno"] = yesno_filter
    env.filters["default_if_none"] = default_if_none_filter
    env.filters["linebreaks"] = linebreaks_filter
    env.filters["striptags"] = striptags_filter


def get_templates() -> Jinja2Templates:
    """Get the global templates instance."""
    global _templates
    if _templates is None:
        configure_templates([])
    return _templates  # type: ignore


@property
def templates() -> Jinja2Templates:
    """Property to access templates."""
    return get_templates()


# Make templates accessible as a module-level variable
class TemplatesProxy:
    def __getattr__(self, name):
        return getattr(get_templates(), name)


templates = TemplatesProxy()


def render(
    template_name: str,
    context: dict[str, Any] | None = None,
    request: Request | None = None,
    status_code: int = 200,
) -> Any:
    """
    Render a template.

    Usage:
        @router.get("/")
        async def home(request: Request):
            posts = await Post.objects.all()
            return render("home.html", {"posts": posts}, request=request)
    """
    tmpl = get_templates()
    ctx = context or {}

    if request is not None:
        ctx["request"] = request
        return tmpl.TemplateResponse(
            request=request,
            name=template_name,
            context=ctx,
            status_code=status_code,
        )

    # Without request, just render the template
    template = tmpl.get_template(template_name)
    return template.render(**ctx)


def render_to_string(template_name: str, context: dict[str, Any] | None = None) -> str:
    """
    Render a template to a string.

    Usage:
        html = render_to_string("email/welcome.html", {"user": user})
    """
    tmpl = get_templates()
    template = tmpl.get_template(template_name)
    return template.render(**(context or {}))


# Template helper functions

def static_url(path: str) -> str:
    """Get static file URL."""
    static_url = settings.STATIC_URL.rstrip("/")
    return f"{static_url}/{path.lstrip('/')}"


def url_for(name: str, **kwargs: Any) -> str:
    """Generate URL for a named route."""
    # This would need to integrate with FastAPI's url_for
    return f"/{name}"


def csrf_token(request: Request) -> str:
    """Get CSRF token from request."""
    return getattr(request.state, "csrf_token", "")


def csrf_input(request: Request) -> str:
    """Generate CSRF hidden input."""
    token = csrf_token(request)
    return f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">'


# Template filters

def date_filter(value: Any, format: str = "%Y-%m-%d") -> str:
    """Format a date."""
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime(format)
    return str(value)


def time_filter(value: Any, format: str = "%H:%M:%S") -> str:
    """Format a time."""
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime(format)
    return str(value)


def datetime_filter(value: Any, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime."""
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime(format)
    return str(value)


def truncate_filter(value: str, length: int = 50, suffix: str = "...") -> str:
    """Truncate a string."""
    if len(value) <= length:
        return value
    return value[:length].rsplit(" ", 1)[0] + suffix


def pluralize_filter(value: int, singular: str = "", plural: str = "s") -> str:
    """Return singular or plural suffix."""
    if value == 1:
        return singular
    return plural


def yesno_filter(value: bool, yes: str = "Yes", no: str = "No", none: str = "None") -> str:
    """Return yes/no/none based on boolean value."""
    if value is None:
        return none
    return yes if value else no


def default_if_none_filter(value: Any, default: str = "") -> Any:
    """Return default if value is None."""
    return default if value is None else value


def linebreaks_filter(value: str) -> str:
    """Convert newlines to HTML line breaks."""
    import html
    escaped = html.escape(value)
    return escaped.replace("\n", "<br>")


def striptags_filter(value: str) -> str:
    """Remove HTML tags."""
    import re
    return re.sub(r"<[^>]*>", "", value)
