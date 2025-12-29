"""
Formatters client for Huitzo SDK.

This module provides client methods for text formatting and conversion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class FormattersClient:
    """Client for text formatting and conversion functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the FormattersClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def markdown_to_html(
        self,
        markdown_text: str,
        sanitize: bool = True,
        extensions: list[str] | None = None,
        syntax_highlight: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert Markdown text to HTML.

        Supports GitHub Flavored Markdown (GFM) features like tables,
        fenced code blocks, and task lists.

        Args:
            markdown_text: Markdown-formatted text to convert
            sanitize: Sanitize HTML output to prevent XSS (default: True)
            extensions: Custom Markdown extensions (optional, overrides defaults)
            syntax_highlight: Enable syntax highlighting for code blocks (default: False)

        Returns:
            Dictionary with:
            - status: "success" or "failed"
            - html: Converted HTML
            - toc: Table of contents HTML (if generated)
            - sanitized: Whether HTML was sanitized
            - error_message: Error details (if failed)

        Default Extensions:
            - extra: Tables, fenced code blocks, abbreviations, footnotes
            - nl2br: Newlines to <br> tags
            - sane_lists: Better list handling
            - toc: Table of contents generation

        Raises:
            ValidationError: If markdown text is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Basic conversion
            markdown = '''
            # Hello World

            This is **bold** and this is *italic*.

            ## Code Example
            ```python
            def hello():
                print("Hello!")
            ```
            '''

            result = await client.formatters.markdown_to_html(markdown)
            print(result["html"])

            # With syntax highlighting
            result = await client.formatters.markdown_to_html(
                markdown,
                syntax_highlight=True
            )

            # Unsafe HTML (no sanitization)
            result = await client.formatters.markdown_to_html(
                markdown,
                sanitize=False
            )
            ```
        """
        if not markdown_text:
            raise ValueError("Markdown text cannot be empty")

        args = {
            "markdown_text": markdown_text,
            "sanitize": sanitize,
            "syntax_highlight": syntax_highlight,
        }

        if extensions is not None:
            args["extensions"] = extensions

        payload = {
            "function": "formatters.markdown_to_html",
            "args": args,
        }

        response = await self._sdk._client.post(
            f"{self._sdk._base_url}/api/v1/executor/run",
            json=payload,
        )

        result = await self._sdk._handle_response(response, expected_status=200)

        # Extract result from executor envelope
        if result.get("status") == "success":
            return result.get("result", {})
        else:
            raise Exception(result.get("error", "Unknown error"))

    async def html_to_text(
        self,
        html_content: str,
        preserve_links: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert HTML to plain text.

        Strips HTML tags and extracts readable text content.

        Args:
            html_content: HTML content to convert
            preserve_links: Preserve URLs in [text](url) format (default: False)

        Returns:
            Dictionary with:
            - status: "success" or "failed"
            - text: Plain text output
            - input_length: Original HTML length
            - output_length: Plain text length
            - error_message: Error details (if failed)

        Raises:
            ValidationError: If HTML content is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Basic conversion
            html = '''
            <html>
              <body>
                <h1>Title</h1>
                <p>This is <strong>important</strong> text.</p>
                <a href="https://example.com">Link</a>
              </body>
            </html>
            '''

            result = await client.formatters.html_to_text(html)
            print(result["text"])
            # Output: Title\nThis is important text.\nLink

            # Preserve links
            result = await client.formatters.html_to_text(html, preserve_links=True)
            print(result["text"])
            # Output: Title\nThis is important text.\nLink (https://example.com)
            ```
        """
        if not html_content:
            raise ValueError("HTML content cannot be empty")

        args = {
            "html_content": html_content,
            "preserve_links": preserve_links,
        }

        payload = {
            "function": "formatters.html_to_text",
            "args": args,
        }

        response = await self._sdk._client.post(
            f"{self._sdk._base_url}/api/v1/executor/run",
            json=payload,
        )

        result = await self._sdk._handle_response(response, expected_status=200)

        # Extract result from executor envelope
        if result.get("status") == "success":
            return result.get("result", {})
        else:
            raise Exception(result.get("error", "Unknown error"))
