"""
Runtype - The unified SDK client for building and executing flows, batches, evals, and prompts.

Provides a fluent API with static namespaces for all product areas.

Example:
    ```python
    from travrse import Runtype

    # Global configuration (once per app)
    Runtype.configure(api_key="your-api-key")

    # Build and stream a flow
    result = await Runtype.flows.upsert(name="My Flow")
        .with_record(name="Test", metadata={})
        .prompt(name="Analyze", model="gpt-4o", user_prompt="...")
        .stream()

    # Get complete result
    result = await Runtype.flows.use("flow_123")
        .with_record(name="Test")
        .result()

    # Schedule a batch
    batch = await Runtype.batches.schedule(
        flow_id="flow_123",
        record_type="customers",
    )

    # Run an eval with streaming
    eval_result = await Runtype.evals.run(
        flow_id="flow_123",
        record_type="test_data",
        models=[{"step_name": "Analyze", "model": "gpt-4o"}]
    ).stream()
    ```
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import (
    Any,
    Literal,
)

from .client import AsyncTravrseClient, TravrseClient
from .flow_builder import FlowResult, LocalToolsMap, StreamCallbacks
from .types import (
    DispatchOptions,
    DispatchRequest,
    FlowCompleteEvent,
    FlowConfig,
    FlowErrorEvent,
    FlowMode,
    FlowStartEvent,
    Message,
    RecordConfig,
    RecordMode,
    StepChunkEvent,
    StepCompleteEvent,
    StepStartEvent,
    UpsertOptions,
)

# ============================================================================
# Global Configuration
# ============================================================================


@dataclass
class RuntypeConfig:
    """Configuration for the Runtype client."""

    api_key: str | None = None
    base_url: str = "https://api.travrse.ai"
    api_version: str = "v1"
    timeout: float = 30.0
    headers: dict[str, str] = field(default_factory=dict)


# Global state
_global_config: RuntypeConfig = RuntypeConfig()
_global_client: TravrseClient | None = None
_global_async_client: AsyncTravrseClient | None = None


# ============================================================================
# Internal Step Type
# ============================================================================


@dataclass
class FlowStep:
    """Internal representation of a flow step."""

    id: str
    type: str
    name: str
    order: int
    enabled: bool
    config: dict[str, Any]


# ============================================================================
# RuntypeFlowBuilder
# ============================================================================


class RuntypeFlowBuilder:
    """
    Fluent builder for flows with terminal execution methods.

    Created via Runtype.flows.upsert(), .virtual(), or .use().
    Chain step methods then call .stream() or .result() to execute.
    """

    def __init__(
        self,
        mode: Literal["upsert", "virtual", "existing"],
        config: dict[str, Any] | None = None,
        flow_id: str | None = None,
    ) -> None:
        self._mode = mode
        self._flow_name = config.get("name", "Untitled Flow") if config else "Untitled Flow"
        self._flow_description = config.get("description") if config else None
        self._flow_id = flow_id
        self._steps: list[FlowStep] = []
        self._record_config: RecordConfig | None = None
        self._messages: list[Message] | None = None
        self._options: DispatchOptions = DispatchOptions()
        self._secrets: dict[str, str] | None = None
        self._step_counter = 0
        self._local_tools: LocalToolsMap | None = None

        # Set upsert options if provided
        if config and mode == "upsert":
            self._options.flow_mode = FlowMode.UPSERT
            self._options.upsert_options = UpsertOptions(
                create_version_on_change=config.get("create_version_on_change", True),
                allow_overwrite_external_changes=config.get(
                    "allow_overwrite_external_changes", False
                ),
            )
        elif mode == "virtual":
            self._options.flow_mode = FlowMode.VIRTUAL
        elif mode == "existing":
            self._options.flow_mode = FlowMode.EXISTING

    # =========================================================================
    # Configuration Methods
    # =========================================================================

    def with_record(
        self,
        *,
        id: str | int | None = None,
        name: str | None = None,
        type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntypeFlowBuilder:
        """Set the record configuration."""
        self._record_config = RecordConfig(
            id=id,
            name=name,
            type=type,
            metadata=metadata,
        )
        return self

    def with_messages(self, messages: list[Message | dict[str, Any]]) -> RuntypeFlowBuilder:
        """Set conversation messages."""
        self._messages = [Message(**m) if isinstance(m, dict) else m for m in messages]
        return self

    def with_secrets(self, secrets: dict[str, str]) -> RuntypeFlowBuilder:
        """Set secrets for tool authentication."""
        self._secrets = secrets
        return self

    def with_local_tools(self, local_tools: LocalToolsMap) -> RuntypeFlowBuilder:
        """Set local tools for client-side execution."""
        self._local_tools = local_tools
        return self

    def with_options(
        self,
        *,
        model_override: str | None = None,
        record_mode: RecordMode | str | None = None,
        store_results: bool | None = None,
        auto_append_metadata: bool | None = None,
        debug_mode: bool | None = None,
    ) -> RuntypeFlowBuilder:
        """Set additional dispatch options."""
        if model_override is not None:
            self._options.model_override = model_override
        if record_mode is not None:
            self._options.record_mode = (
                record_mode.value if isinstance(record_mode, RecordMode) else record_mode
            )
        if store_results is not None:
            self._options.store_results = store_results
        if auto_append_metadata is not None:
            self._options.auto_append_metadata = auto_append_metadata
        if debug_mode is not None:
            self._options.debug_mode = debug_mode
        return self

    # =========================================================================
    # Step Methods
    # =========================================================================

    def prompt(
        self,
        *,
        name: str,
        model: str,
        user_prompt: str,
        system_prompt: str | None = None,
        previous_messages: str | list[dict[str, str]] | None = None,
        output_variable: str | None = None,
        response_format: Literal["text", "json"] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        reasoning: bool | None = None,
        stream_output: bool | None = None,
        tools: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a prompt step."""
        config: dict[str, Any] = {
            "model": model,
            "user_prompt": user_prompt,
            "text": user_prompt,
        }
        if system_prompt is not None:
            config["system_prompt"] = system_prompt
        if previous_messages is not None:
            config["previous_messages"] = previous_messages
        if output_variable is not None:
            config["output_variable"] = output_variable
        if response_format is not None:
            config["response_format"] = response_format
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_tokens"] = max_tokens
        if reasoning is not None:
            config["reasoning"] = reasoning
        if stream_output is not None:
            config["stream_output"] = stream_output
        if tools is not None:
            config["tools"] = tools

        self._add_step("prompt", name, config, enabled)
        return self

    def fetch_url(
        self,
        *,
        name: str,
        url: str,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET",
        headers: dict[str, str] | None = None,
        body: str | None = None,
        output_variable: str | None = None,
        fetch_method: Literal["http", "firecrawl"] | None = None,
        error_handling: Literal["fail", "continue", "retry"] | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a fetch URL step."""
        config: dict[str, Any] = {"http": {"url": url, "method": method}}
        if headers is not None:
            config["http"]["headers"] = headers
        if body is not None:
            config["http"]["body"] = body
        if output_variable is not None:
            config["output_variable"] = output_variable
        if fetch_method is not None:
            config["fetch_method"] = fetch_method
        if error_handling is not None:
            config["error_handling"] = error_handling

        self._add_step("fetch-url", name, config, enabled)
        return self

    def transform_data(
        self,
        *,
        name: str,
        script: str,
        output_variable: str | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a transform data step."""
        config: dict[str, Any] = {"script": script}
        if output_variable is not None:
            config["output_variable"] = output_variable

        self._add_step("transform-data", name, config, enabled)
        return self

    def search(
        self,
        *,
        name: str,
        provider: str,
        query: str,
        max_results: int | None = None,
        output_variable: str | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a search step."""
        config: dict[str, Any] = {"provider": provider, "query": query}
        if max_results is not None:
            config["max_results"] = max_results
        if output_variable is not None:
            config["output_variable"] = output_variable

        self._add_step("search", name, config, enabled)
        return self

    def retrieve_record(
        self,
        *,
        name: str,
        record_type: str | None = None,
        record_name: str | None = None,
        output_variable: str | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a retrieve record step."""
        config: dict[str, Any] = {}
        if record_type is not None:
            config["record_type"] = record_type
        if record_name is not None:
            config["record_name"] = record_name
        if output_variable is not None:
            config["output_variable"] = output_variable

        self._add_step("retrieve-record", name, config, enabled)
        return self

    def upsert_record(
        self,
        *,
        name: str,
        record_type: str,
        record_name: str | None = None,
        source_variable: str | None = None,
        merge_strategy: Literal["merge", "replace"] | None = None,
        output_variable: str | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add an upsert record step."""
        config: dict[str, Any] = {"record_type": record_type}
        if record_name is not None:
            config["record_name"] = record_name
        if source_variable is not None:
            config["source_variable"] = source_variable
        if merge_strategy is not None:
            config["merge_strategy"] = merge_strategy
        if output_variable is not None:
            config["output_variable"] = output_variable

        self._add_step("upsert-record", name, config, enabled)
        return self

    def vector_search(
        self,
        *,
        name: str,
        query: str,
        record_type: str | None = None,
        limit: int | None = None,
        threshold: float | None = None,
        output_variable: str | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a vector search step."""
        config: dict[str, Any] = {"query": query}
        if record_type is not None:
            config["record_type"] = record_type
        if limit is not None:
            config["limit"] = limit
        if threshold is not None:
            config["threshold"] = threshold
        if output_variable is not None:
            config["output_variable"] = output_variable

        self._add_step("vector-search", name, config, enabled)
        return self

    def send_email(
        self,
        *,
        name: str,
        to: str,
        subject: str,
        html: str,
        from_address: str | None = None,
        output_variable: str | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a send email step."""
        config: dict[str, Any] = {"to": to, "subject": subject, "html": html}
        if from_address is not None:
            config["from"] = from_address
        if output_variable is not None:
            config["output_variable"] = output_variable

        self._add_step("send-email", name, config, enabled)
        return self

    def conditional(
        self,
        *,
        name: str,
        condition: str,
        true_steps: list[dict[str, Any]] | None = None,
        false_steps: list[dict[str, Any]] | None = None,
        enabled: bool = True,
    ) -> RuntypeFlowBuilder:
        """Add a conditional step."""
        config: dict[str, Any] = {
            "condition": condition,
            "true_steps": true_steps or [],
            "false_steps": false_steps or [],
        }
        self._add_step("conditional", name, config, enabled)
        return self

    # =========================================================================
    # Build Method
    # =========================================================================

    def build(self) -> DispatchRequest:
        """Build the dispatch request."""
        if self._flow_id:
            flow = FlowConfig(id=self._flow_id)
        else:
            steps = [
                {
                    "id": step.id,
                    "type": step.type,
                    "name": step.name,
                    "order": step.order,
                    "enabled": step.enabled,
                    "config": step.config,
                }
                for step in self._steps
            ]
            flow = FlowConfig(name=self._flow_name, steps=steps)

        request = DispatchRequest(flow=flow)

        if self._record_config:
            request.record = self._record_config

        if self._messages:
            request.messages = self._messages

        if self._secrets:
            request.secrets = self._secrets

        options_dict = self._options.model_dump(exclude_none=True)
        if options_dict:
            request.options = self._options

        return request

    # =========================================================================
    # Terminal Execution Methods
    # =========================================================================

    async def stream(
        self,
        callbacks: StreamCallbacks | None = None,
    ) -> FlowResult:
        """
        Execute the flow and stream results.

        Returns a FlowResult with all events after completion.

        Example:
            ```python
            result = await Runtype.flows.upsert(name="My Flow")
                .prompt(name="Step", model="gpt-4o", user_prompt="Hello")
                .stream()

            output = result.get_result("Step")
            ```
        """
        client = Runtype.get_async_client()
        request = self.build()
        request.options = request.options or DispatchOptions()
        request.options.stream_response = True

        events: list[dict[str, Any]] = []

        if self._local_tools:
            return await self._stream_with_local_tools(client, callbacks)

        async for event in await client.dispatch(request, stream=True):
            events.append(event)
            if callbacks:
                self._handle_event(event, callbacks)

        return FlowResult(events)

    async def result(self) -> FlowResult:
        """
        Execute the flow and return complete result (non-streaming).

        Example:
            ```python
            result = await Runtype.flows.use("flow_123")
                .with_record(name="Test")
                .result()

            output = result.get_result("Step Name")
            ```
        """
        client = Runtype.get_async_client()
        request = self.build()
        request.options = request.options or DispatchOptions()
        request.options.stream_response = True  # Still stream internally for events

        events: list[dict[str, Any]] = []

        if self._local_tools:
            return await self._stream_with_local_tools(client, None)

        async for event in await client.dispatch(request, stream=True):
            events.append(event)

        return FlowResult(events)

    def stream_sync(
        self,
        callbacks: StreamCallbacks | None = None,
    ) -> FlowResult:
        """
        Execute the flow synchronously and stream results.

        Example:
            ```python
            result = Runtype.flows.upsert(name="My Flow")
                .prompt(name="Step", model="gpt-4o", user_prompt="Hello")
                .stream_sync()
            ```
        """
        client = Runtype.get_client()
        request = self.build()
        request.options = request.options or DispatchOptions()
        request.options.stream_response = True

        events: list[dict[str, Any]] = []

        if self._local_tools:
            return self._stream_sync_with_local_tools(client, callbacks)

        for event in client.dispatch(request, stream=True):
            events.append(event)
            if callbacks:
                self._handle_event(event, callbacks)

        return FlowResult(events)

    def result_sync(self) -> FlowResult:
        """
        Execute the flow synchronously and return complete result.

        Example:
            ```python
            result = Runtype.flows.use("flow_123")
                .with_record(name="Test")
                .result_sync()
            ```
        """
        return self.stream_sync()

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _add_step(
        self,
        step_type: str,
        name: str,
        config: dict[str, Any],
        enabled: bool = True,
    ) -> None:
        """Add a step to the flow."""
        self._step_counter += 1
        clean_config = {k: v for k, v in config.items() if v is not None}
        self._steps.append(
            FlowStep(
                id=f"step-{self._step_counter}",
                type=step_type,
                name=name,
                order=self._step_counter,
                enabled=enabled,
                config=clean_config,
            )
        )

    def _handle_event(self, event: dict[str, Any], callbacks: StreamCallbacks) -> None:
        """Handle a streaming event with callbacks."""
        event_type = event.get("type")
        try:
            if event_type == "flow_start" and callbacks.on_flow_start:
                callbacks.on_flow_start(FlowStartEvent(**event))
            elif event_type == "step_start" and callbacks.on_step_start:
                callbacks.on_step_start(StepStartEvent(**event))
            elif event_type == "step_chunk" and callbacks.on_step_chunk:
                chunk_event = StepChunkEvent(**event)
                # Get chunk text from raw event (API sends 'text', model has 'chunk')
                chunk_text = event.get("text") or event.get("chunk") or chunk_event.chunk
                callbacks.on_step_chunk(chunk_text, chunk_event)
            elif event_type == "step_complete" and callbacks.on_step_complete:
                complete_event = StepCompleteEvent(**event)
                callbacks.on_step_complete(complete_event.result, complete_event)
            elif event_type == "flow_complete" and callbacks.on_flow_complete:
                callbacks.on_flow_complete(FlowCompleteEvent(**event))
            elif event_type == "flow_error" and callbacks.on_error:
                error_event = FlowErrorEvent(**event)
                callbacks.on_error(Exception(error_event.error))
        except Exception as e:
            if callbacks.on_error:
                callbacks.on_error(e)

    async def _stream_with_local_tools(
        self,
        client: AsyncTravrseClient,
        callbacks: StreamCallbacks | None,
    ) -> FlowResult:
        """Stream with local tools support (pause/resume loop)."""
        import inspect

        request = self.build()
        request.options = request.options or DispatchOptions()
        request.options.stream_response = True

        all_events: list[dict[str, Any]] = []
        event_source: AsyncIterator[dict[str, Any]] = await client.dispatch(request, stream=True)
        execution_id: str | None = None

        while True:
            paused_state: dict[str, Any] | None = None

            async for event in event_source:
                all_events.append(event)
                event_type = event.get("type")

                if event_type == "flow_start" and not execution_id:
                    execution_id = event.get("execution_id") or event.get("executionId")

                if event_type in ("step_waiting_local", "flow_paused", "tool_waiting_local"):
                    paused_state = {
                        "tool_name": event.get("toolName") or event.get("tool_name"),
                        "parameters": event.get("parameters", {}),
                        "execution_id": event.get("executionId")
                        or event.get("execution_id")
                        or execution_id,
                    }

                if callbacks:
                    self._handle_event(event, callbacks)

            if paused_state and paused_state.get("tool_name") and self._local_tools:
                tool_name = paused_state["tool_name"]
                parameters = paused_state["parameters"]
                pause_execution_id = paused_state["execution_id"]

                if not pause_execution_id:
                    raise ValueError("Flow paused but no execution_id provided")

                if tool_name not in self._local_tools:
                    raise ValueError(f'Local tool "{tool_name}" not provided')

                handler = self._local_tools[tool_name]
                tool_result = handler(parameters)
                if inspect.iscoroutine(tool_result):
                    tool_result = await tool_result

                event_source = await client.resume(
                    execution_id=pause_execution_id,
                    tool_outputs={tool_name: tool_result},
                    stream=True,
                )
                continue

            break

        return FlowResult(all_events)

    def _stream_sync_with_local_tools(
        self,
        client: TravrseClient,
        callbacks: StreamCallbacks | None,
    ) -> FlowResult:
        """Stream synchronously with local tools support."""
        request = self.build()
        request.options = request.options or DispatchOptions()
        request.options.stream_response = True

        all_events: list[dict[str, Any]] = []
        event_source: Iterator[dict[str, Any]] = client.dispatch(request, stream=True)
        execution_id: str | None = None

        while True:
            paused_state: dict[str, Any] | None = None

            for event in event_source:
                all_events.append(event)
                event_type = event.get("type")

                if event_type == "flow_start" and not execution_id:
                    execution_id = event.get("execution_id") or event.get("executionId")

                if event_type in ("step_waiting_local", "flow_paused", "tool_waiting_local"):
                    paused_state = {
                        "tool_name": event.get("toolName") or event.get("tool_name"),
                        "parameters": event.get("parameters", {}),
                        "execution_id": event.get("executionId")
                        or event.get("execution_id")
                        or execution_id,
                    }

                if callbacks:
                    self._handle_event(event, callbacks)

            if paused_state and paused_state.get("tool_name") and self._local_tools:
                tool_name = paused_state["tool_name"]
                parameters = paused_state["parameters"]
                pause_execution_id = paused_state["execution_id"]

                if not pause_execution_id:
                    raise ValueError("Flow paused but no execution_id provided")

                if tool_name not in self._local_tools:
                    raise ValueError(f'Local tool "{tool_name}" not provided')

                tool_result = self._local_tools[tool_name](parameters)

                event_source = client.resume(
                    execution_id=pause_execution_id,
                    tool_outputs={tool_name: tool_result},
                    stream=True,
                )
                continue

            break

        return FlowResult(all_events)


# ============================================================================
# Namespace Classes
# ============================================================================


class FlowsNamespace:
    """
    Flows namespace - Build and execute flows.

    Factory methods:
    - upsert(): Create or update a flow by name
    - virtual(): One-off execution without saving
    - use(): Execute an existing flow by ID
    """

    def upsert(
        self,
        *,
        name: str,
        description: str | None = None,
        create_version_on_change: bool = True,
        allow_overwrite_external_changes: bool = False,
    ) -> RuntypeFlowBuilder:
        """
        Create or update a flow by name (upsert mode).

        Example:
            ```python
            result = await Runtype.flows.upsert(name="My Flow")
                .prompt(name="Analyze", model="gpt-4o", user_prompt="...")
                .stream()
            ```
        """
        return RuntypeFlowBuilder(
            mode="upsert",
            config={
                "name": name,
                "description": description,
                "create_version_on_change": create_version_on_change,
                "allow_overwrite_external_changes": allow_overwrite_external_changes,
            },
        )

    def virtual(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> RuntypeFlowBuilder:
        """
        Create a virtual flow (one-off, not saved).

        Example:
            ```python
            result = await Runtype.flows.virtual(name="Temp Flow")
                .prompt(name="Process", model="gpt-4o", user_prompt="...")
                .stream()
            ```
        """
        return RuntypeFlowBuilder(
            mode="virtual",
            config={"name": name, "description": description},
        )

    def use(self, flow_id: str) -> RuntypeFlowBuilder:
        """
        Use an existing flow by ID.

        Example:
            ```python
            result = await Runtype.flows.use("flow_123")
                .with_record(name="Test", type="data")
                .stream()
            ```
        """
        return RuntypeFlowBuilder(mode="existing", flow_id=flow_id)

    async def execute(
        self,
        flow_id: str,
        *,
        record: dict[str, Any] | None = None,
        messages: list[Message | dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> FlowResult:
        """
        Quick execution of an existing flow.

        Example:
            ```python
            result = await Runtype.flows.execute(
                "flow_123",
                record={"name": "Test", "type": "data"},
            )
            ```
        """
        builder = self.use(flow_id)
        if record:
            builder.with_record(**record)
        if messages:
            builder.with_messages(messages)
        return await builder.stream() if stream else await builder.result()


class BatchesNamespace:
    """
    Batches namespace - Schedule and manage batch operations.
    """

    async def schedule(
        self,
        *,
        flow_id: str,
        record_type: str,
        filter: dict[str, Any] | None = None,
        model_override: str | None = None,
    ) -> dict[str, Any]:
        """
        Schedule a batch operation.

        Example:
            ```python
            batch = await Runtype.batches.schedule(
                flow_id="flow_123",
                record_type="customers",
            )
            ```
        """
        client = Runtype.get_async_client()
        data: dict[str, Any] = {
            "flow_id": flow_id,
            "record_type": record_type,
        }
        if filter:
            data["filter"] = filter
        if model_override:
            data["model_override"] = model_override

        return await client.post("/batches", data)

    async def get(self, batch_id: str) -> dict[str, Any]:
        """Get batch status."""
        client = Runtype.get_async_client()
        return await client.get(f"/batches/{batch_id}")

    async def cancel(self, batch_id: str) -> dict[str, Any]:
        """Cancel a running batch."""
        client = Runtype.get_async_client()
        return await client.post(f"/batches/{batch_id}/cancel")

    async def list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List batches."""
        client = Runtype.get_async_client()
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return await client.get("/batches", params=params)


class EvalsNamespace:
    """
    Evals namespace - Run evaluations and compare models.
    """

    def run(
        self,
        *,
        flow_id: str,
        record_type: str | None = None,
        record_ids: list[str] | None = None,
        models: list[dict[str, Any]] | list[list[dict[str, Any]]] | None = None,
    ) -> EvalBuilder:
        """
        Create an eval run builder.

        Example:
            ```python
            result = await Runtype.evals.run(
                flow_id="flow_123",
                record_type="test_data",
                models=[{"step_name": "Analyze", "model": "gpt-4o"}]
            ).stream()
            ```
        """
        return EvalBuilder(
            flow_id=flow_id,
            record_type=record_type,
            record_ids=record_ids,
            models=models,
        )


class EvalBuilder:
    """Builder for eval execution."""

    def __init__(
        self,
        flow_id: str,
        record_type: str | None = None,
        record_ids: list[str] | None = None,
        models: list[dict[str, Any]] | list[list[dict[str, Any]]] | None = None,
    ) -> None:
        self._flow_id = flow_id
        self._record_type = record_type
        self._record_ids = record_ids
        self._models = models

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        """Execute eval with streaming results."""
        client = Runtype.get_async_client()
        data = {"flow_id": self._flow_id, "stream": True}
        if self._record_type:
            data["record_type"] = self._record_type
        if self._record_ids:
            data["record_ids"] = self._record_ids
        if self._models:
            data["models"] = self._models

        async for event in await client.dispatch(
            {"flow": {"id": self._flow_id}, "options": {"stream_response": True}},
            stream=True,
        ):
            yield event

    async def submit(self) -> dict[str, Any]:
        """Submit eval as background job."""
        client = Runtype.get_async_client()
        data: dict[str, Any] = {"flow_id": self._flow_id}
        if self._record_type:
            data["record_type"] = self._record_type
        if self._record_ids:
            data["record_ids"] = self._record_ids
        if self._models:
            data["models"] = self._models

        return await client.post("/evals", data)


class PromptsNamespace:
    """
    Prompts namespace - Manage and execute prompts.
    """

    def run(
        self,
        prompt_id: str,
        *,
        record_id: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> PromptBuilder:
        """
        Create a prompt execution builder.

        Example:
            ```python
            result = await Runtype.prompts.run("prompt_123", record_id="rec_456").result()
            ```
        """
        return PromptBuilder(
            prompt_id=prompt_id,
            record_id=record_id,
            variables=variables,
        )

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List prompts."""
        client = Runtype.get_async_client()
        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return await client.get("/prompts", params=params)

    async def get(self, prompt_id: str) -> dict[str, Any]:
        """Get a prompt by ID."""
        client = Runtype.get_async_client()
        return await client.get(f"/prompts/{prompt_id}")

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new prompt."""
        client = Runtype.get_async_client()
        return await client.post("/prompts", data)

    async def update(self, prompt_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a prompt."""
        client = Runtype.get_async_client()
        return await client.patch(f"/prompts/{prompt_id}", data)

    async def delete(self, prompt_id: str) -> dict[str, Any]:
        """Delete a prompt."""
        client = Runtype.get_async_client()
        return await client.delete(f"/prompts/{prompt_id}")


class PromptBuilder:
    """Builder for prompt execution."""

    def __init__(
        self,
        prompt_id: str,
        record_id: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> None:
        self._prompt_id = prompt_id
        self._record_id = record_id
        self._variables = variables

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        """Execute prompt with streaming."""
        client = Runtype.get_async_client()
        data: dict[str, Any] = {"prompt_id": self._prompt_id, "stream": True}
        if self._record_id:
            data["record_id"] = self._record_id
        if self._variables:
            data["variables"] = self._variables

        async for event in await client.dispatch(
            {"prompt": {"id": self._prompt_id}, "options": {"stream_response": True}},
            stream=True,
        ):
            yield event

    async def result(self) -> dict[str, Any]:
        """Execute prompt and get complete result."""
        client = Runtype.get_async_client()
        data: dict[str, Any] = {"prompt_id": self._prompt_id}
        if self._record_id:
            data["record_id"] = self._record_id
        if self._variables:
            data["variables"] = self._variables

        return await client.post("/prompts/execute", data)


# ============================================================================
# Main Runtype Class
# ============================================================================


class Runtype:
    """
    Runtype - Main entry point for the SDK.

    Use static methods and namespaces to interact with the API.

    Example:
        ```python
        from travrse import Runtype

        # Configure once at startup
        Runtype.configure(api_key="your-api-key")

        # Use namespaces
        result = await Runtype.flows.upsert(name="My Flow")
            .prompt(name="Step", model="gpt-4o", user_prompt="Hello")
            .stream()
        ```
    """

    # Namespace instances (class attributes for direct access)
    flows: FlowsNamespace
    batches: BatchesNamespace
    evals: EvalsNamespace
    prompts: PromptsNamespace

    @classmethod
    def configure(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Configure the global Runtype client.

        Call this once at app startup.

        Example:
            ```python
            Runtype.configure(api_key="your-api-key")
            ```
        """
        global _global_config, _global_client, _global_async_client

        if api_key is not None:
            _global_config.api_key = api_key
        if base_url is not None:
            _global_config.base_url = base_url
        if api_version is not None:
            _global_config.api_version = api_version
        if timeout is not None:
            _global_config.timeout = timeout
        if headers is not None:
            _global_config.headers = headers

        # Reset clients so they get recreated with new config
        _global_client = None
        _global_async_client = None

    @classmethod
    def get_client(cls) -> TravrseClient:
        """Get the global sync client, creating if needed."""
        global _global_client
        if _global_client is None:
            _global_client = TravrseClient(
                api_key=_global_config.api_key,
                base_url=_global_config.base_url,
                api_version=_global_config.api_version,
                timeout=_global_config.timeout,
                headers=_global_config.headers or None,
            )
        return _global_client

    @classmethod
    def get_async_client(cls) -> AsyncTravrseClient:
        """Get the global async client, creating if needed."""
        global _global_async_client
        if _global_async_client is None:
            _global_async_client = AsyncTravrseClient(
                api_key=_global_config.api_key,
                base_url=_global_config.base_url,
                api_version=_global_config.api_version,
                timeout=_global_config.timeout,
                headers=_global_config.headers or None,
            )
        return _global_async_client

    @classmethod
    def create_client(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> TravrseClient:
        """Create a new sync client with custom config."""
        return TravrseClient(
            api_key=api_key or _global_config.api_key,
            base_url=base_url or _global_config.base_url,
            timeout=timeout or _global_config.timeout,
        )

    @classmethod
    def create_async_client(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> AsyncTravrseClient:
        """Create a new async client with custom config."""
        return AsyncTravrseClient(
            api_key=api_key or _global_config.api_key,
            base_url=base_url or _global_config.base_url,
            timeout=timeout or _global_config.timeout,
        )


# Initialize Runtype namespace class attributes
Runtype.flows = FlowsNamespace()
Runtype.batches = BatchesNamespace()
Runtype.evals = EvalsNamespace()
Runtype.prompts = PromptsNamespace()
