"""
Travrse SDK types and models.

All models use Pydantic v2 for validation and serialization.
API uses snake_case, Python SDK uses snake_case to match.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

# =============================================================================
# Enums
# =============================================================================


class FlowStatus(str, Enum):
    """Status of a flow."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class ResponseFormat(str, Enum):
    """Response format for prompts."""

    DEFAULT = "default"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    XML = "xml"
    TEXT = "text"


class ToolType(str, Enum):
    """Type of tool."""

    FLOW = "flow"
    CUSTOM = "custom"
    EXTERNAL = "external"
    BUILTIN = "builtin"  # Built-in model tools (e.g., DALL-E, web search)
    MCP = "mcp"  # Model Context Protocol tools
    LOCAL = "local"  # Local tools executed by SDK (pause/resume pattern)


class ToolExecutionStatus(str, Enum):
    """Tool execution status."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING_FOR_LOCAL = "waiting_for_local"


class ExecutionStatus(str, Enum):
    """Flow execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class RecordMode(str, Enum):
    """Record mode for dispatch."""

    EXISTING = "existing"
    CREATE = "create"
    VIRTUAL = "virtual"


class FlowMode(str, Enum):
    """Flow mode for dispatch."""

    EXISTING = "existing"
    CREATE = "create"
    VIRTUAL = "virtual"
    UPSERT = "upsert"


class VersionType(str, Enum):
    """Version type for flow versions."""

    PUBLISHED = "published"
    DRAFT = "draft"
    TEST = "test"
    VIRTUAL = "virtual"


class ErrorHandling(str, Enum):
    """Error handling strategy for steps."""

    FAIL = "fail"
    CONTINUE = "continue"
    RETRY = "retry"


class FetchMethod(str, Enum):
    """HTTP fetch method."""

    HTTP = "http"
    FIRECRAWL = "firecrawl"


# =============================================================================
# Base Models
# =============================================================================


class TravrseModel(BaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra="allow",
    )


# =============================================================================
# Resource Models
# =============================================================================


class Flow(TravrseModel):
    """Flow resource model."""

    id: str
    name: str
    description: str | None = None
    status: FlowStatus = FlowStatus.DRAFT
    user_id: str | None = None
    organization_id: str | None = None
    created_at: datetime | str
    updated_at: datetime | str
    last_run_at: datetime | str | None = None


class Prompt(TravrseModel):
    """Prompt resource model."""

    id: str
    name: str
    text: str
    response_format: ResponseFormat = ResponseFormat.DEFAULT
    model: str
    is_streamed: bool = False
    tools: list[str] = Field(default_factory=list)
    input_variables: str | None = None
    estimated_tokens: int | None = None
    estimated_cost: str | None = None
    user_id: str | None = None
    created_at: datetime | str
    updated_at: datetime | str


class Record(TravrseModel):
    """Record resource model."""

    id: str
    type: str
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    metadata_schema: dict[str, Any] | None = None
    available_fields: list[str] | None = None
    user_id: str | None = None
    created_at: datetime | str
    updated_at: datetime | str


class ApiKey(TravrseModel):
    """API key resource model."""

    id: str
    name: str
    key_prefix: str
    search_hint: str | None = None
    permissions: list[str] = Field(default_factory=list)
    is_active: bool = True
    expires_at: datetime | str | None = None
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    allowed_ips: list[str] = Field(default_factory=list)
    created_at: datetime | str
    updated_at: datetime | str | None = None
    usage_count: int | None = None
    last_used_at: datetime | str | None = None


class ModelConfig(TravrseModel):
    """Model configuration resource."""

    id: str
    provider: str
    model_id: str
    display_name: str | None = None
    requires_api_key: bool = True
    cost_per_1k_tokens: float | None = None
    max_tokens: int | None = None
    supports_streaming: bool | None = None
    supported_response_formats: list[str] | None = None
    supports_search: bool | None = None
    is_enabled: bool = True
    is_default: bool = False
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | str
    updated_at: datetime | str


class Tool(TravrseModel):
    """Tool resource model."""

    id: str
    user_id: str
    organization_id: str | None = None
    name: str
    description: str
    tool_type: ToolType
    parameters_schema: dict[str, Any]
    config: dict[str, Any]
    is_active: bool = True
    created_at: datetime | str
    updated_at: datetime | str


# =============================================================================
# Request Models
# =============================================================================


class CreateFlowRequest(TravrseModel):
    """Request to create a flow."""

    name: str
    description: str | None = None


class CreatePromptRequest(TravrseModel):
    """Request to create a prompt."""

    name: str
    text: str
    response_format: ResponseFormat | str = ResponseFormat.TEXT
    model: str | None = None
    input_variables: str | None = None
    flow_ids: list[str] | None = None


class CreateRecordRequest(TravrseModel):
    """Request to create a record."""

    type: str
    name: str
    metadata: dict[str, Any] | None = None


class CreateApiKeyRequest(TravrseModel):
    """Request to create an API key."""

    name: str
    permissions: list[str] | None = None
    expires_at: str | None = None
    rate_limit_per_hour: int | None = None
    rate_limit_per_day: int | None = None
    allowed_ips: list[str] | None = None


class UpsertOptions(TravrseModel):
    """Options for upsert mode."""

    create_version_on_change: bool = True
    allow_overwrite_external_changes: bool = False


class DispatchOptions(TravrseModel):
    """Options for dispatch requests."""

    stream_response: bool = True
    model_override: str | None = None
    record_mode: RecordMode | str | None = None
    flow_mode: FlowMode | str | None = None
    store_results: bool | None = None
    auto_append_metadata: bool | None = None
    debug_mode: bool | None = None
    create_version: bool | None = None
    version_type: VersionType | str | None = None
    version_label: str | None = None
    version_notes: str | None = None
    flow_version_id: str | None = None
    upsert_options: UpsertOptions | None = None


class RecordConfig(TravrseModel):
    """Record configuration for dispatch."""

    id: str | int | None = None
    name: str | None = None
    type: str | None = None
    metadata: dict[str, Any] | None = None


class FlowConfig(TravrseModel):
    """Flow configuration for dispatch."""

    id: str | None = None
    name: str | None = None
    steps: list[dict[str, Any]] | None = None


class Message(TravrseModel):
    """Chat message."""

    role: Literal["system", "user", "assistant"]
    content: str | list[dict[str, Any]]


class DispatchRequest(TravrseModel):
    """Full dispatch request."""

    flow: FlowConfig
    record: RecordConfig | None = None
    messages: list[Message] | None = None
    secrets: dict[str, str] | None = None
    options: DispatchOptions | None = None


# =============================================================================
# Response Models
# =============================================================================


class PaginationInfo(TravrseModel):
    """Pagination information."""

    next_cursor: str | None = None
    prev_cursor: str | None = None
    has_more: bool = False
    has_prev: bool = False
    limit: int = 20
    current_offset: int = 0
    total_pages: int | None = None
    current_page: int | None = None
    total_count: int | None = None


class PaginatedResponse(TravrseModel):
    """Generic paginated response."""

    data: list[Any]
    pagination: PaginationInfo


class ApiResponse(TravrseModel):
    """Generic API response."""

    data: Any | None = None
    success: bool = True
    error: str | None = None
    message: str | None = None


# =============================================================================
# Local Tool / Pause-Resume Models
# =============================================================================


class PausedReason(TravrseModel):
    """Reason for flow pause (local tool execution)."""

    type: Literal["local_action"] = "local_action"
    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    execution_id: str


class DispatchResponse(TravrseModel):
    """Response from dispatch endpoint (non-streaming)."""

    success: bool = True
    status: ExecutionStatus | str | None = None
    paused_reason: PausedReason | None = None
    execution_id: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class ResumeRequest(TravrseModel):
    """Request to resume a paused flow execution."""

    execution_id: str
    tool_result: Any


# =============================================================================
# Streaming Event Models
# =============================================================================


class FlowStartEvent(TravrseModel):
    """Event when flow execution starts."""

    type: Literal["flow_start"] = "flow_start"
    flow_id: str | None = Field(default=None, validation_alias=AliasChoices("flow_id", "flowId"))
    flow_name: str | None = Field(
        default=None, validation_alias=AliasChoices("flow_name", "flowName")
    )
    total_steps: int = Field(default=0, validation_alias=AliasChoices("total_steps", "totalSteps"))


class StepStartEvent(TravrseModel):
    """Event when a step starts executing."""

    type: Literal["step_start"] = "step_start"
    id: str | None = None
    name: str | None = Field(
        default=None, validation_alias=AliasChoices("step_name", "name", "stepName")
    )
    index: int = 0
    execution_type: str | None = Field(
        default=None, validation_alias=AliasChoices("execution_type", "executionType")
    )


class StepChunkEvent(TravrseModel):
    """Event for streaming output chunk."""

    type: Literal["step_chunk"] = "step_chunk"
    id: str | None = None
    name: str | None = None
    execution_type: str | None = Field(
        default=None, validation_alias=AliasChoices("execution_type", "executionType")
    )
    chunk: str = Field(default="", validation_alias=AliasChoices("chunk", "text"))
    index: int = 0


class StepCompleteEvent(TravrseModel):
    """Event when a step completes."""

    type: Literal["step_complete"] = "step_complete"
    id: str | None = None
    name: str | None = Field(
        default=None, validation_alias=AliasChoices("step_name", "name", "stepName")
    )
    index: int = 0
    execution_type: str | None = Field(
        default=None, validation_alias=AliasChoices("execution_type", "executionType")
    )
    result: Any = None
    execution_time: int = Field(
        default=0, validation_alias=AliasChoices("execution_time", "executionTime")
    )


class FlowCompleteEvent(TravrseModel):
    """Event when flow execution completes."""

    type: Literal["flow_complete"] = "flow_complete"
    flow_id: str | None = Field(default=None, validation_alias=AliasChoices("flow_id", "flowId"))
    total_steps: int = Field(default=0, validation_alias=AliasChoices("total_steps", "totalSteps"))
    successful_steps: int = Field(
        default=0, validation_alias=AliasChoices("successful_steps", "successfulSteps")
    )
    failed_steps: int = Field(
        default=0, validation_alias=AliasChoices("failed_steps", "failedSteps")
    )
    execution_time: int = Field(
        default=0, validation_alias=AliasChoices("execution_time", "executionTime")
    )


class FlowErrorEvent(TravrseModel):
    """Event when an error occurs."""

    type: Literal["flow_error"] = "flow_error"
    error: str = ""
    step_id: str | None = Field(default=None, validation_alias=AliasChoices("step_id", "stepId"))


StreamEvent = Union[
    FlowStartEvent,
    StepStartEvent,
    StepChunkEvent,
    StepCompleteEvent,
    FlowCompleteEvent,
    FlowErrorEvent,
]


# =============================================================================
# List Parameters
# =============================================================================


class ListParams(TravrseModel):
    """Parameters for list operations."""

    limit: int | None = None
    cursor: str | None = None
    direction: Literal["next", "prev"] | None = None


class RecordListParams(ListParams):
    """Parameters for listing records."""

    metadata_keys: str | None = None
    metadata_keys_all: str | None = None
    min_fields: int | None = None
    max_fields: int | None = None
    metadata_types: str | None = None
    has_large_fields: bool | None = None
    min_size_kb: int | None = None
    max_size_kb: int | None = None
    sort_by: str | None = None
    sort_order: Literal["asc", "desc"] | None = None
    include_fields: bool | None = None


# =============================================================================
# Step Configuration Types
# =============================================================================


class PromptStepConfig(TravrseModel):
    """Configuration for a prompt step."""

    name: str
    model: str
    user_prompt: str
    system_prompt: str | None = None
    previous_messages: str | list[dict[str, str]] | None = None
    output_variable: str | None = None
    response_format: Literal["text", "json"] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    reasoning: bool | None = None
    stream_output: bool | None = None
    tools: dict[str, Any] | None = None
    enabled: bool = True


class FetchUrlStepConfig(TravrseModel):
    """Configuration for a fetch URL step."""

    name: str
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    headers: dict[str, str] | None = None
    body: str | None = None
    output_variable: str | None = None
    fetch_method: FetchMethod | str | None = None
    firecrawl: dict[str, Any] | None = None
    error_handling: ErrorHandling | str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class TransformDataStepConfig(TravrseModel):
    """Configuration for a transform data step."""

    name: str
    script: str
    output_variable: str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class SearchStepConfig(TravrseModel):
    """Configuration for a search step."""

    name: str
    provider: str
    query: str
    max_results: int | None = None
    output_variable: str | None = None
    return_citations: bool | None = None
    error_handling: ErrorHandling | str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class RetrieveRecordStepConfig(TravrseModel):
    """Configuration for a retrieve record step."""

    name: str
    record_type: str | None = None
    record_name: str | None = None
    fields_to_include: list[str] | None = None
    fields_to_exclude: list[str] | None = None
    output_variable: str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class UpsertRecordStepConfig(TravrseModel):
    """Configuration for an upsert record step."""

    name: str
    record_type: str
    record_name: str | None = None
    source_variable: str | None = None
    merge_strategy: Literal["merge", "replace"] | None = None
    output_variable: str | None = None
    error_handling: ErrorHandling | str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class VectorSearchStepConfig(TravrseModel):
    """Configuration for a vector search step."""

    name: str
    query: str
    record_type: str | None = None
    embedding_model: str | None = None
    limit: int | None = None
    threshold: float | None = None
    output_variable: str | None = None
    include_distance: bool | None = None
    stream_output: bool | None = None
    enabled: bool = True


class GenerateEmbeddingStepConfig(TravrseModel):
    """Configuration for a generate embedding step."""

    name: str
    text: str
    embedding_model: str | None = None
    max_length: int | None = None
    output_variable: str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class SendEmailStepConfig(TravrseModel):
    """Configuration for a send email step."""

    name: str
    to: str
    subject: str
    html: str
    from_: str | None = Field(None, alias="from")
    output_variable: str | None = None
    error_handling: ErrorHandling | str | None = None
    stream_output: bool | None = None
    enabled: bool = True


class SendStreamStepConfig(TravrseModel):
    """Configuration for a send stream step."""

    name: str
    message: str
    enabled: bool = True


class ConditionalStepConfig(TravrseModel):
    """Configuration for a conditional step."""

    name: str
    condition: str
    true_steps: list[dict[str, Any]] | None = None
    false_steps: list[dict[str, Any]] | None = None
    enabled: bool = True


class WaitUntilStepConfig(TravrseModel):
    """Configuration for a wait until step."""

    name: str
    delay_ms: int | None = None
    continue_on_timeout: bool | None = None
    poll: dict[str, Any] | None = None
    output_variable: str | None = None
    error_handling: ErrorHandling | str | None = None
    stream_output: bool | None = None
    enabled: bool = True


# =============================================================================
# Runtime Tool Types
# =============================================================================


class RuntimeTool(TravrseModel):
    """Runtime tool definition for inline tool definitions."""

    name: str
    description: str
    tool_type: ToolType
    parameters_schema: dict[str, Any]
    config: dict[str, Any]


class ToolsConfig(TravrseModel):
    """Tools configuration for prompt steps."""

    tool_ids: list[str] | None = None
    runtime_tools: list[RuntimeTool] | None = None
    max_tool_calls: int | None = None
    tool_call_strategy: Literal["auto", "required", "none"] | None = None
    parallel_calls: bool | None = None
    tool_configs: dict[str, dict[str, Any]] | None = None
