from . import schemathesis
from ._version import VERSION
from .http import HttpInteraction, HttpRequest, HttpResponse  # noqa: F401

__version__ = VERSION

try:
    # Try professional first, fall back to community
    try:
        from tracecov_professional import CoverageMap  # noqa: F401

        __edition__ = "professional"  # pragma: no cover
    except ImportError:  # pragma: no cover
        from tracecov_community import CoverageMap  # noqa: F401

        __edition__ = "community"
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "No TraceCov implementation found. Try reinstalling 'tracecov' or install 'tracecov-professional' for the professional edition."
    ) from exc


__all__ = [
    "__version__",
    "__edition__",
    "HttpInteraction",
    "HttpRequest",
    "HttpResponse",
    "CoverageMap",
    "schemathesis",
]
