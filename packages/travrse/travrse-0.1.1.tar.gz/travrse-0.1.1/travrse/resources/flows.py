"""
Flows resource for the Travrse SDK.
"""

from __future__ import annotations

from builtins import list as list_type
from typing import TYPE_CHECKING, Any

from ..types import Flow, PaginatedResponse

if TYPE_CHECKING:
    from ..client import AsyncTravrseClient, TravrseClient


class FlowsResource:
    """
    Synchronous flows resource.

    Provides CRUD operations for flows.

    Example:
        ```python
        # List all flows
        response = client.flows.list()
        for flow in response.data:
            print(flow.name)

        # Get a specific flow
        flow = client.flows.get("flow_123")

        # Create a new flow
        flow = client.flows.create(name="My Flow", description="A test flow")

        # Update a flow
        client.flows.update("flow_123", name="Updated Name")

        # Delete a flow
        client.flows.delete("flow_123")
        ```
    """

    def __init__(self, client: TravrseClient) -> None:
        self._client = client

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        direction: str | None = None,
    ) -> PaginatedResponse:
        """
        List all flows.

        Args:
            limit: Maximum number of results to return
            cursor: Pagination cursor
            direction: Pagination direction ('next' or 'prev')

        Returns:
            Paginated response containing flows
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if direction is not None:
            params["direction"] = direction

        response = self._client.get("/flows", params=params if params else None)

        # Transform response data to Flow objects
        flows = [Flow(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=flows, pagination=pagination)

    def get(self, flow_id: str) -> Flow:
        """
        Get a specific flow by ID.

        Args:
            flow_id: The flow ID

        Returns:
            The flow object
        """
        response = self._client.get(f"/flows/{flow_id}")
        return Flow(**response.get("data", response))

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Flow:
        """
        Create a new flow.

        Args:
            name: Flow name
            description: Optional flow description

        Returns:
            The created flow
        """
        data: dict[str, Any] = {"name": name}
        if description is not None:
            data["description"] = description

        response = self._client.post("/flows", data)
        return Flow(**response.get("data", response))

    def update(
        self,
        flow_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Flow:
        """
        Update a flow.

        Args:
            flow_id: The flow ID
            name: New flow name
            description: New flow description
            status: New flow status

        Returns:
            The updated flow
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status

        response = self._client.patch(f"/flows/{flow_id}", data)
        return Flow(**response.get("data", response))

    def delete(self, flow_id: str) -> dict[str, Any]:
        """
        Delete a flow.

        Args:
            flow_id: The flow ID

        Returns:
            Deletion confirmation
        """
        return self._client.delete(f"/flows/{flow_id}")

    def publish(self, flow_id: str) -> Flow:
        """
        Publish a flow (change status to active).

        Args:
            flow_id: The flow ID

        Returns:
            The published flow
        """
        response = self._client.post(f"/flows/{flow_id}/publish")
        return Flow(**response.get("data", response))

    def get_steps(self, flow_id: str) -> list_type[dict[str, Any]]:
        """
        Get all steps for a flow.

        Args:
            flow_id: The flow ID

        Returns:
            List of flow steps
        """
        response = self._client.get(f"/flows/{flow_id}/steps")
        data: list_type[dict[str, Any]] = response.get("data", [])
        return data

    def add_step(
        self,
        flow_id: str,
        *,
        step_type: str,
        name: str,
        config: dict[str, Any],
        order: int | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Add a step to a flow.

        Args:
            flow_id: The flow ID
            step_type: Type of step (e.g., 'prompt', 'transform-data')
            name: Step name
            config: Step configuration
            order: Step order (optional, appends if not specified)
            enabled: Whether the step is enabled

        Returns:
            The created step
        """
        data: dict[str, Any] = {
            "type": step_type,
            "name": name,
            "config": config,
            "enabled": enabled,
        }
        if order is not None:
            data["order"] = order

        response = self._client.post(f"/flows/{flow_id}/steps", data)
        result: dict[str, Any] = response.get("data", response)
        return result


class AsyncFlowsResource:
    """
    Asynchronous flows resource.

    Provides async CRUD operations for flows.

    Example:
        ```python
        # List all flows
        response = await client.flows.list()
        for flow in response.data:
            print(flow.name)

        # Get a specific flow
        flow = await client.flows.get("flow_123")
        ```
    """

    def __init__(self, client: AsyncTravrseClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        direction: str | None = None,
    ) -> PaginatedResponse:
        """
        List all flows.

        Args:
            limit: Maximum number of results to return
            cursor: Pagination cursor
            direction: Pagination direction ('next' or 'prev')

        Returns:
            Paginated response containing flows
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if direction is not None:
            params["direction"] = direction

        response = await self._client.get("/flows", params=params if params else None)

        flows = [Flow(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=flows, pagination=pagination)

    async def get(self, flow_id: str) -> Flow:
        """
        Get a specific flow by ID.

        Args:
            flow_id: The flow ID

        Returns:
            The flow object
        """
        response = await self._client.get(f"/flows/{flow_id}")
        return Flow(**response.get("data", response))

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Flow:
        """
        Create a new flow.

        Args:
            name: Flow name
            description: Optional flow description

        Returns:
            The created flow
        """
        data: dict[str, Any] = {"name": name}
        if description is not None:
            data["description"] = description

        response = await self._client.post("/flows", data)
        return Flow(**response.get("data", response))

    async def update(
        self,
        flow_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Flow:
        """
        Update a flow.

        Args:
            flow_id: The flow ID
            name: New flow name
            description: New flow description
            status: New flow status

        Returns:
            The updated flow
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status

        response = await self._client.patch(f"/flows/{flow_id}", data)
        return Flow(**response.get("data", response))

    async def delete(self, flow_id: str) -> dict[str, Any]:
        """
        Delete a flow.

        Args:
            flow_id: The flow ID

        Returns:
            Deletion confirmation
        """
        return await self._client.delete(f"/flows/{flow_id}")

    async def publish(self, flow_id: str) -> Flow:
        """
        Publish a flow (change status to active).

        Args:
            flow_id: The flow ID

        Returns:
            The published flow
        """
        response = await self._client.post(f"/flows/{flow_id}/publish")
        return Flow(**response.get("data", response))

    async def get_steps(self, flow_id: str) -> list_type[dict[str, Any]]:
        """
        Get all steps for a flow.

        Args:
            flow_id: The flow ID

        Returns:
            List of flow steps
        """
        response = await self._client.get(f"/flows/{flow_id}/steps")
        data: list_type[dict[str, Any]] = response.get("data", [])
        return data

    async def add_step(
        self,
        flow_id: str,
        *,
        step_type: str,
        name: str,
        config: dict[str, Any],
        order: int | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Add a step to a flow.

        Args:
            flow_id: The flow ID
            step_type: Type of step (e.g., 'prompt', 'transform-data')
            name: Step name
            config: Step configuration
            order: Step order (optional, appends if not specified)
            enabled: Whether the step is enabled

        Returns:
            The created step
        """
        data: dict[str, Any] = {
            "type": step_type,
            "name": name,
            "config": config,
            "enabled": enabled,
        }
        if order is not None:
            data["order"] = order

        response = await self._client.post(f"/flows/{flow_id}/steps", data)
        result: dict[str, Any] = response.get("data", response)
        return result
