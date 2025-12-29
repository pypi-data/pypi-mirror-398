"""
Static Site Hosting Service client for Huitzo SDK.

This module provides the SitesClient class for managing temporary static site deployments:
- deploy(): Upload and deploy a static site from a .zip archive
- list(): List all sites for the authenticated user
- get(): Get details for a specific site
- delete(): Delete a site and its files

All methods are async and handle error responses appropriately.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp

from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)

if TYPE_CHECKING:
    from .client import HuitzoTools


class SitesClient:
    """
    Client for Static Site Hosting Service.

    This client provides methods for deploying and managing temporary static sites
    from .zip archives with automatic expiration.

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Deploy a static site
            site = await sdk.sites.deploy(
                zip_file_path="./dist.zip",
                project_name="my-portfolio",
                expiration_minutes=2880  # 2 days
            )
            print(f"Site live at: {site['access_url']}")
        ```
    """

    def __init__(self, sdk: "HuitzoTools"):
        """
        Initialize SitesClient.

        Args:
            sdk: Parent HuitzoTools instance
        """
        self._sdk = sdk

    async def deploy(
        self,
        zip_file_path: str | Path,
        project_name: str,
        expiration_minutes: int = 1440,
    ) -> dict[str, Any]:
        """
        Deploy a static site from a zip archive.

        Uploads a .zip file containing static assets (HTML, CSS, JS, images) and
        deploys it as a temporary publicly accessible site.

        Args:
            zip_file_path: Path to the .zip file containing the static site
                Must be <= 50MB and contain valid static files
            project_name: Unique name for the project (1-100 characters)
                Must match pattern: ^[a-z0-9][a-z0-9-]*[a-z0-9]$
            expiration_minutes: Minutes until site expires (default: 1440 = 24h)
                Minimum: 60 (1 hour), Maximum: 10080 (7 days)

        Returns:
            Dictionary containing:
            - id: Site UUID
            - project_name: Project name
            - access_url: Public URL to access the site
            - size_bytes: Total size of uploaded files
            - status: Site status ("active", "expired")
            - expires_at: ISO timestamp when site will expire
            - created_at: ISO timestamp of creation

        Raises:
            ValidationError: If zip file doesn't exist, is too large (>50MB),
                project_name is invalid, or expiration is out of range
            QuotaExceededError: If user has reached site limits (5 sites or 200MB)
            RateLimitError: If API rate limit exceeded
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Quota Limits (per user):
            - Maximum sites: 5
            - Total storage: 200MB
            - File size: 50MB per zip

        Example:
            ```python
            # Deploy a site with 2-day expiration
            site = await sdk.sites.deploy(
                zip_file_path="./build/dist.zip",
                project_name="landing-page",
                expiration_minutes=2880
            )
            print(f"Deployed to: {site['access_url']}")
            print(f"Expires at: {site['expires_at']}")
            ```
        """
        # Convert to Path object and validate existence
        zip_path = Path(zip_file_path)
        if not zip_path.exists():
            raise ValidationError(f"Zip file not found: {zip_file_path}")

        if not zip_path.is_file():
            raise ValidationError(f"Path is not a file: {zip_file_path}")

        # Check file size (50MB limit)
        file_size = zip_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if file_size > max_size:
            raise ValidationError(f"Zip file exceeds 50MB limit: {file_size / 1024 / 1024:.2f}MB")

        # Read file into memory
        try:
            with open(zip_path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            raise ValidationError(f"Failed to read zip file: {e}")

        # Create multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field(
            "file",
            file_data,
            filename=zip_path.name,
            content_type="application/zip",
        )
        form_data.add_field("project_name", project_name)
        form_data.add_field("expiration_minutes", str(expiration_minutes))

        # Make API request with multipart upload
        # Note: Remove Content-Type header to let aiohttp set it with boundary
        headers = {
            "Authorization": f"Bearer {self._sdk.api_token}",
            "User-Agent": "huitzo-sdk/1.0.0",
        }

        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/tools/sites/deploy",
            data=form_data,
            headers=headers,
        ) as response:
            return await self._handle_deploy_response(response)

    async def _handle_deploy_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """
        Handle deployment response with specific error handling.

        Args:
            response: aiohttp ClientResponse object

        Returns:
            Parsed JSON response

        Raises:
            ValidationError: 400 - Invalid input or file too large
            QuotaExceededError: 403 - Site quota exceeded
            RateLimitError: 429 - Rate limit exceeded
            AuthenticationError: 401 - Authentication failed
            HuitzoAPIError: Other errors
        """
        status = response.status

        # Success case
        if status == 201:
            try:
                return await response.json()
            except Exception as e:
                raise HuitzoAPIError(
                    f"Invalid JSON response from API",
                    status_code=status,
                )

        # Handle error responses
        try:
            error_data = await response.json()
            error_message = error_data.get("detail", f"HTTP {status}")
        except Exception:
            try:
                error_message = await response.text()
            except Exception:
                error_message = f"HTTP {status}"
            error_data = {}

        # Map status codes to exceptions with specific messages
        if status == 413:
            raise ValidationError(
                message="Zip file exceeds 50MB limit",
                response_data=error_data,
            )
        elif status == 400:
            raise ValidationError(
                message=error_message,
                response_data=error_data,
            )
        elif status == 403:
            # Check if this is a quota error or auth error
            if "quota" in error_message.lower() or "limit" in error_message.lower():
                raise QuotaExceededError(
                    message=error_message,
                    response_data=error_data,
                )
            else:
                raise AuthenticationError(
                    message=error_message,
                    status_code=status,
                    response_data=error_data,
                )
        elif status == 401:
            raise AuthenticationError(
                message=error_message,
                status_code=status,
                response_data=error_data,
            )
        elif status == 429:
            raise RateLimitError(
                message=error_message,
                response_data=error_data,
            )
        else:
            raise HuitzoAPIError(
                message=error_message,
                status_code=status,
                response_data=error_data,
            )

    async def list(self, include_expired: bool = False) -> list[dict[str, Any]]:
        """
        List all sites for the authenticated user.

        Retrieves a list of sites with their current status and metadata.

        Args:
            include_expired: Include expired sites in results (default: False)

        Returns:
            List of site dictionaries, each containing:
            - id: Site UUID
            - project_name: Project name
            - access_url: Public URL to access the site
            - size_bytes: Total size of files
            - status: Site status ("active", "expired")
            - expires_at: ISO timestamp when site will expire
            - created_at: ISO timestamp of creation

        Raises:
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Get all active sites
            sites = await sdk.sites.list()
            for site in sites:
                print(f"{site['project_name']}: {site['access_url']}")

            # Include expired sites
            all_sites = await sdk.sites.list(include_expired=True)
            ```
        """
        # Build query parameters
        params: dict[str, Any] = {}
        if include_expired:
            params["include_expired"] = "true"

        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/sites",
            params=params,
            headers=self._sdk._get_headers(),
        ) as response:
            result = await self._sdk._handle_response(response)
            # API returns {"sites": [...]}
            return result.get("sites", [])

    async def get(self, site_id: str) -> dict[str, Any]:
        """
        Get details for a specific site.

        Retrieves complete site information including current status.

        Args:
            site_id: UUID of the site

        Returns:
            Site details dictionary containing:
            - id: Site UUID
            - project_name: Project name
            - access_url: Public URL to access the site
            - size_bytes: Total size of files
            - status: Site status ("active", "expired")
            - expires_at: ISO timestamp when site will expire
            - created_at: ISO timestamp of creation

        Raises:
            NotFoundError: If site doesn't exist or user doesn't own it
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            site = await sdk.sites.get("123e4567-e89b-12d3-a456-426614174000")
            print(f"Status: {site['status']}")
            print(f"URL: {site['access_url']}")
            print(f"Size: {site['size_bytes']} bytes")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/sites/{site_id}",
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def delete(self, site_id: str) -> None:
        """
        Delete a site and its files.

        Permanently deletes the site and all associated files. This frees up
        quota for new deployments.

        Args:
            site_id: UUID of the site to delete

        Raises:
            NotFoundError: If site doesn't exist or user doesn't own it
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            await sdk.sites.delete("123e4567-e89b-12d3-a456-426614174000")
            print("Site deleted successfully")
            ```
        """
        # Make API request
        async with self._sdk._session.delete(
            f"{self._sdk.base_url}/api/v1/tools/sites/{site_id}",
            headers=self._sdk._get_headers(),
        ) as response:
            await self._sdk._handle_response(response, expected_status=204)
