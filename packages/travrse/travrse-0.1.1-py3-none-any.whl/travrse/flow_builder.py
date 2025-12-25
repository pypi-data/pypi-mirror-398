"""
FlowBuilder - Fluent builder for constructing and executing flows.

Provides a chainable API for building flows with steps, making flow
construction more readable and type-safe.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
)

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

if TYPE_CHECKING:
    from .client import AsyncTravrseClient, TravrseClient

# Type alias for local tool handlers
LocalToolHandler = Callable[[dict[str, Any]], Any]
AsyncLocalToolHandler = Callable[[dict[str, Any]], Any]  # Can be sync or async
LocalToolsMap = dict[str, LocalToolHandler]


@dataclass
class FlowStep:
    """Internal representation of a flow step."""

    id: str
    type: str
    name: str
    order: int
    enabled: bool
    config: dict[str, Any]


@dataclass
class StreamCallbacks:
    """Callbacks for streaming flow execution."""

    on_flow_start: Callable[[FlowStartEvent], None] | None = None
    on_step_start: Callable[[StepStartEvent], None] | None = None
    on_step_chunk: Callable[[str, StepChunkEvent], None] | None = None
    on_step_complete: Callable[[Any, StepCompleteEvent], None] | None = None
    on_flow_complete: Callable[[FlowCompleteEvent], None] | None = None
    on_error: Callable[[Exception], None] | None = None


@dataclass
class FlowSummary:
    """Summary returned after flow execution completes."""

    flow_id: str
    flow_name: str
    total_steps: int
    successful_steps: int
    failed_steps: int
    execution_time: int
    results: dict[str, Any] = field(default_factory=dict)
    success: bool = True


class FlowResult:
    """
    Result of a flow execution.

    Wraps the streaming response and provides methods to process events
    or extract results.
    """

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = events
        self._results: dict[str, Any] = {}
        self._summary: FlowSummary | None = None
        self._process_events()

    def _process_events(self) -> None:
        """Process events to extract results and summary."""
        for event in self._events:
            event_type = event.get("type")

            if event_type == "step_complete":
                # Handle snake_case (step_name), simple (name), and camelCase (stepName)
                step_name = event.get("step_name") or event.get("name") or event.get("stepName", "")
                # Prompt steps use "result", context steps use "output"
                result = event.get("result") or event.get("output")
                if step_name:
                    self._results[step_name] = result

            elif event_type == "flow_complete":
                self._summary = FlowSummary(
                    flow_id=event.get("flow_id") or event.get("flowId", ""),
                    flow_name=event.get("flow_name") or event.get("flowName", ""),
                    total_steps=event.get("total_steps") or event.get("totalSteps", 0),
                    successful_steps=event.get("successful_steps")
                    or event.get("successfulSteps", 0),
                    failed_steps=event.get("failed_steps") or event.get("failedSteps", 0),
                    execution_time=event.get("execution_time") or event.get("executionTime", 0),
                    results=self._results.copy(),
                    success=(event.get("failed_steps") or event.get("failedSteps", 0)) == 0,
                )

    def get_result(self, step_name: str) -> Any:
        """
        Get the result of a specific step.

        Args:
            step_name: Name of the step

        Returns:
            The step's result, or None if not found
        """
        return self._results.get(step_name)

    def get_all_results(self) -> dict[str, Any]:
        """
        Get all step results.

        Returns:
            Dictionary mapping step names to their results
        """
        return self._results.copy()

    def get_summary(self) -> FlowSummary | None:
        """
        Get the execution summary.

        Returns:
            Flow summary if execution completed, None otherwise
        """
        return self._summary

    @property
    def events(self) -> list[dict[str, Any]]:
        """Get all raw events."""
        return self._events


class FlowBuilder:
    """
    Fluent builder for constructing dispatch configurations.

    Provides a chainable API for building flows with steps.

    Example:
        ```python
        from travrse import FlowBuilder

        builder = (
            FlowBuilder()
            .create_flow(name="My Flow", description="A test flow")
            .with_record(name="Test Record", type="test", metadata={"key": "value"})
            .fetch_url(name="Fetch", url="https://api.example.com", output_variable="data")
            .prompt(name="Process", model="gpt-4o", user_prompt="Analyze: {{data}}")
            .with_options(stream_response=True, flow_mode="virtual")
        )

        # Build the configuration
        config = builder.build()

        # Or run directly with a client
        result = builder.run(client)
        ```
    """

    def __init__(self) -> None:
        self._flow_name: str = "Untitled Flow"
        self._flow_description: str | None = None
        self._steps: list[FlowStep] = []
        self._record_config: RecordConfig | None = None
        self._messages: list[Message] | None = None
        self._options: DispatchOptions = DispatchOptions()
        self._step_counter: int = 0
        self._existing_flow_id: str | None = None
        self._secrets: dict[str, str] | None = None

    def create_flow(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> FlowBuilder:
        """
        Initialize the flow with a name and optional description.

        Args:
            name: Flow name
            description: Optional flow description

        Returns:
            Self for chaining
        """
        self._flow_name = name
        self._flow_description = description
        self._existing_flow_id = None
        return self

    def upsert_flow(
        self,
        *,
        name: str,
        description: str | None = None,
        create_version_on_change: bool = True,
        allow_overwrite_external_changes: bool = False,
    ) -> FlowBuilder:
        """
        Define a flow for upsert - creates if it doesn't exist, updates if steps changed.

        This is the recommended pattern for code-first flow management.

        Args:
            name: Flow name
            description: Optional flow description
            create_version_on_change: Create version snapshot before updating
            allow_overwrite_external_changes: Allow overwriting dashboard changes

        Returns:
            Self for chaining
        """
        self._flow_name = name
        self._flow_description = description
        self._existing_flow_id = None
        self._options = DispatchOptions(
            flow_mode=FlowMode.UPSERT,
            upsert_options=UpsertOptions(
                create_version_on_change=create_version_on_change,
                allow_overwrite_external_changes=allow_overwrite_external_changes,
            ),
        )
        return self

    def use_existing_flow(self, flow_id: str) -> FlowBuilder:
        """
        Use an existing flow by ID instead of defining steps inline.

        Args:
            flow_id: ID of the existing flow

        Returns:
            Self for chaining
        """
        self._existing_flow_id = flow_id
        self._steps = []
        return self

    def with_record(
        self,
        *,
        id: str | int | None = None,
        name: str | None = None,
        type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FlowBuilder:
        """
        Set the record configuration.

        Args:
            id: Record ID (for existing records)
            name: Record name
            type: Record type
            metadata: Record metadata

        Returns:
            Self for chaining
        """
        self._record_config = RecordConfig(
            id=id,
            name=name,
            type=type,
            metadata=metadata,
        )
        return self

    def with_messages(self, messages: list[Message | dict[str, Any]]) -> FlowBuilder:
        """
        Set conversation messages.

        Args:
            messages: List of messages

        Returns:
            Self for chaining
        """
        self._messages = [Message(**m) if isinstance(m, dict) else m for m in messages]
        return self

    def with_secrets(self, secrets: dict[str, str]) -> FlowBuilder:
        """
        Set secrets for tool authentication.

        Secrets are never logged or returned in responses.
        Available as {{secrets.key_name}} in tool configurations.

        Args:
            secrets: Dictionary of secret key-value pairs

        Returns:
            Self for chaining
        """
        self._secrets = secrets
        return self

    def with_options(
        self,
        *,
        stream_response: bool | None = None,
        model_override: str | None = None,
        record_mode: RecordMode | str | None = None,
        flow_mode: FlowMode | str | None = None,
        store_results: bool | None = None,
        auto_append_metadata: bool | None = None,
        debug_mode: bool | None = None,
        create_version: bool | None = None,
        version_type: str | None = None,
        version_label: str | None = None,
        version_notes: str | None = None,
        flow_version_id: str | None = None,
    ) -> FlowBuilder:
        """
        Set dispatch options.

        Args:
            stream_response: Whether to stream the response
            model_override: Override the model for all prompt steps
            record_mode: Record handling mode
            flow_mode: Flow handling mode
            store_results: Whether to store execution results
            auto_append_metadata: Auto-append metadata to records
            debug_mode: Enable debug mode
            create_version: Create a flow version
            version_type: Type of version
            version_label: Version label
            version_notes: Version notes
            flow_version_id: Specific flow version to use

        Returns:
            Self for chaining
        """
        # Update only provided options
        if stream_response is not None:
            self._options.stream_response = stream_response
        if model_override is not None:
            self._options.model_override = model_override
        if record_mode is not None:
            self._options.record_mode = (
                record_mode.value if isinstance(record_mode, RecordMode) else record_mode
            )
        if flow_mode is not None:
            self._options.flow_mode = (
                flow_mode.value if isinstance(flow_mode, FlowMode) else flow_mode
            )
        if store_results is not None:
            self._options.store_results = store_results
        if auto_append_metadata is not None:
            self._options.auto_append_metadata = auto_append_metadata
        if debug_mode is not None:
            self._options.debug_mode = debug_mode
        if create_version is not None:
            self._options.create_version = create_version
        if version_type is not None:
            self._options.version_type = version_type
        if version_label is not None:
            self._options.version_label = version_label
        if version_notes is not None:
            self._options.version_notes = version_notes
        if flow_version_id is not None:
            self._options.flow_version_id = flow_version_id

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
    ) -> FlowBuilder:
        """
        Add a prompt step.

        Args:
            name: Step name
            model: Model to use (e.g., 'gpt-4o', 'claude-3-opus')
            user_prompt: The user prompt text
            system_prompt: Optional system prompt
            previous_messages: Variable name or list of previous messages
            output_variable: Variable to store the output
            response_format: Expected response format
            temperature: Model temperature
            max_tokens: Maximum tokens in response
            reasoning: Enable reasoning/thinking mode
            stream_output: Whether to stream this step's output
            tools: Tools configuration
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {
            "model": model,
            "user_prompt": user_prompt,
            "text": user_prompt,  # backward compat
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
        firecrawl: dict[str, Any] | None = None,
        error_handling: Literal["fail", "continue", "retry"] | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a fetch URL step.

        Args:
            name: Step name
            url: URL to fetch
            method: HTTP method
            headers: HTTP headers
            body: Request body
            output_variable: Variable to store the output
            fetch_method: Fetch method ('http' or 'firecrawl')
            firecrawl: Firecrawl-specific options
            error_handling: Error handling strategy
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {
            "http": {
                "url": url,
                "method": method,
            }
        }
        if headers is not None:
            config["http"]["headers"] = headers
        if body is not None:
            config["http"]["body"] = body
        if output_variable is not None:
            config["output_variable"] = output_variable
        if fetch_method is not None:
            config["fetch_method"] = fetch_method
        if firecrawl is not None:
            config["firecrawl"] = firecrawl
        if error_handling is not None:
            config["error_handling"] = error_handling
        if stream_output is not None:
            config["stream_output"] = stream_output

        self._add_step("fetch-url", name, config, enabled)
        return self

    def transform_data(
        self,
        *,
        name: str,
        script: str,
        output_variable: str | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a transform data step.

        Executes JavaScript code in a sandboxed environment.

        Args:
            name: Step name
            script: JavaScript code to execute
            output_variable: Variable to store the output
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {"script": script}
        if output_variable is not None:
            config["output_variable"] = output_variable
        if stream_output is not None:
            config["stream_output"] = stream_output

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
        return_citations: bool | None = None,
        error_handling: Literal["fail", "continue", "retry"] | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a search step.

        Args:
            name: Step name
            provider: Search provider (e.g., 'exa', 'google')
            query: Search query
            max_results: Maximum number of results
            output_variable: Variable to store the output
            return_citations: Include citation information
            error_handling: Error handling strategy
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {
            "provider": provider,
            "query": query,
        }
        if max_results is not None:
            config["max_results"] = max_results
        if output_variable is not None:
            config["output_variable"] = output_variable
        if return_citations is not None:
            config["return_citations"] = return_citations
        if error_handling is not None:
            config["error_handling"] = error_handling
        if stream_output is not None:
            config["stream_output"] = stream_output

        self._add_step("search", name, config, enabled)
        return self

    def retrieve_record(
        self,
        *,
        name: str,
        record_type: str | None = None,
        record_name: str | None = None,
        fields_to_include: list[str] | None = None,
        fields_to_exclude: list[str] | None = None,
        output_variable: str | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a retrieve record step.

        Args:
            name: Step name
            record_type: Type of record to retrieve
            record_name: Name of record to retrieve
            fields_to_include: Fields to include in output
            fields_to_exclude: Fields to exclude from output
            output_variable: Variable to store the output
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {}
        if record_type is not None:
            config["record_type"] = record_type
        if record_name is not None:
            config["record_name"] = record_name
        if fields_to_include is not None:
            config["fields_to_include"] = fields_to_include
        if fields_to_exclude is not None:
            config["fields_to_exclude"] = fields_to_exclude
        if output_variable is not None:
            config["output_variable"] = output_variable
        if stream_output is not None:
            config["stream_output"] = stream_output

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
        error_handling: Literal["fail", "continue", "retry"] | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add an upsert record step.

        Args:
            name: Step name
            record_type: Type of record
            record_name: Name of record
            source_variable: Variable containing data to upsert
            merge_strategy: How to merge with existing data
            output_variable: Variable to store the output
            error_handling: Error handling strategy
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {"record_type": record_type}
        if record_name is not None:
            config["record_name"] = record_name
        if source_variable is not None:
            config["source_variable"] = source_variable
        if merge_strategy is not None:
            config["merge_strategy"] = merge_strategy
        if output_variable is not None:
            config["output_variable"] = output_variable
        if error_handling is not None:
            config["error_handling"] = error_handling
        if stream_output is not None:
            config["stream_output"] = stream_output

        self._add_step("upsert-record", name, config, enabled)
        return self

    def vector_search(
        self,
        *,
        name: str,
        query: str,
        record_type: str | None = None,
        embedding_model: str | None = None,
        limit: int | None = None,
        threshold: float | None = None,
        output_variable: str | None = None,
        include_distance: bool | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a vector search step.

        Args:
            name: Step name
            query: Search query
            record_type: Type of records to search
            embedding_model: Embedding model to use
            limit: Maximum number of results
            threshold: Similarity threshold
            output_variable: Variable to store the output
            include_distance: Include distance scores
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {"query": query}
        if record_type is not None:
            config["record_type"] = record_type
        if embedding_model is not None:
            config["embedding_model"] = embedding_model
        if limit is not None:
            config["limit"] = limit
        if threshold is not None:
            config["threshold"] = threshold
        if output_variable is not None:
            config["output_variable"] = output_variable
        if include_distance is not None:
            config["include_distance"] = include_distance
        if stream_output is not None:
            config["stream_output"] = stream_output

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
        error_handling: Literal["fail", "continue", "retry"] | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a send email step.

        Args:
            name: Step name
            to: Recipient email address
            subject: Email subject
            html: Email body (HTML)
            from_address: Sender email address
            output_variable: Variable to store the output
            error_handling: Error handling strategy
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {
            "to": to,
            "subject": subject,
            "html": html,
        }
        if from_address is not None:
            config["from"] = from_address
        if output_variable is not None:
            config["output_variable"] = output_variable
        if error_handling is not None:
            config["error_handling"] = error_handling
        if stream_output is not None:
            config["stream_output"] = stream_output

        self._add_step("send-email", name, config, enabled)
        return self

    def send_stream(
        self,
        *,
        name: str,
        message: str,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a send stream step.

        Sends a message to the stream output.

        Args:
            name: Step name
            message: Message to send
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        self._add_step("send-stream", name, {"message": message}, enabled)
        return self

    def conditional(
        self,
        *,
        name: str,
        condition: str,
        true_steps: list[dict[str, Any]] | None = None,
        false_steps: list[dict[str, Any]] | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a conditional step.

        Args:
            name: Step name
            condition: JavaScript condition expression
            true_steps: Steps to execute if condition is true
            false_steps: Steps to execute if condition is false
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {
            "condition": condition,
            "true_steps": true_steps or [],
            "false_steps": false_steps or [],
        }
        self._add_step("conditional", name, config, enabled)
        return self

    def wait_until(
        self,
        *,
        name: str,
        delay_ms: int | None = None,
        continue_on_timeout: bool | None = None,
        poll: dict[str, Any] | None = None,
        output_variable: str | None = None,
        error_handling: Literal["fail", "continue", "retry"] | None = None,
        stream_output: bool | None = None,
        enabled: bool = True,
    ) -> FlowBuilder:
        """
        Add a wait until step.

        Args:
            name: Step name
            delay_ms: Delay in milliseconds
            continue_on_timeout: Continue if timeout occurs
            poll: Polling configuration
            output_variable: Variable to store the output
            error_handling: Error handling strategy
            stream_output: Whether to stream this step's output
            enabled: Whether the step is enabled

        Returns:
            Self for chaining
        """
        config: dict[str, Any] = {}
        if delay_ms is not None:
            config["delay_ms"] = delay_ms
        if continue_on_timeout is not None:
            config["continue_on_timeout"] = continue_on_timeout
        if poll is not None:
            config["poll"] = poll
        if output_variable is not None:
            config["output_variable"] = output_variable
        if error_handling is not None:
            config["error_handling"] = error_handling
        if stream_output is not None:
            config["stream_output"] = stream_output

        self._add_step("wait-until", name, config, enabled)
        return self

    # =========================================================================
    # Build and Execute Methods
    # =========================================================================

    def build(self) -> DispatchRequest:
        """
        Build the final dispatch request configuration.

        Returns:
            The dispatch request ready for execution
        """
        # Determine flow configuration
        if self._existing_flow_id:
            flow = FlowConfig(id=self._existing_flow_id)
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

        # Only include options if any are set
        options_dict = self._options.model_dump(exclude_none=True)
        if options_dict:
            request.options = self._options

        return request

    def run(
        self,
        client: TravrseClient,
        *,
        stream: bool = True,
        callbacks: StreamCallbacks | None = None,
        local_tools: LocalToolsMap | None = None,
    ) -> FlowResult | FlowSummary:
        """
        Build and execute the flow with the provided client.

        Args:
            client: Travrse client
            stream: Whether to stream the response
            callbacks: Optional callbacks for streaming events
            local_tools: Map of tool names to handler functions for local tool execution

        Returns:
            FlowResult if no callbacks, FlowSummary if callbacks provided

        Example with local tools:
            ```python
            def get_user_data(args: dict) -> dict:
                return {"name": "John", "id": args.get("user_id")}

            result = builder.run(
                client,
                local_tools={"get_user_data": get_user_data}
            )
            ```
        """
        # If local tools are provided, use the local tools execution loop
        if local_tools:
            return self._run_with_local_tools(client, local_tools, stream, callbacks)

        request = self.build()

        # Ensure streaming option is set
        if request.options is None:
            request.options = DispatchOptions(stream_response=stream)
        else:
            request.options.stream_response = stream

        # Collect events
        events: list[dict[str, Any]] = []

        for event in client.dispatch(request, stream=True):
            events.append(event)

            if callbacks:
                self._handle_event(event, callbacks)

        result = FlowResult(events)

        if callbacks:
            return result.get_summary() or FlowSummary(
                flow_id="",
                flow_name=self._flow_name,
                total_steps=len(self._steps),
                successful_steps=0,
                failed_steps=0,
                execution_time=0,
                results=result.get_all_results(),
                success=False,
            )

        return result

    def _run_with_local_tools(
        self,
        client: TravrseClient,
        local_tools: LocalToolsMap,
        stream: bool = True,
        callbacks: StreamCallbacks | None = None,
    ) -> FlowResult | FlowSummary:
        """
        Execute the flow with local tools support (pause/resume loop).

        When a flow uses local tools, the server pauses execution and returns
        a pause event. This method handles the pause/resume cycle:
        1. Execute flow until it pauses or completes
        2. If paused for a local tool, execute the tool locally
        3. Resume the flow with the tool result
        4. Repeat until flow completes

        Args:
            client: Travrse client
            local_tools: Map of tool names to handler functions
            stream: Whether to stream the response
            callbacks: Optional callbacks for streaming events

        Returns:
            FlowResult or FlowSummary
        """
        request = self.build()

        # Ensure streaming option is set
        if request.options is None:
            request.options = DispatchOptions(stream_response=stream)
        else:
            request.options.stream_response = stream

        all_events: list[dict[str, Any]] = []
        results: dict[str, Any] = {}

        # Start with initial dispatch
        event_source: Iterator[dict[str, Any]] = client.dispatch(request, stream=True)
        execution_id: str | None = None

        while True:
            paused_state: dict[str, Any] | None = None

            for event in event_source:
                all_events.append(event)
                event_type = event.get("type")

                # Capture execution_id from flow_start
                if event_type == "flow_start" and not execution_id:
                    execution_id = event.get("execution_id") or event.get("executionId")

                # Check for pause events (local tool needed)
                if event_type in ("step_waiting_local", "flow_paused", "tool_waiting_local"):
                    paused_state = {
                        "tool_name": event.get("toolName") or event.get("tool_name"),
                        "parameters": event.get("parameters", {}),
                        "execution_id": event.get("executionId")
                        or event.get("execution_id")
                        or execution_id,
                    }

                # Track step results
                if event_type == "step_complete":
                    step_name = event.get("name", "")
                    results[step_name] = event.get("result")

                # Handle callbacks
                if callbacks:
                    self._handle_event(event, callbacks)

            # If flow is paused for local tool, execute and resume
            if paused_state and paused_state.get("tool_name"):
                tool_name = paused_state["tool_name"]
                parameters = paused_state["parameters"]
                pause_execution_id = paused_state["execution_id"]

                if not pause_execution_id:
                    raise ValueError("Flow paused but no execution_id provided - cannot resume")

                if tool_name not in local_tools:
                    raise ValueError(
                        f'Local tool "{tool_name}" required but not provided in local_tools map'
                    )

                # Execute the local tool
                try:
                    tool_result = local_tools[tool_name](parameters)
                except Exception as e:
                    raise RuntimeError(f'Error executing local tool "{tool_name}": {e}') from e

                # Resume the flow with the tool result
                event_source = client.resume(
                    execution_id=pause_execution_id,
                    tool_outputs={tool_name: tool_result},
                    stream=True,
                )
                continue

            # Flow completed (no pause)
            break

        result = FlowResult(all_events)

        if callbacks:
            return result.get_summary() or FlowSummary(
                flow_id="",
                flow_name=self._flow_name,
                total_steps=len(self._steps),
                successful_steps=0,
                failed_steps=0,
                execution_time=0,
                results=results,
                success=True,
            )

        return result

    async def run_async(
        self,
        client: AsyncTravrseClient,
        *,
        stream: bool = True,
        callbacks: StreamCallbacks | None = None,
        local_tools: LocalToolsMap | None = None,
    ) -> FlowResult | FlowSummary:
        """
        Build and execute the flow asynchronously.

        Args:
            client: Async Travrse client
            stream: Whether to stream the response
            callbacks: Optional callbacks for streaming events
            local_tools: Map of tool names to handler functions for local tool execution

        Returns:
            FlowResult if no callbacks, FlowSummary if callbacks provided

        Example with local tools:
            ```python
            def get_user_data(args: dict) -> dict:
                return {"name": "John", "id": args.get("user_id")}

            result = await builder.run_async(
                client,
                local_tools={"get_user_data": get_user_data}
            )
            ```
        """
        # If local tools are provided, use the local tools execution loop
        if local_tools:
            return await self._run_async_with_local_tools(client, local_tools, stream, callbacks)

        request = self.build()

        if request.options is None:
            request.options = DispatchOptions(stream_response=stream)
        else:
            request.options.stream_response = stream

        events: list[dict[str, Any]] = []

        async for event in await client.dispatch(request, stream=True):
            events.append(event)

            if callbacks:
                self._handle_event(event, callbacks)

        result = FlowResult(events)

        if callbacks:
            return result.get_summary() or FlowSummary(
                flow_id="",
                flow_name=self._flow_name,
                total_steps=len(self._steps),
                successful_steps=0,
                failed_steps=0,
                execution_time=0,
                results=result.get_all_results(),
                success=False,
            )

        return result

    async def _run_async_with_local_tools(
        self,
        client: AsyncTravrseClient,
        local_tools: LocalToolsMap,
        stream: bool = True,
        callbacks: StreamCallbacks | None = None,
    ) -> FlowResult | FlowSummary:
        """
        Execute the flow asynchronously with local tools support (pause/resume loop).

        Args:
            client: Async Travrse client
            local_tools: Map of tool names to handler functions
            stream: Whether to stream the response
            callbacks: Optional callbacks for streaming events

        Returns:
            FlowResult or FlowSummary
        """
        import inspect

        request = self.build()

        if request.options is None:
            request.options = DispatchOptions(stream_response=stream)
        else:
            request.options.stream_response = stream

        all_events: list[dict[str, Any]] = []
        results: dict[str, Any] = {}

        # Start with initial dispatch
        event_source: AsyncIterator[dict[str, Any]] = await client.dispatch(request, stream=True)
        execution_id: str | None = None

        while True:
            paused_state: dict[str, Any] | None = None

            async for event in event_source:
                all_events.append(event)
                event_type = event.get("type")

                # Capture execution_id from flow_start
                if event_type == "flow_start" and not execution_id:
                    execution_id = event.get("execution_id") or event.get("executionId")

                # Check for pause events (local tool needed)
                if event_type in ("step_waiting_local", "flow_paused", "tool_waiting_local"):
                    paused_state = {
                        "tool_name": event.get("toolName") or event.get("tool_name"),
                        "parameters": event.get("parameters", {}),
                        "execution_id": event.get("executionId")
                        or event.get("execution_id")
                        or execution_id,
                    }

                # Track step results
                if event_type == "step_complete":
                    step_name = event.get("name", "")
                    results[step_name] = event.get("result")

                # Handle callbacks
                if callbacks:
                    self._handle_event(event, callbacks)

            # If flow is paused for local tool, execute and resume
            if paused_state and paused_state.get("tool_name"):
                tool_name = paused_state["tool_name"]
                parameters = paused_state["parameters"]
                pause_execution_id = paused_state["execution_id"]

                if not pause_execution_id:
                    raise ValueError("Flow paused but no execution_id provided - cannot resume")

                if tool_name not in local_tools:
                    raise ValueError(
                        f'Local tool "{tool_name}" required but not provided in local_tools map'
                    )

                # Execute the local tool (support both sync and async handlers)
                try:
                    handler = local_tools[tool_name]
                    tool_result = handler(parameters)
                    # If handler is async, await it
                    if inspect.iscoroutine(tool_result):
                        tool_result = await tool_result
                except Exception as e:
                    raise RuntimeError(f'Error executing local tool "{tool_name}": {e}') from e

                # Resume the flow with the tool result
                event_source = await client.resume(
                    execution_id=pause_execution_id,
                    tool_outputs={tool_name: tool_result},
                    stream=True,
                )
                continue

            # Flow completed (no pause)
            break

        result = FlowResult(all_events)

        if callbacks:
            return result.get_summary() or FlowSummary(
                flow_id="",
                flow_name=self._flow_name,
                total_steps=len(self._steps),
                successful_steps=0,
                failed_steps=0,
                execution_time=0,
                results=results,
                success=True,
            )

        return result

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

        # Clean undefined values from config
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

    def _handle_event(
        self,
        event: dict[str, Any],
        callbacks: StreamCallbacks,
    ) -> None:
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
