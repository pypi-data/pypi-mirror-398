# python
"""Markdown conversion utilities (simplified, Mermaid-enabled).

This module converts GitHub Flavored Markdown (GFM) to HTML and keeps Mermaid
fenced code blocks by turning them into <div class="mermaid">...</div>.
Client-side Mermaid.js should render those at runtime (e.g., in Swagger UI).

If inline rendering (e.g., SVG) is desired, provide a custom `mermaid_to_html`
callable that transforms Mermaid code into final HTML.

Python 3.11 compatible.
"""
from __future__ import annotations

import datetime
import re
from typing import Callable, Final, Optional

import mistune

# Single shared Markdown converter with GFM plugins.
_MARKDOWN_PLUGINS: Final[list[str]] = ["strikethrough", "table", "url"]
_markdown = mistune.create_markdown(plugins=_MARKDOWN_PLUGINS)

# Matches ```mermaid ... ``` and ~~~mermaid ... ~~~, capturing the content.
# Groups:
#   1: leading newline (or start)
#   2: fence marker (``` or ~~~)
#   3: inner Mermaid content
_MERMAID_FENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"(^|\n)(```|~~~)mermaid[^\n]*\n(.*?)(\n\2)",
    re.IGNORECASE | re.DOTALL,
)


def _inject_mermaid_blocks(text: str, mermaid_to_html: Callable[[str], str]) -> str:
    """Replace Mermaid fenced blocks with HTML produced by `mermaid_to_html`.

    Args:
        text: Input Markdown text.
        mermaid_to_html: Callable that converts Mermaid code into HTML.

    Returns:
        Markdown text where Mermaid fences are replaced by HTML blocks.
    """

    def _repl(match: re.Match[str]) -> str:
        leading = match.group(1)
        content = match.group(3)
        return f"{leading}{mermaid_to_html(content)}"

    return _MERMAID_FENCE_RE.sub(_repl, text)


def markdown_to_html(
    text: str,
    last_updated: Optional[datetime] = None,
) -> str:
    """Convert Markdown (GFM) to HTML, preserving Mermaid as HTML.

    Args:
        text: The Markdown source string or None.
        last_updated: Optional datetime to append as "Last Updated" info.

    Returns:
        The converted HTML string, or None if `text` is None.
    """
    # Convert Markdown to HTML.
    html_out = _markdown(text)

    # At the end of the HTML, add the Last Updated info
    text_exists = text is not None and text.strip() != ""
    if text_exists and last_updated is not None:
        last_updated_text = datetime.datetime.fromtimestamp(last_updated).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        html_out += (
            f"<hr><p><em>Resource Last Updated: " f"{last_updated_text}</em></p>"
        )

    return html_out
