"""
LLM Completions Service client for Huitzo SDK.

This module provides the LLMClient class for managing LLM operations:
- complete(): Generate text completions (streaming and non-streaming)
- complete_with_template(): Use templates for completions
- create_template(): Create reusable prompt templates
- list_templates(): List available templates
- get_template(): Get template by ID or name
- get_usage(): Get usage statistics
- get_quota(): Get quota information
- list_models(): List available LLM models

All methods are async and handle error responses appropriately.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Union
from uuid import UUID

from ..exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ..models import (
    CompleteRequest,
    CompleteTemplateRequest,
    CreateLLMTemplateRequest,
)

if TYPE_CHECKING:
    from ..client import HuitzoTools

__all__ = ["LLMClient"]


class LLMClient:
    """
    Client for LLM Completions Service.

    This client provides methods for generating text completions using various
    LLM providers (OpenAI, Claude) with support for streaming, templates,
    caching, and quota management.

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Generate a completion
            result = await sdk.llm.complete(
                prompt="Explain quantum computing in 2 sentences",
                model="gpt-4o-mini"
            )
            print(f"Completion: {result['content']}")
            print(f"Cost: ${result['cost_usd']:.4f}")
        ```
    """

    def __init__(self, sdk: "HuitzoTools"):
        """
        Initialize LLMClient.

        Args:
            sdk: Parent HuitzoTools instance
        """
        self._sdk = sdk

    async def complete(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        use_cache: bool = True,
        user_id: str | UUID | None = None,
        plugin_id: str = "llm",
    ) -> Union[dict[str, Any], AsyncGenerator[str, None]]:
        """
        Generate a text completion using an LLM.

        Args:
            prompt: Input prompt text
            model: Model name (default: "gpt-4o-mini")
                Available models: gpt-4o, gpt-4o-mini, claude-sonnet-4.5, claude-haiku-4
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
                Higher values = more creative, lower = more deterministic
            max_tokens: Maximum tokens to generate (default: 1000)
            stream: Enable streaming response (default: False)
            use_cache: Use cached responses if available (default: True)
            user_id: User ID (auto-detected if not provided)
            plugin_id: Plugin identifier (default: "llm")

        Returns:
            If stream=False: Dictionary containing:
                - id: Completion UUID
                - content: Generated text
                - model: Model used
                - provider: Provider used (openai, claude)
                - tokens: Token usage (prompt, completion, total)
                - cost_usd: Estimated cost in USD
                - duration_ms: Response time in milliseconds
                - cached: Whether response came from cache
                - finish_reason: Completion finish reason
                - created_at: ISO timestamp

            If stream=True: AsyncGenerator yielding text chunks

        Raises:
            ValidationError: Invalid parameters
            RateLimitError: Quota exceeded
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Rate Limits (per day):
            - FREE: 100 requests, $5/month
            - PRO: 1000 requests, $50/month
            - ENTERPRISE: Unlimited

        Example:
            ```python
            # Non-streaming completion
            result = await sdk.llm.complete(
                prompt="Write a haiku about programming",
                model="gpt-4o-mini",
                temperature=0.9
            )
            print(result['content'])

            # Streaming completion
            async for chunk in await sdk.llm.complete(
                prompt="Explain neural networks",
                stream=True
            ):
                print(chunk, end="", flush=True)
            ```
        """
        # Get user_id from context if not provided
        if user_id is None:
            # TODO: Get from auth context when available
            from uuid import uuid4

            user_id = uuid4()
        elif isinstance(user_id, str):
            user_id = UUID(user_id)

        # Validate request using Pydantic model
        request = CompleteRequest(
            user_id=user_id,
            plugin_id=plugin_id,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            use_cache=use_cache,
        )

        # Make API request
        if stream:
            # Return async generator for streaming
            return self._stream_completion(request)
        else:
            # Return non-streaming response
            async with self._sdk._session.post(
                f"{self._sdk.base_url}/api/v1/tools/llm/complete",
                json=request.model_dump(mode="json", exclude_none=True),
                headers=self._sdk._get_headers(),
            ) as response:
                return await self._sdk._handle_response(response)

    async def _stream_completion(self, request: CompleteRequest) -> AsyncGenerator[str, None]:
        """
        Stream completion chunks from LLM.

        Args:
            request: Completion request

        Yields:
            Text chunks as they arrive
        """
        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/tools/llm/complete",
            json=request.model_dump(mode="json", exclude_none=True),
            headers=self._sdk._get_headers(),
        ) as response:
            # Check for errors
            if response.status != 200:
                await self._sdk._handle_response(response)

            # Stream Server-Sent Events
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    chunk_data = line[6:]  # Remove "data: " prefix
                    if chunk_data:
                        import json

                        try:
                            chunk = json.loads(chunk_data)
                            if "content" in chunk:
                                yield chunk["content"]
                        except json.JSONDecodeError:
                            continue

    async def complete_with_template(
        self,
        template_name: str,
        variables: dict[str, str],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        use_cache: bool = True,
        user_id: str | UUID | None = None,
        plugin_id: str = "llm",
    ) -> Union[dict[str, Any], AsyncGenerator[str, None]]:
        """
        Generate a completion using a template.

        Renders the template with provided variables and then calls the LLM
        with the rendered prompt. Template defaults can be overridden.

        Args:
            template_name: Template name
            variables: Template variables (key-value pairs)
            model: Override model (uses template default if None)
            temperature: Override temperature (uses template default if None)
            max_tokens: Override max tokens (uses template default if None)
            stream: Enable streaming response (default: False)
            use_cache: Use cached responses if available (default: True)
            user_id: User ID (auto-detected if not provided)
            plugin_id: Plugin identifier (default: "llm")

        Returns:
            Same as complete() method

        Raises:
            NotFoundError: Template not found
            ValidationError: Invalid template variables
            RateLimitError: Quota exceeded
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Create template first
            await sdk.llm.create_template(
                name="summarize",
                template="Summarize this text in {{max_sentences}} sentences:\\n\\n{{text}}",
                variables=["text", "max_sentences"]
            )

            # Use template
            result = await sdk.llm.complete_with_template(
                template_name="summarize",
                variables={
                    "text": "Long article text here...",
                    "max_sentences": "3"
                }
            )
            ```
        """
        # Get user_id from context if not provided
        if user_id is None:
            from uuid import uuid4

            user_id = uuid4()
        elif isinstance(user_id, str):
            user_id = UUID(user_id)

        # Validate request using Pydantic model
        request = CompleteTemplateRequest(
            user_id=user_id,
            plugin_id=plugin_id,
            template_name=template_name,
            variables=variables,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            use_cache=use_cache,
        )

        # Make API request
        if stream:
            # TODO: Implement streaming for template completions
            raise NotImplementedError("Streaming not yet supported for template completions")
        else:
            async with self._sdk._session.post(
                f"{self._sdk.base_url}/api/v1/tools/llm/complete-template",
                json=request.model_dump(mode="json", exclude_none=True),
                headers=self._sdk._get_headers(),
            ) as response:
                return await self._sdk._handle_response(response)

    async def create_template(
        self,
        name: str,
        template: str,
        variables: list[str],
        provider_preference: str = "auto",
        model_preference: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        plugin_id: str = "llm",
    ) -> dict[str, Any]:
        """
                Create a new prompt template.

                Templates use Jinja2 syntax for variable substitution and can have
                default model/temperature settings.

                Args:
                    name: Unique template name within plugin scope
                    template: Jinja2 template string
                    variables: List of required variable names
                    provider_preference: Preferred provider (openai, claude, auto)
                    model_preference: Preferred model (optional)
                    temperature: Default temperature (optional)
                    max_tokens: Default max tokens (optional)
                    plugin_id: Plugin identifier (default: "llm")

                Returns:
                    Template details including:
                    - id: Template UUID
                    - plugin_id: Plugin ID
                    - name: Template name
                    - template: Template string
                    - variables: Variable names
                    - provider_preference: Preferred provider
                    - model_preference: Preferred model
                    - created_at: Creation timestamp

                Raises:
                    ValidationError: Invalid Jinja2 syntax or parameters
                    HuitzoAPIError: Template name already exists or other errors
                    AuthenticationError: Invalid or expired API token

                Example:
                    ```python
                    template = await sdk.llm.create_template(
                        name="code_review",
                        template=\"\"\"Review this {{language}} code and provide feedback:

        {{code}}

        Focus on:
        - Code quality
        - Best practices
        - Potential bugs
        \"\"\",
                        variables=["language", "code"],
                        model_preference="gpt-4o",
                        temperature=0.3
                    )
                    ```
        """
        # Validate request using Pydantic model
        request = CreateLLMTemplateRequest(
            plugin_id=plugin_id,
            name=name,
            template=template,
            variables=variables,
            provider_preference=provider_preference,
            model_preference=model_preference,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Make API request
        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/tools/llm/templates",
            json=request.model_dump(exclude_none=True),
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response, expected_status=201)

    async def list_templates(
        self,
        plugin_id: str = "llm",
    ) -> dict[str, Any]:
        """
        List all templates for a plugin.

        Args:
            plugin_id: Plugin identifier (default: "llm")

        Returns:
            List of template objects with:
            - id: Template UUID
            - name: Template name
            - template: Template string
            - variables: Variable names
            - provider_preference: Preferred provider
            - created_at: Creation timestamp

        Raises:
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            templates = await sdk.llm.list_templates()
            for template in templates:
                print(f"{template['name']}: {template['variables']}")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/llm/templates",
            params={"plugin_id": plugin_id},
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def get_template(
        self,
        template_name: str,
        plugin_id: str = "llm",
    ) -> dict[str, Any]:
        """
        Get a specific template by name.

        Args:
            template_name: Template name
            plugin_id: Plugin identifier (default: "llm")

        Returns:
            Template details including all fields

        Raises:
            NotFoundError: Template not found
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            template = await sdk.llm.get_template("code_review")
            print(f"Template: {template['template']}")
            print(f"Variables: {template['variables']}")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/llm/templates/{plugin_id}/{template_name}",
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def get_usage(
        self,
        user_id: str | UUID | None = None,
        plugin_id: str = "llm",
        period: str | date | None = None,
    ) -> dict[str, Any]:
        """
        Get usage statistics for a specific period.

        Returns token usage, cost, and request count for the specified date.

        Args:
            user_id: User ID (auto-detected if not provided)
            plugin_id: Plugin identifier (default: "llm")
            period: Date for statistics (ISO format string or date object, default: today)

        Returns:
            Usage statistics including:
            - user_id: User UUID
            - plugin_id: Plugin ID
            - period: Date
            - requests_count: Number of requests
            - tokens_used: Total tokens used
            - cost_usd: Total cost in USD
            - cached_responses: Number of cached responses

        Raises:
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Get today's usage
            usage = await sdk.llm.get_usage()
            print(f"Requests: {usage['requests_count']}")
            print(f"Cost: ${usage['cost_usd']:.2f}")

            # Get usage for specific date
            from datetime import date
            usage = await sdk.llm.get_usage(period=date(2025, 10, 1))
            ```
        """
        # Get user_id from context if not provided
        if user_id is None:
            from uuid import uuid4

            user_id = uuid4()
        elif isinstance(user_id, str):
            user_id = UUID(user_id)

        # Get period (default to today)
        if period is None:
            period = date.today()
        elif isinstance(period, str):
            period = date.fromisoformat(period)

        # Build query parameters
        params = {
            "user_id": str(user_id),
            "plugin_id": plugin_id,
            "period": period.isoformat(),
        }

        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/llm/usage",
            params=params,
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def get_quota(
        self,
        user_id: str | UUID | None = None,
        user_plan: str = "FREE",
    ) -> dict[str, Any]:
        """
        Get quota information for a user.

        Returns current usage, limits, and whether quota is exceeded.

        Args:
            user_id: User ID (auto-detected if not provided)
            user_plan: User plan (FREE, PRO, ENTERPRISE, default: FREE)

        Returns:
            Quota information including:
            - user_id: User UUID
            - plan: User plan
            - daily_limit: Daily request limit
            - monthly_cost_limit: Monthly cost limit (USD)
            - current_daily_usage: Current daily usage
            - current_monthly_cost: Current monthly cost
            - quota_remaining: Remaining requests today
            - quota_exceeded: Whether quota is exceeded

        Raises:
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            quota = await sdk.llm.get_quota(user_plan="PRO")
            if quota['quota_exceeded']:
                print("Quota exceeded!")
            else:
                print(f"Remaining: {quota['quota_remaining']} requests")
            ```
        """
        # Get user_id from context if not provided
        if user_id is None:
            from uuid import uuid4

            user_id = uuid4()
        elif isinstance(user_id, str):
            user_id = UUID(user_id)

        # Build query parameters
        params = {
            "user_id": str(user_id),
            "user_plan": user_plan,
        }

        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/llm/quota",
            params=params,
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def list_models(self) -> dict[str, Any]:
        """
        List all available LLM models.

        Returns models grouped by provider with pricing information.

        Returns:
            Dictionary containing:
            - models: List of model objects with:
                - name: Model name
                - provider: Provider name
                - description: Model description
                - supports_streaming: Whether streaming is supported
                - cost_per_1k_prompt: Cost per 1K prompt tokens (USD)
                - cost_per_1k_completion: Cost per 1K completion tokens (USD)
            - providers: List of available providers

        Raises:
            HuitzoAPIError: API errors

        Example:
            ```python
            result = await sdk.llm.list_models()
            print(f"Available providers: {result['providers']}")
            for model in result['models']:
                print(f"{model['name']}: ${model['cost_per_1k_prompt']:.4f}/1K tokens")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/llm/models",
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)
