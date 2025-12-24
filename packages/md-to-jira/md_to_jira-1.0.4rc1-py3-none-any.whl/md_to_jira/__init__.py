"""Markdown to JIRA and Confluence Markup Syntax Converter."""

try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("md-to-jira")
    except PackageNotFoundError:
        __version__ = "0.0.0.dev0"  # Package not installed
except ImportError:
    # Python < 3.8
    __version__ = "0.0.0.dev0"

from .md_to_jira import (
    convert_line as md_convert_line,
    convert_multiline_elements as md_convert_multiline_elements,
    markdown_to_jira,
)
from .jira_to_md import convert_line as jira_convert_line
from .jira_to_md import convert_multiline_elements as jira_convert_multiline_elements
from .jira_to_md import jira_to_markdown

# Backwards-compatible aliases for existing API names
convert_line = md_convert_line
convert_multiline_elements = md_convert_multiline_elements

__all__ = [
    # Markdown → Jira helpers (old and new, consistent names)
    "convert_line",
    "convert_multiline_elements",
    "md_convert_line",
    "md_convert_multiline_elements",
    "markdown_to_jira",
    # Jira → Markdown helpers
    "jira_convert_line",
    "jira_convert_multiline_elements",
    "jira_to_markdown",
]
