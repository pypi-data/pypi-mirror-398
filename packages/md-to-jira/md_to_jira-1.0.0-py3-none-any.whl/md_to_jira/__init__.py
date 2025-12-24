"""Markdown to JIRA and Confluence Markup Syntax Converter."""

__version__ = "1.0.0"

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
