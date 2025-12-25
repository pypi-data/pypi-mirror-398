"""Templating package for agentic workflow.

Provides clean separation between template infrastructure (TemplateEngine)
and domain logic (ContextResolver).
"""

from .engine import TemplateEngine
from .context import ContextResolver
from .exceptions import TemplateError

__all__ = [
    "TemplateEngine",
    "ContextResolver", 
    "TemplateError",
]