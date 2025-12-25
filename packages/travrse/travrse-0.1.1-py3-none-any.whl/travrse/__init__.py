"""
Travrse Python SDK.

A Python SDK for the Travrse AI product platform.

Example (Legacy - Instance-based):
    ```python
    from travrse import TravrseClient, FlowBuilder

    # Initialize client
    client = TravrseClient(api_key="your-api-key")

    # Build and execute a flow
    result = (
        FlowBuilder()
        .create_flow(name="My Flow")
        .prompt(
            name="Analyze",
            model="gpt-4o",
            user_prompt="Analyze the following: {{input}}"
        )
        .run(client)
    )
    ```

Example (Modern - Runtype Static API):
    ```python
    from travrse import Runtype

    # Global configuration (once per app)
    Runtype.configure(api_key="your-api-key")

    # Build and stream a flow
    result = await Runtype.flows.upsert(name="My Flow")
        .prompt(name="Analyze", model="gpt-4o", user_prompt="...")
        .stream()

    # Use existing flow
    result = await Runtype.flows.use("flow_123")
        .with_record(name="Test")
        .result()

    # Schedule a batch
    batch = await Runtype.batches.schedule(
        flow_id="flow_123",
        record_type="customers",
    )
    ```

Local Tools Example:
    ```python
    from travrse import Runtype

    Runtype.configure(api_key="your-api-key")

    def get_user_data(args: dict) -> dict:
        return {"name": "John", "id": args.get("user_id")}

    result = await Runtype.flows.upsert(name="My Flow")
        .prompt(name="Process", model="gpt-4o", user_prompt="Get user data")
        .with_local_tools({"get_user_data": get_user_data})
        .stream()
    ```
"""

from .client import AsyncTravrseClient, TravrseClient
from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    StreamError,
    TimeoutError,
    TravrseError,
    ValidationError,
)
from .flow_builder import (
    FlowBuilder,
    FlowResult,
    FlowSummary,
    LocalToolHandler,
    LocalToolsMap,
    StreamCallbacks,
)
from .runtype import (
    BatchesNamespace,
    EvalBuilder,
    EvalsNamespace,
    FlowsNamespace,
    PromptBuilder,
    PromptsNamespace,
    Runtype,
    RuntypeConfig,
    RuntypeFlowBuilder,
)
from .types import (
    ApiKey,
    ApiResponse,
    CreateApiKeyRequest,
    CreateFlowRequest,
    CreatePromptRequest,
    CreateRecordRequest,
    DispatchOptions,
    DispatchRequest,
    DispatchResponse,
    ErrorHandling,
    ExecutionStatus,
    FetchMethod,
    Flow,
    FlowCompleteEvent,
    FlowConfig,
    FlowErrorEvent,
    FlowMode,
    FlowStartEvent,
    FlowStatus,
    GenerateEmbeddingStepConfig,
    ListParams,
    Message,
    ModelConfig,
    PaginatedResponse,
    PaginationInfo,
    PausedReason,
    Prompt,
    PromptStepConfig,
    Record,
    RecordConfig,
    RecordListParams,
    RecordMode,
    ResponseFormat,
    ResumeRequest,
    RuntimeTool,
    SearchStepConfig,
    SendEmailStepConfig,
    StepChunkEvent,
    StepCompleteEvent,
    StepStartEvent,
    StreamEvent,
    Tool,
    ToolExecutionStatus,
    ToolsConfig,
    ToolType,
    TransformDataStepConfig,
    UpsertOptions,
    UpsertRecordStepConfig,
    VectorSearchStepConfig,
    VersionType,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Clients
    "TravrseClient",
    "AsyncTravrseClient",
    # Runtype (Modern API)
    "Runtype",
    "RuntypeConfig",
    "RuntypeFlowBuilder",
    "FlowsNamespace",
    "BatchesNamespace",
    "EvalsNamespace",
    "PromptsNamespace",
    "EvalBuilder",
    "PromptBuilder",
    # Flow Builder (Legacy API)
    "FlowBuilder",
    "FlowResult",
    "FlowSummary",
    "StreamCallbacks",
    "LocalToolHandler",
    "LocalToolsMap",
    # Exceptions
    "TravrseError",
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "StreamError",
    "TimeoutError",
    "ConnectionError",
    # Core Types
    "Flow",
    "Prompt",
    "Record",
    "ApiKey",
    "ModelConfig",
    "Tool",
    # Request Types
    "CreateFlowRequest",
    "CreatePromptRequest",
    "CreateRecordRequest",
    "CreateApiKeyRequest",
    "DispatchRequest",
    "DispatchResponse",
    "DispatchOptions",
    "FlowConfig",
    "RecordConfig",
    "Message",
    "UpsertOptions",
    "ResumeRequest",
    "PausedReason",
    # Response Types
    "ApiResponse",
    "PaginatedResponse",
    "PaginationInfo",
    # List Parameters
    "ListParams",
    "RecordListParams",
    # Enums
    "FlowStatus",
    "FlowMode",
    "RecordMode",
    "ResponseFormat",
    "ToolType",
    "ToolExecutionStatus",
    "ExecutionStatus",
    "VersionType",
    "ErrorHandling",
    "FetchMethod",
    # Step Configurations
    "PromptStepConfig",
    "TransformDataStepConfig",
    "SearchStepConfig",
    "VectorSearchStepConfig",
    "GenerateEmbeddingStepConfig",
    "UpsertRecordStepConfig",
    "SendEmailStepConfig",
    # Streaming Events
    "StreamEvent",
    "FlowStartEvent",
    "StepStartEvent",
    "StepChunkEvent",
    "StepCompleteEvent",
    "FlowCompleteEvent",
    "FlowErrorEvent",
    # Tools
    "ToolsConfig",
    "RuntimeTool",
]
