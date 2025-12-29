"""
CRON Scheduling Service client for Huitzo SDK.

This module provides the CronClient class for managing scheduled jobs:
- schedule(): Create a new scheduled job
- list(): List user's scheduled jobs with filtering and pagination
- get(): Get detailed job information with execution history
- update(): Update job schedule, arguments, or enabled status
- delete(): Delete a scheduled job

All methods are async and handle error responses appropriately.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models import CreateJobRequest, UpdateJobRequest

if TYPE_CHECKING:
    from .client import HuitzoTools


class CronClient:
    """
    Client for CRON Scheduling Service.

    This client provides methods for managing scheduled jobs that execute
    commands at specified intervals using CRON expressions.

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Schedule a weekly report job
            job = await sdk.cron.schedule(
                name="weekly_report",
                command="finance.report.generate",
                schedule="0 10 * * 1",  # Every Monday at 10:00 AM
                timezone="America/New_York",
                arguments={"format": "pdf"}
            )
            print(f"Job created: {job['id']}")
            print(f"Next run: {job['next_run_at']}")
        ```
    """

    def __init__(self, sdk: "HuitzoTools"):
        """
        Initialize CronClient.

        Args:
            sdk: Parent HuitzoTools instance
        """
        self._sdk = sdk

    async def schedule(
        self,
        name: str,
        command: str,
        schedule: str,
        timezone: str = "UTC",
        arguments: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Schedule a new CRON job.

        Creates a scheduled job that executes a command at specified intervals.

        Args:
            name: Unique job name within user+plugin scope
            command: Full command path (e.g., "finance.report.generate")
            schedule: CRON expression (5 fields: minute hour day month weekday)
                Examples:
                - "0 10 * * *" = Every day at 10:00 AM
                - "30 14 * * 5" = Every Friday at 2:30 PM
                - "0 */6 * * *" = Every 6 hours
            timezone: IANA timezone (e.g., "America/New_York", "UTC")
            arguments: Command arguments as dictionary
            enabled: Whether job should be active immediately

        Returns:
            Job details including:
            - id: Job UUID
            - name: Job name
            - command: Command path
            - schedule: CRON expression
            - timezone: Timezone
            - enabled: Active status
            - status: Job status ("active", "paused", "error")
            - next_run_at: ISO timestamp of next execution
            - created_at: ISO timestamp of creation

        Raises:
            ValidationError: Invalid CRON expression or timezone
            RateLimitError: Job quota exceeded for user's plan
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            job = await sdk.cron.schedule(
                name="daily_backup",
                command="system.backup.run",
                schedule="0 2 * * *",  # 2 AM daily
                timezone="UTC",
                arguments={"target": "s3"}
            )
            ```
        """
        # Validate request using Pydantic model
        request = CreateJobRequest(
            name=name,
            command=command,
            schedule=schedule,
            timezone=timezone,
            arguments=arguments or {},
            enabled=enabled,
        )

        # Make API request
        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/tools/cron/jobs",
            json=request.model_dump(),
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response, expected_status=201)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List user's scheduled jobs.

        Retrieves a paginated list of jobs with optional status filtering.

        Args:
            status: Optional status filter ("active", "paused", "error")
            limit: Maximum number of results (1-100, default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            Dictionary containing:
            - jobs: List of job objects with details
            - total: Total number of jobs matching filter
            - limit: Limit used for this request
            - offset: Offset used for this request

        Raises:
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Get all active jobs
            result = await sdk.cron.list(status="active", limit=10)
            for job in result["jobs"]:
                print(f"{job['name']}: {job['next_run_at']}")
            ```
        """
        # Build query parameters
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status

        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/cron/jobs",
            params=params,
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def get(self, job_id: str | UUID) -> dict[str, Any]:
        """
        Get detailed job information.

        Retrieves complete job details including recent execution history.

        Args:
            job_id: Job UUID

        Returns:
            Job details including:
            - All job configuration fields
            - executions: List of recent executions (up to 5) with:
                - id: Execution UUID
                - started_at: Start timestamp
                - completed_at: Completion timestamp
                - status: Execution status
                - exit_code: Command exit code
                - duration_ms: Execution duration in milliseconds

        Raises:
            NotFoundError: Job not found or belongs to another user
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            job = await sdk.cron.get("123e4567-e89b-12d3-a456-426614174000")
            print(f"Job status: {job['status']}")
            print(f"Last run: {job['last_run_at']}")
            for execution in job.get("executions", []):
                print(f"  {execution['started_at']}: {execution['status']}")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/cron/jobs/{job_id}",
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def update(
        self,
        job_id: str | UUID,
        schedule: str | None = None,
        timezone: str | None = None,
        arguments: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update a scheduled job.

        Updates job configuration. Only provided fields are updated.

        Args:
            job_id: Job UUID
            schedule: New CRON expression (optional)
            timezone: New IANA timezone (optional)
            arguments: New command arguments (optional)
            enabled: New enabled status (optional)

        Returns:
            Updated job details with new configuration

        Raises:
            ValidationError: Invalid CRON expression or timezone
            NotFoundError: Job not found or belongs to another user
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Pause a job
            job = await sdk.cron.update(job_id, enabled=False)

            # Change schedule to daily at 3 AM
            job = await sdk.cron.update(
                job_id,
                schedule="0 3 * * *",
                timezone="America/New_York"
            )
            ```
        """
        # Validate request using Pydantic model
        request = UpdateJobRequest(
            schedule=schedule,
            timezone=timezone,
            arguments=arguments,
            enabled=enabled,
        )

        # Make API request (only include non-None fields)
        payload = request.model_dump(exclude_none=True)

        async with self._sdk._session.patch(
            f"{self._sdk.base_url}/api/v1/tools/cron/jobs/{job_id}",
            json=payload,
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def delete(self, job_id: str | UUID) -> None:
        """
        Delete a scheduled job.

        Permanently deletes a job and its execution history.

        Args:
            job_id: Job UUID

        Raises:
            NotFoundError: Job not found or belongs to another user
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            await sdk.cron.delete("123e4567-e89b-12d3-a456-426614174000")
            print("Job deleted successfully")
            ```
        """
        # Make API request
        async with self._sdk._session.delete(
            f"{self._sdk.base_url}/api/v1/tools/cron/jobs/{job_id}",
            headers=self._sdk._get_headers(),
        ) as response:
            await self._sdk._handle_response(response, expected_status=204)
