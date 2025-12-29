"""
QR Code client for Huitzo SDK.

This module provides client methods for QR code generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class QrCodeClient:
    """Client for QR code generation functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the QrCodeClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def generate_qr_code(
        self,
        data: str,
        size: int = 300,
        error_correction: str = "M",
        format: str = "png",
    ) -> Dict[str, Any]:
        """
        Generate a QR code from data.

        Args:
            data: Data to encode in QR code (URL, text, etc.)
            size: Image size in pixels (default: 300)
            error_correction: Error correction level: "L", "M", "Q", "H" (default: "M")
            format: Image format: "png" or "svg" (default: "png")

        Returns:
            Dictionary with:
            - status: "success" or "failed"
            - image_base64: Base64-encoded image data
            - format: Image format
            - size: Image dimensions
            - error_message: Error details (if failed)

        Error Correction Levels:
            - L: ~7% error correction (good for clean environments)
            - M: ~15% error correction (default, balanced)
            - Q: ~25% error correction (good for less clean environments)
            - H: ~30% error correction (best for damaged/dirty surfaces)

        Raises:
            ValidationError: If data or parameters are invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Generate URL QR code
            result = await client.qrcode.generate_qr_code(
                "https://example.com",
                size=400,
                error_correction="H"
            )

            # Decode and save image
            import base64
            image_data = base64.b64decode(result["image_base64"])
            with open("qrcode.png", "wb") as f:
                f.write(image_data)

            # Generate text QR code
            result = await client.qrcode.generate_qr_code(
                "Hello, World!",
                size=200
            )
            ```
        """
        if not data:
            raise ValueError("Data cannot be empty")

        if size < 100 or size > 2000:
            raise ValueError("Size must be between 100 and 2000 pixels")

        if error_correction not in ["L", "M", "Q", "H"]:
            raise ValueError("Error correction must be L, M, Q, or H")

        if format not in ["png", "svg"]:
            raise ValueError("Format must be png or svg")

        args = {
            "data": data,
            "size": size,
            "error_correction": error_correction,
            "format": format,
        }

        payload = {
            "function": "qrcode_generator.generate_qr_code",
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

    async def generate_wifi_qr_code(
        self,
        ssid: str,
        password: str,
        security: str = "WPA",
        hidden: bool = False,
        size: int = 300,
    ) -> Dict[str, Any]:
        """
        Generate a WiFi QR code for easy network connection.

        When scanned, this QR code allows devices to automatically
        connect to the WiFi network.

        Args:
            ssid: WiFi network name (SSID)
            password: WiFi password
            security: Security type: "WPA", "WEP", "nopass" (default: "WPA")
            hidden: Is the network hidden? (default: False)
            size: Image size in pixels (default: 300)

        Returns:
            Dictionary with QR code image data

        Raises:
            ValidationError: If SSID or parameters are invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Generate WiFi QR code
            result = await client.qrcode.generate_wifi_qr_code(
                ssid="MyNetwork",
                password="SecurePassword123",
                security="WPA",
                size=400
            )

            # Save QR code
            import base64
            image_data = base64.b64decode(result["image_base64"])
            with open("wifi_qr.png", "wb") as f:
                f.write(image_data)

            # Open network (no password)
            result = await client.qrcode.generate_wifi_qr_code(
                ssid="PublicNetwork",
                password="",
                security="nopass"
            )
            ```
        """
        if not ssid:
            raise ValueError("SSID cannot be empty")

        if security not in ["WPA", "WEP", "nopass"]:
            raise ValueError("Security must be WPA, WEP, or nopass")

        if security != "nopass" and not password:
            raise ValueError("Password required for WPA/WEP networks")

        if size < 100 or size > 2000:
            raise ValueError("Size must be between 100 and 2000 pixels")

        args = {
            "ssid": ssid,
            "password": password,
            "security": security,
            "hidden": hidden,
            "size": size,
        }

        payload = {
            "function": "qrcode_generator.generate_wifi_qr_code",
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
