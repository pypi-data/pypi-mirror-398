"""
Prompts resource for the Travrse SDK.
"""

from __future__ import annotations

from builtins import list as list_type
from typing import TYPE_CHECKING, Any, Literal

from ..types import PaginatedResponse, Prompt, ResponseFormat

if TYPE_CHECKING:
    from ..client import AsyncTravrseClient, TravrseClient


class PromptsResource:
    """
    Synchronous prompts resource.

    Provides CRUD operations for prompts.

    Example:
        ```python
        # List all prompts
        response = client.prompts.list()
        for prompt in response.data:
            print(prompt.name)

        # Get a specific prompt
        prompt = client.prompts.get("prompt_123")

        # Create a new prompt
        prompt = client.prompts.create(
            name="Summarizer",
            text="Summarize the following text: {{input}}",
            model="gpt-4o"
        )

        # Update a prompt
        client.prompts.update("prompt_123", text="New prompt text")

        # Delete a prompt
        client.prompts.delete("prompt_123")
        ```
    """

    def __init__(self, client: TravrseClient) -> None:
        self._client = client

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        direction: Literal["next", "prev"] | None = None,
    ) -> PaginatedResponse:
        """
        List all prompts.

        Args:
            limit: Maximum number of results to return
            cursor: Pagination cursor
            direction: Pagination direction

        Returns:
            Paginated response containing prompts
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if direction is not None:
            params["direction"] = direction

        response = self._client.get("/prompts", params=params if params else None)

        prompts = [Prompt(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=prompts, pagination=pagination)

    def get(self, prompt_id: str) -> Prompt:
        """
        Get a specific prompt by ID.

        Args:
            prompt_id: The prompt ID

        Returns:
            The prompt object
        """
        response = self._client.get(f"/prompts/{prompt_id}")
        return Prompt(**response.get("data", response))

    def create(
        self,
        *,
        name: str,
        text: str,
        model: str | None = None,
        response_format: ResponseFormat | str = ResponseFormat.TEXT,
        input_variables: str | None = None,
        flow_ids: list_type[str] | None = None,
    ) -> Prompt:
        """
        Create a new prompt.

        Args:
            name: Prompt name
            text: Prompt text/template
            model: Model to use for execution
            response_format: Expected response format
            input_variables: Input variable definitions
            flow_ids: IDs of flows to attach this prompt to

        Returns:
            The created prompt
        """
        data: dict[str, Any] = {
            "name": name,
            "text": text,
        }
        if model is not None:
            data["model"] = model
        if response_format is not None:
            data["response_format"] = (
                response_format.value
                if isinstance(response_format, ResponseFormat)
                else response_format
            )
        if input_variables is not None:
            data["input_variables"] = input_variables
        if flow_ids is not None:
            data["flow_ids"] = flow_ids

        response = self._client.post("/prompts", data)
        return Prompt(**response.get("data", response))

    def update(
        self,
        prompt_id: str,
        *,
        name: str | None = None,
        text: str | None = None,
        model: str | None = None,
        response_format: ResponseFormat | str | None = None,
        input_variables: str | None = None,
    ) -> Prompt:
        """
        Update a prompt.

        Args:
            prompt_id: The prompt ID
            name: New prompt name
            text: New prompt text
            model: New model
            response_format: New response format
            input_variables: New input variables

        Returns:
            The updated prompt
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if text is not None:
            data["text"] = text
        if model is not None:
            data["model"] = model
        if response_format is not None:
            data["response_format"] = (
                response_format.value
                if isinstance(response_format, ResponseFormat)
                else response_format
            )
        if input_variables is not None:
            data["input_variables"] = input_variables

        response = self._client.patch(f"/prompts/{prompt_id}", data)
        return Prompt(**response.get("data", response))

    def delete(self, prompt_id: str) -> dict[str, Any]:
        """
        Delete a prompt.

        Args:
            prompt_id: The prompt ID

        Returns:
            Deletion confirmation
        """
        return self._client.delete(f"/prompts/{prompt_id}")


class AsyncPromptsResource:
    """
    Asynchronous prompts resource.

    Provides async CRUD operations for prompts.

    Example:
        ```python
        # List all prompts
        response = await client.prompts.list()
        for prompt in response.data:
            print(prompt.name)
        ```
    """

    def __init__(self, client: AsyncTravrseClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        direction: Literal["next", "prev"] | None = None,
    ) -> PaginatedResponse:
        """
        List all prompts.

        Args:
            limit: Maximum number of results to return
            cursor: Pagination cursor
            direction: Pagination direction

        Returns:
            Paginated response containing prompts
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if direction is not None:
            params["direction"] = direction

        response = await self._client.get("/prompts", params=params if params else None)

        prompts = [Prompt(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=prompts, pagination=pagination)

    async def get(self, prompt_id: str) -> Prompt:
        """
        Get a specific prompt by ID.

        Args:
            prompt_id: The prompt ID

        Returns:
            The prompt object
        """
        response = await self._client.get(f"/prompts/{prompt_id}")
        return Prompt(**response.get("data", response))

    async def create(
        self,
        *,
        name: str,
        text: str,
        model: str | None = None,
        response_format: ResponseFormat | str = ResponseFormat.TEXT,
        input_variables: str | None = None,
        flow_ids: list_type[str] | None = None,
    ) -> Prompt:
        """
        Create a new prompt.

        Args:
            name: Prompt name
            text: Prompt text/template
            model: Model to use for execution
            response_format: Expected response format
            input_variables: Input variable definitions
            flow_ids: IDs of flows to attach this prompt to

        Returns:
            The created prompt
        """
        data: dict[str, Any] = {
            "name": name,
            "text": text,
        }
        if model is not None:
            data["model"] = model
        if response_format is not None:
            data["response_format"] = (
                response_format.value
                if isinstance(response_format, ResponseFormat)
                else response_format
            )
        if input_variables is not None:
            data["input_variables"] = input_variables
        if flow_ids is not None:
            data["flow_ids"] = flow_ids

        response = await self._client.post("/prompts", data)
        return Prompt(**response.get("data", response))

    async def update(
        self,
        prompt_id: str,
        *,
        name: str | None = None,
        text: str | None = None,
        model: str | None = None,
        response_format: ResponseFormat | str | None = None,
        input_variables: str | None = None,
    ) -> Prompt:
        """
        Update a prompt.

        Args:
            prompt_id: The prompt ID
            name: New prompt name
            text: New prompt text
            model: New model
            response_format: New response format
            input_variables: New input variables

        Returns:
            The updated prompt
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if text is not None:
            data["text"] = text
        if model is not None:
            data["model"] = model
        if response_format is not None:
            data["response_format"] = (
                response_format.value
                if isinstance(response_format, ResponseFormat)
                else response_format
            )
        if input_variables is not None:
            data["input_variables"] = input_variables

        response = await self._client.patch(f"/prompts/{prompt_id}", data)
        return Prompt(**response.get("data", response))

    async def delete(self, prompt_id: str) -> dict[str, Any]:
        """
        Delete a prompt.

        Args:
            prompt_id: The prompt ID

        Returns:
            Deletion confirmation
        """
        return await self._client.delete(f"/prompts/{prompt_id}")
