"""
Travrse API client.

Provides both synchronous and asynchronous HTTP clients for the Travrse API.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    overload,
)

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)
from .types import DispatchRequest

if TYPE_CHECKING:
    from .resources.flows import AsyncFlowsResource, FlowsResource
    from .resources.prompts import AsyncPromptsResource, PromptsResource
    from .resources.records import AsyncRecordsResource, RecordsResource


DEFAULT_BASE_URL = "https://api.travrse.ai"
DEFAULT_API_VERSION = "v1"
DEFAULT_TIMEOUT = 30.0


class TravrseClient:
    """
    Synchronous Travrse API client.

    Example:
        ```python
        from travrse import TravrseClient

        client = TravrseClient(api_key="your-api-key")

        # List flows
        flows = client.flows.list()

        # Execute a flow
        result = client.dispatch(
            flow={"name": "My Flow", "steps": [...]},
            options={"stream_response": False}
        )
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the Travrse client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API (default: https://api.travrse.ai)
            api_version: API version (default: v1)
            timeout: Request timeout in seconds (default: 30)
            headers: Additional headers to include in requests
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._api_version = api_version
        self._timeout = timeout
        self._custom_headers = headers or {}

        # Build default headers
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._custom_headers,
        }
        if self._api_key:
            self._headers["Authorization"] = f"Bearer {self._api_key}"

        # Initialize HTTP client
        self._client = httpx.Client(
            base_url=f"{self._base_url}/{self._api_version}",
            headers=self._headers,
            timeout=self._timeout,
        )

        # Lazy-loaded resources
        self._flows: FlowsResource | None = None
        self._records: RecordsResource | None = None
        self._prompts: PromptsResource | None = None

    @property
    def flows(self) -> FlowsResource:
        """Access flows resource."""
        if self._flows is None:
            from .resources.flows import FlowsResource

            self._flows = FlowsResource(self)
        return self._flows

    @property
    def records(self) -> RecordsResource:
        """Access records resource."""
        if self._records is None:
            from .resources.records import RecordsResource

            self._records = RecordsResource(self)
        return self._records

    @property
    def prompts(self) -> PromptsResource:
        """Access prompts resource."""
        if self._prompts is None:
            from .resources.prompts import PromptsResource

            self._prompts = PromptsResource(self)
        return self._prompts

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            data: dict[str, Any] = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text}

        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(
                data.get("error", "Authentication failed"),
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 404:
            raise NotFoundError(
                data.get("error", "Resource not found"),
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                data.get("error", "Rate limit exceeded"),
                status_code=response.status_code,
                response_body=data,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code >= 400:
            raise APIError(
                data.get("error", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response_body=data,
            )

        return data

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request."""
        try:
            response = self._client.get(path, params=params)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        try:
            response = self._client.post(path, json=data, params=params)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    def put(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        try:
            response = self._client.put(path, json=data)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    def patch(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        try:
            response = self._client.patch(path, json=data)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    def delete(self, path: str) -> dict[str, Any]:
        """Make a DELETE request."""
        try:
            response = self._client.delete(path)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    @overload
    def dispatch(
        self,
        request: DispatchRequest | dict[str, Any],
        *,
        stream: Literal[False],
    ) -> dict[str, Any]: ...

    @overload
    def dispatch(
        self,
        request: DispatchRequest | dict[str, Any],
        *,
        stream: Literal[True] = ...,
    ) -> Iterator[dict[str, Any]]: ...

    def dispatch(
        self,
        request: DispatchRequest | dict[str, Any],
        *,
        stream: bool = True,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]:
        """
        Execute a flow via the dispatch API.

        Args:
            request: Dispatch request configuration
            stream: Whether to stream the response (default: True)

        Returns:
            If stream=False: Complete response dict
            If stream=True: Iterator of SSE events
        """
        if isinstance(request, DispatchRequest):
            data = request.model_dump(exclude_none=True, by_alias=True)
        else:
            data = request

        # Ensure options exists and set streaming preference
        if "options" not in data:
            data["options"] = {}
        data["options"]["stream_response"] = stream

        if stream:
            return self._dispatch_stream(data)
        else:
            return self.post("/dispatch", data)

    def _dispatch_stream(self, data: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Stream dispatch response as SSE events."""
        try:
            with self._client.stream("POST", "/dispatch", json=data) as response:
                if response.status_code >= 400:
                    # Read full response for error handling
                    response.read()
                    self._handle_response(response)

                buffer = ""
                for chunk in response.iter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines[-1]  # Keep incomplete line in buffer

                    for line in lines[:-1]:
                        line = line.strip()
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                continue

                # Process any remaining data
                if buffer.strip().startswith("data: "):
                    try:
                        event_data = json.loads(buffer.strip()[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        pass

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    @overload
    def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: Literal[False],
    ) -> dict[str, Any]: ...

    @overload
    def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: Literal[True] = ...,
    ) -> Iterator[dict[str, Any]]: ...

    @overload
    def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: bool,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]: ...

    def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: bool = True,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]:
        """
        Resume a paused flow execution with tool outputs.

        Args:
            execution_id: The execution ID from the paused flow
            tool_outputs: Map of tool names to their results
            stream: Whether to stream the response (default: True)

        Returns:
            If stream=False: Complete response dict
            If stream=True: Iterator of SSE events
        """
        data = {
            "execution_id": execution_id,
            "tool_outputs": tool_outputs,
            "stream_response": stream,
        }

        if stream:
            return self._resume_stream(data)
        else:
            return self.post("/dispatch/resume", data)

    def _resume_stream(self, data: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Stream resume response as SSE events."""
        try:
            with self._client.stream("POST", "/dispatch/resume", json=data) as response:
                if response.status_code >= 400:
                    response.read()
                    self._handle_response(response)

                buffer = ""
                for chunk in response.iter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines[-1]

                    for line in lines[:-1]:
                        line = line.strip()
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                continue

                if buffer.strip().startswith("data: "):
                    try:
                        event_data = json.loads(buffer.strip()[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        pass

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> TravrseClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncTravrseClient:
    """
    Asynchronous Travrse API client.

    Example:
        ```python
        from travrse import AsyncTravrseClient

        async with AsyncTravrseClient(api_key="your-api-key") as client:
            # List flows
            flows = await client.flows.list()

            # Stream flow execution
            async for event in client.dispatch(
                flow={"name": "My Flow", "steps": [...]},
                stream=True
            ):
                print(event)
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the async Travrse client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API (default: https://api.travrse.ai)
            api_version: API version (default: v1)
            timeout: Request timeout in seconds (default: 30)
            headers: Additional headers to include in requests
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._api_version = api_version
        self._timeout = timeout
        self._custom_headers = headers or {}

        # Build default headers
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._custom_headers,
        }
        if self._api_key:
            self._headers["Authorization"] = f"Bearer {self._api_key}"

        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            base_url=f"{self._base_url}/{self._api_version}",
            headers=self._headers,
            timeout=self._timeout,
        )

        # Lazy-loaded resources
        self._flows: AsyncFlowsResource | None = None
        self._records: AsyncRecordsResource | None = None
        self._prompts: AsyncPromptsResource | None = None

    @property
    def flows(self) -> AsyncFlowsResource:
        """Access flows resource."""
        if self._flows is None:
            from .resources.flows import AsyncFlowsResource

            self._flows = AsyncFlowsResource(self)
        return self._flows

    @property
    def records(self) -> AsyncRecordsResource:
        """Access records resource."""
        if self._records is None:
            from .resources.records import AsyncRecordsResource

            self._records = AsyncRecordsResource(self)
        return self._records

    @property
    def prompts(self) -> AsyncPromptsResource:
        """Access prompts resource."""
        if self._prompts is None:
            from .resources.prompts import AsyncPromptsResource

            self._prompts = AsyncPromptsResource(self)
        return self._prompts

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            data: dict[str, Any] = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text}

        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(
                data.get("error", "Authentication failed"),
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 404:
            raise NotFoundError(
                data.get("error", "Resource not found"),
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                data.get("error", "Rate limit exceeded"),
                status_code=response.status_code,
                response_body=data,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code >= 400:
            raise APIError(
                data.get("error", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response_body=data,
            )

        return data

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        try:
            response = await self._client.get(path, params=params)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    async def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        try:
            response = await self._client.post(path, json=data, params=params)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    async def put(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        try:
            response = await self._client.put(path, json=data)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    async def patch(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        try:
            response = await self._client.patch(path, json=data)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    async def delete(self, path: str) -> dict[str, Any]:
        """Make a DELETE request."""
        try:
            response = await self._client.delete(path)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    @overload
    async def dispatch(
        self,
        request: DispatchRequest | dict[str, Any],
        *,
        stream: Literal[False],
    ) -> dict[str, Any]: ...

    @overload
    async def dispatch(
        self,
        request: DispatchRequest | dict[str, Any],
        *,
        stream: Literal[True] = True,
    ) -> AsyncIterator[dict[str, Any]]: ...

    async def dispatch(
        self,
        request: DispatchRequest | dict[str, Any],
        *,
        stream: bool = True,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """
        Execute a flow via the dispatch API.

        Args:
            request: Dispatch request configuration
            stream: Whether to stream the response (default: True)

        Returns:
            If stream=False: Complete response dict
            If stream=True: AsyncIterator of SSE events
        """
        if isinstance(request, DispatchRequest):
            data = request.model_dump(exclude_none=True, by_alias=True)
        else:
            data = request

        # Ensure options exists and set streaming preference
        if "options" not in data:
            data["options"] = {}
        data["options"]["stream_response"] = stream

        if stream:
            return self._dispatch_stream(data)
        else:
            return await self.post("/dispatch", data)

    async def _dispatch_stream(
        self,
        data: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream dispatch response as SSE events."""
        try:
            async with self._client.stream("POST", "/dispatch", json=data) as response:
                if response.status_code >= 400:
                    await response.aread()
                    self._handle_response(response)

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines[-1]

                    for line in lines[:-1]:
                        line = line.strip()
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                continue

                if buffer.strip().startswith("data: "):
                    try:
                        event_data = json.loads(buffer.strip()[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        pass

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    @overload
    async def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: Literal[False],
    ) -> dict[str, Any]: ...

    @overload
    async def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: Literal[True] = ...,
    ) -> AsyncIterator[dict[str, Any]]: ...

    @overload
    async def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: bool,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]: ...

    async def resume(
        self,
        execution_id: str,
        tool_outputs: dict[str, Any],
        *,
        stream: bool = True,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """
        Resume a paused flow execution with tool outputs.

        Args:
            execution_id: The execution ID from the paused flow
            tool_outputs: Map of tool names to their results
            stream: Whether to stream the response (default: True)

        Returns:
            If stream=False: Complete response dict
            If stream=True: AsyncIterator of SSE events
        """
        data = {
            "execution_id": execution_id,
            "tool_outputs": tool_outputs,
            "stream_response": stream,
        }

        if stream:
            return self._resume_stream(data)
        else:
            return await self.post("/dispatch/resume", data)

    async def _resume_stream(
        self,
        data: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream resume response as SSE events."""
        try:
            async with self._client.stream("POST", "/dispatch/resume", json=data) as response:
                if response.status_code >= 400:
                    await response.aread()
                    self._handle_response(response)

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines[-1]

                    for line in lines[:-1]:
                        line = line.strip()
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                continue

                if buffer.strip().startswith("data: "):
                    try:
                        event_data = json.loads(buffer.strip()[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        pass

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncTravrseClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
