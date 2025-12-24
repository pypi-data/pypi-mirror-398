"""
Sigmoda Python SDK.

Call `sigmoda.init(...)` to configure, then use `sigmoda.openai.responses.create(...)`
or `sigmoda.openai.chat.completions.create(...)`
or `sigmoda.log_event(...)` to send events.
"""

from importlib import metadata as _metadata

try:
    __version__ = _metadata.version("sigmoda")
except _metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

from .config import init, get_config  # noqa: F401
from .client import flush, get_stats, log_event  # noqa: F401
from . import openai_wrapper as openai  # noqa: F401

__all__ = ["__version__", "init", "get_config", "log_event", "flush", "get_stats", "openai"]
