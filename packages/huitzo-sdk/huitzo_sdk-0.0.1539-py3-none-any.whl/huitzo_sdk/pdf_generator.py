"""
PDF Generator client for Huitzo SDK.

This module provides client methods for generating PDFs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class PdfGeneratorClient:
    """Client for PDF generation functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the PdfGeneratorClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def html_to_pdf(
        self,
        html_content: str,
        page_size: str = "A4",
        orientation: str = "portrait",
        margin: str = "1cm",
        css: str | None = None,
        base_url: str | None = None,
    ) -> Dict[str, Any]:
        """
        Generate a PDF from HTML content.

        Args:
            html_content: HTML content to convert to PDF
            page_size: Page size: "A4", "Letter", "Legal", "A3", "A5" (default: "A4")
            orientation: Page orientation: "portrait" or "landscape" (default: "portrait")
            margin: Page margins (CSS format, e.g., "1cm", "0.5in", "10mm") (default: "1cm")
            css: Additional CSS stylesheet (optional)
            base_url: Base URL for resolving relative URLs in HTML (optional)

        Returns:
            Dictionary with:
            - status: "success" or "failed"
            - pdf_base64: Base64-encoded PDF data (if successful)
            - size_bytes: PDF file size in bytes
            - pages: Number of pages (if available)
            - error_message: Error details (if failed)

        Page Sizes:
            - A4: 210mm x 297mm (standard document)
            - Letter: 8.5in x 11in (US standard)
            - Legal: 8.5in x 14in (US legal)
            - A3: 297mm x 420mm (large format)
            - A5: 148mm x 210mm (small format)

        Raises:
            ValidationError: If HTML content or parameters are invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Simple HTML to PDF
            html = '''
            <html>
              <head><title>Invoice</title></head>
              <body>
                <h1>Invoice #12345</h1>
                <p>Total: $100.00</p>
              </body>
            </html>
            '''
            result = await client.pdf_generator.html_to_pdf(html)

            # With custom CSS
            html = '<h1>Report</h1><p>Content here</p>'
            css = '''
            @page { size: Letter; margin: 2cm; }
            h1 { color: #333; font-family: Arial; }
            '''
            result = await client.pdf_generator.html_to_pdf(
                html,
                css=css,
                page_size="Letter"
            )

            # Use base64 PDF
            import base64
            pdf_data = base64.b64decode(result["pdf_base64"])
            with open("output.pdf", "wb") as f:
                f.write(pdf_data)
            ```
        """
        if not html_content or len(html_content) < 10:
            raise ValueError("HTML content is too short or empty")

        valid_page_sizes = ["A4", "Letter", "Legal", "A3", "A5"]
        if page_size not in valid_page_sizes:
            raise ValueError(
                f"Invalid page size: {page_size}. Valid sizes: {', '.join(valid_page_sizes)}"
            )

        if orientation not in ["portrait", "landscape"]:
            raise ValueError(
                f"Invalid orientation: {orientation}. Must be 'portrait' or 'landscape'"
            )

        args = {
            "html_content": html_content,
            "page_size": page_size,
            "orientation": orientation,
            "margin": margin,
        }

        if css is not None:
            args["css"] = css

        if base_url is not None:
            args["base_url"] = base_url

        payload = {
            "function": "pdf_generator.html_to_pdf",
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

    async def markdown_to_pdf(
        self,
        markdown_content: str,
        page_size: str = "A4",
        orientation: str = "portrait",
        title: str | None = None,
    ) -> Dict[str, Any]:
        """
        Generate a PDF from Markdown content.

        This is a convenience function that converts Markdown to HTML
        and then generates a PDF with nice styling.

        Args:
            markdown_content: Markdown content to convert
            page_size: Page size (default: "A4")
            orientation: Page orientation (default: "portrait")
            title: Document title (optional)

        Returns:
            Dictionary with PDF data and status

        Raises:
            ValidationError: If markdown content is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            markdown = '''
            # Report Title

            ## Section 1
            This is a paragraph with **bold** and *italic* text.

            ### Subsection
            - Bullet point 1
            - Bullet point 2

            ### Code Example
            ```python
            def hello():
                print("Hello, world!")
            ```
            '''

            result = await client.pdf_generator.markdown_to_pdf(
                markdown,
                title="My Report"
            )

            # Save PDF to file
            import base64
            pdf_data = base64.b64decode(result["pdf_base64"])
            with open("report.pdf", "wb") as f:
                f.write(pdf_data)
            ```
        """
        if not markdown_content:
            raise ValueError("Markdown content cannot be empty")

        args = {
            "markdown_content": markdown_content,
            "page_size": page_size,
            "orientation": orientation,
        }

        if title is not None:
            args["title"] = title

        payload = {
            "function": "pdf_generator.markdown_to_pdf",
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
