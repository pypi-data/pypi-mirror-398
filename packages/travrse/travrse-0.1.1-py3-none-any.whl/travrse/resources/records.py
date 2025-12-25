"""
Records resource for the Travrse SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ..types import PaginatedResponse, Record

if TYPE_CHECKING:
    from ..client import AsyncTravrseClient, TravrseClient


class RecordsResource:
    """
    Synchronous records resource.

    Provides CRUD operations for records.

    Example:
        ```python
        # List all records
        response = client.records.list()
        for record in response.data:
            print(record.name, record.type)

        # Get a specific record
        record = client.records.get("rec_123")

        # Create a new record
        record = client.records.create(
            type="customer",
            name="Acme Corp",
            metadata={"industry": "tech", "size": "enterprise"}
        )

        # Update a record
        client.records.update("rec_123", metadata={"updated": True})

        # Delete a record
        client.records.delete("rec_123")
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
        metadata_keys: str | None = None,
        metadata_keys_all: str | None = None,
        min_fields: int | None = None,
        max_fields: int | None = None,
        sort_by: str | None = None,
        sort_order: Literal["asc", "desc"] | None = None,
        include_fields: bool | None = None,
    ) -> PaginatedResponse:
        """
        List all records.

        Args:
            limit: Maximum number of results to return
            cursor: Pagination cursor
            direction: Pagination direction
            metadata_keys: Filter by records containing any of these metadata keys
            metadata_keys_all: Filter by records containing all of these metadata keys
            min_fields: Minimum number of metadata fields
            max_fields: Maximum number of metadata fields
            sort_by: Field to sort by
            sort_order: Sort order
            include_fields: Include available fields in response

        Returns:
            Paginated response containing records
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if direction is not None:
            params["direction"] = direction
        if metadata_keys is not None:
            params["metadata_keys"] = metadata_keys
        if metadata_keys_all is not None:
            params["metadata_keys_all"] = metadata_keys_all
        if min_fields is not None:
            params["min_fields"] = min_fields
        if max_fields is not None:
            params["max_fields"] = max_fields
        if sort_by is not None:
            params["sort_by"] = sort_by
        if sort_order is not None:
            params["sort_order"] = sort_order
        if include_fields is not None:
            params["include_fields"] = include_fields

        response = self._client.get("/records", params=params if params else None)

        records = [Record(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=records, pagination=pagination)

    def get(self, record_id: str) -> Record:
        """
        Get a specific record by ID.

        Args:
            record_id: The record ID

        Returns:
            The record object
        """
        response = self._client.get(f"/records/{record_id}")
        return Record(**response.get("data", response))

    def create(
        self,
        *,
        type: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Record:
        """
        Create a new record.

        Args:
            type: Record type (e.g., 'customer', 'product')
            name: Record name
            metadata: Optional metadata dictionary

        Returns:
            The created record
        """
        data: dict[str, Any] = {
            "type": type,
            "name": name,
        }
        if metadata is not None:
            data["metadata"] = metadata

        response = self._client.post("/records", data)
        return Record(**response.get("data", response))

    def update(
        self,
        record_id: str,
        *,
        name: str | None = None,
        type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Record:
        """
        Update a record.

        Args:
            record_id: The record ID
            name: New record name
            type: New record type
            metadata: New or updated metadata

        Returns:
            The updated record
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if type is not None:
            data["type"] = type
        if metadata is not None:
            data["metadata"] = metadata

        response = self._client.patch(f"/records/{record_id}", data)
        return Record(**response.get("data", response))

    def delete(self, record_id: str) -> dict[str, Any]:
        """
        Delete a record.

        Args:
            record_id: The record ID

        Returns:
            Deletion confirmation
        """
        return self._client.delete(f"/records/{record_id}")

    def list_by_type(
        self,
        record_type: str,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PaginatedResponse:
        """
        List records by type.

        Args:
            record_type: The record type to filter by
            limit: Maximum number of results
            cursor: Pagination cursor

        Returns:
            Paginated response containing records of the specified type
        """
        params: dict[str, Any] = {"type": record_type}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        response = self._client.get("/records", params=params)

        records = [Record(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=records, pagination=pagination)


class AsyncRecordsResource:
    """
    Asynchronous records resource.

    Provides async CRUD operations for records.

    Example:
        ```python
        # List all records
        response = await client.records.list()
        for record in response.data:
            print(record.name, record.type)
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
        metadata_keys: str | None = None,
        metadata_keys_all: str | None = None,
        min_fields: int | None = None,
        max_fields: int | None = None,
        sort_by: str | None = None,
        sort_order: Literal["asc", "desc"] | None = None,
        include_fields: bool | None = None,
    ) -> PaginatedResponse:
        """
        List all records.

        Args:
            limit: Maximum number of results to return
            cursor: Pagination cursor
            direction: Pagination direction
            metadata_keys: Filter by records containing any of these metadata keys
            metadata_keys_all: Filter by records containing all of these metadata keys
            min_fields: Minimum number of metadata fields
            max_fields: Maximum number of metadata fields
            sort_by: Field to sort by
            sort_order: Sort order
            include_fields: Include available fields in response

        Returns:
            Paginated response containing records
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if direction is not None:
            params["direction"] = direction
        if metadata_keys is not None:
            params["metadata_keys"] = metadata_keys
        if metadata_keys_all is not None:
            params["metadata_keys_all"] = metadata_keys_all
        if min_fields is not None:
            params["min_fields"] = min_fields
        if max_fields is not None:
            params["max_fields"] = max_fields
        if sort_by is not None:
            params["sort_by"] = sort_by
        if sort_order is not None:
            params["sort_order"] = sort_order
        if include_fields is not None:
            params["include_fields"] = include_fields

        response = await self._client.get("/records", params=params if params else None)

        records = [Record(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=records, pagination=pagination)

    async def get(self, record_id: str) -> Record:
        """
        Get a specific record by ID.

        Args:
            record_id: The record ID

        Returns:
            The record object
        """
        response = await self._client.get(f"/records/{record_id}")
        return Record(**response.get("data", response))

    async def create(
        self,
        *,
        type: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Record:
        """
        Create a new record.

        Args:
            type: Record type (e.g., 'customer', 'product')
            name: Record name
            metadata: Optional metadata dictionary

        Returns:
            The created record
        """
        data: dict[str, Any] = {
            "type": type,
            "name": name,
        }
        if metadata is not None:
            data["metadata"] = metadata

        response = await self._client.post("/records", data)
        return Record(**response.get("data", response))

    async def update(
        self,
        record_id: str,
        *,
        name: str | None = None,
        type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Record:
        """
        Update a record.

        Args:
            record_id: The record ID
            name: New record name
            type: New record type
            metadata: New or updated metadata

        Returns:
            The updated record
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if type is not None:
            data["type"] = type
        if metadata is not None:
            data["metadata"] = metadata

        response = await self._client.patch(f"/records/{record_id}", data)
        return Record(**response.get("data", response))

    async def delete(self, record_id: str) -> dict[str, Any]:
        """
        Delete a record.

        Args:
            record_id: The record ID

        Returns:
            Deletion confirmation
        """
        return await self._client.delete(f"/records/{record_id}")

    async def list_by_type(
        self,
        record_type: str,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PaginatedResponse:
        """
        List records by type.

        Args:
            record_type: The record type to filter by
            limit: Maximum number of results
            cursor: Pagination cursor

        Returns:
            Paginated response containing records of the specified type
        """
        params: dict[str, Any] = {"type": record_type}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        response = await self._client.get("/records", params=params)

        records = [Record(**item) for item in response.get("data", [])]
        pagination = response.get("pagination", {})

        return PaginatedResponse(data=records, pagination=pagination)
