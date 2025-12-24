"""
Oximy SDK Types

Complete type definitions for the Oximy observability SDK.
Designed for forward compatibility with v0.2 policy features.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional, TypedDict
from enum import Enum


# =============================================================================
# TYPE ALIASES
# =============================================================================

Provider = Literal[
    "openai",
    "anthropic",
    "google",
    "mistral",
    "cohere",
    "openrouter",
    "azure",
    "bedrock",
    "groq",
    "together",
    "fireworks",
    "perplexity",
    "ollama",
    "custom",
]

EventType = Literal[
    "completion",
    "embedding",
    "image",
    "audio",
    "moderation",
    "file",
    "assistant",
    "thread",
    "tool",
    "other",
]

Framework = Literal[
    "langchain",
    "llamaindex",
    "crewai",
    "autogen",
    "semantic-kernel",
    "haystack",
    "vercel-ai",
    "custom",
]

PolicyMode = Literal["shadow", "quarantine", "enforce"]

OximyErrorCode = Literal[
    "init_failed",
    "telemetry_failed",
    "policy_fetch_failed",
    "policy_evaluation_failed",
    "invalid_config",
    "network_error",
    "timeout",
    "unknown",
]


# =============================================================================
# SDK CONFIGURATION
# =============================================================================


@dataclass
class OximyConfig:
    """Configuration options for the Oximy SDK."""

    api_key: str
    """Oximy API key for authentication. Format: ox_xxxxxxxxxxxxxxxx"""

    project_id: str
    """Project ID to associate telemetry with. Format: proj_xxxxxxxx"""

    environment: Optional[str] = None
    """Environment name (sent with every event). Example: 'production', 'staging', 'development'"""

    service: Optional[str] = None
    """Service or application name. Example: 'chat-api', 'support-bot'"""

    version: Optional[str] = None
    """Application version. Example: '1.2.3'"""

    metadata: Optional[dict[str, Any]] = None
    """Custom metadata sent with every event."""

    api_url: str = "https://api.oximy.com"
    """Oximy API base URL."""

    timeout: int = 100
    """Timeout for telemetry requests in milliseconds."""

    debug: bool = False
    """Enable debug logging to console."""

    on_policy_violation: Optional[Callable[["PolicyViolation"], None]] = None
    """Callback when a policy violation is detected. Called in all modes."""

    on_error: Optional[Callable[["OximyError"], None]] = None
    """Callback when an SDK error occurs (not provider errors)."""


class RequestContext(TypedDict, total=False):
    """Per-request context options. Passed as second argument to wrapped client methods."""

    user_id: str
    """User identifier for this request."""

    session_id: str
    """Session identifier for this request."""

    trace_id: str
    """Trace ID for distributed tracing."""

    parent_event_id: str
    """Parent event ID for nested/chained calls."""

    span_name: str
    """Span name for framework operations. Example: 'langchain.chain.run', 'agent.execute'"""

    tags: list[str]
    """Searchable tags for this request."""

    metadata: dict[str, Any]
    """Custom metadata for this request."""


# =============================================================================
# SERVER SETTINGS (Fetched from API)
# =============================================================================


@dataclass
class ProjectSettings:
    """Project settings fetched from /v1/init."""

    project_id: str
    """Project ID."""

    project_name: str
    """Project name."""

    config_version: int
    """Configuration version (incremented on any change)."""

    telemetry_enabled: bool
    """Whether telemetry is enabled."""

    policy_enabled: bool
    """Whether policies are enabled (v0.2+)."""

    policy_mode: PolicyMode
    """Policy mode (v0.2+)."""


# =============================================================================
# TELEMETRY EVENT
# =============================================================================


class EventSource(TypedDict):
    """Source information for an event."""

    sdk_version: str
    """SDK version. Example: '0.0.1'"""

    sdk_language: Literal["node", "python"]
    """SDK language."""

    provider: Provider
    """LLM provider."""

    api_type: str
    """API endpoint called. Example: 'chat.completions', 'messages', 'embeddings'"""

    event_type: EventType
    """High-level event category."""

    framework: Optional[Framework]
    """Agent framework if applicable."""

    framework_version: Optional[str]
    """Framework version."""


class RawData(TypedDict):
    """Raw request/response data (preserved as-is)."""

    request: Any
    """Exact request sent to provider."""

    response: Any
    """Exact response from provider."""


class NormalizedInput(TypedDict, total=False):
    """Normalized input summary."""

    type: Literal["messages", "text", "text_array", "thread", "file", "other"]
    """Input format type."""

    message_count: int
    """Number of messages (for message-based APIs)."""

    content_length: int
    """Total character length of input content."""

    roles: list[str]
    """Message roles present."""

    has_system: bool
    """Has system message/instruction."""

    has_images: bool
    """Has image content."""

    has_audio: bool
    """Has audio content."""

    has_files: bool
    """Has file attachments."""

    item_count: int
    """Number of items (for array inputs like embeddings)."""


class NormalizedOutput(TypedDict, total=False):
    """Normalized output summary."""

    type: Literal[
        "message",
        "messages",
        "embedding",
        "embeddings",
        "image_url",
        "image_b64",
        "audio",
        "tool_calls",
        "moderation",
        "file",
        "other",
    ]
    """Output format type."""

    content_length: int
    """Total character length of output content."""

    choice_count: int
    """Number of choices/results."""

    finish_reason: str
    """Finish reason from provider."""

    embedding_dimensions: int
    """For embeddings: dimensions per vector."""

    image_count: int
    """For images: number generated."""

    audio_duration_seconds: float
    """For audio: duration in seconds."""


class NormalizedToolsAvailable(TypedDict):
    """Tools available in request."""

    count: int
    names: list[str]


class NormalizedToolsCalled(TypedDict, total=False):
    """Tools called in response."""

    count: int
    calls: list[dict[str, Any]]


class NormalizedTools(TypedDict, total=False):
    """Tool usage information."""

    available: NormalizedToolsAvailable
    """Tools available in request."""

    called: NormalizedToolsCalled
    """Tools called in response."""

    results: dict[str, int]
    """Tool results provided in request."""


class NormalizedMcp(TypedDict, total=False):
    """MCP (Model Context Protocol) information."""

    servers: list[str]
    """MCP servers involved."""

    resources: list[str]
    """Resources accessed."""

    prompts: list[str]
    """Prompts used."""


class NormalizedUsage(TypedDict, total=False):
    """Token usage information."""

    input_tokens: int
    """Input/prompt tokens."""

    output_tokens: int
    """Output/completion tokens."""

    total_tokens: int
    """Total tokens."""

    cached_tokens: int
    """Cached tokens (prompt caching)."""

    reasoning_tokens: int
    """Reasoning tokens (o1 models)."""


class NormalizedData(TypedDict, total=False):
    """Normalized data extracted from raw request/response."""

    model: dict[str, str]
    """Model information. Keys: 'requested', 'used'"""

    input: NormalizedInput
    """Input summary."""

    output: NormalizedOutput
    """Output summary."""

    tools: NormalizedTools
    """Tool usage."""

    mcp: NormalizedMcp
    """MCP information."""

    usage: NormalizedUsage
    """Token usage."""


class EventTiming(TypedDict):
    """Timing information."""

    started_at: str
    """Request start time (ISO8601)."""

    ended_at: str
    """Request end time (ISO8601)."""

    duration_ms: int
    """Total duration in milliseconds."""

    ttft_ms: Optional[int]
    """Time to first token for streaming (milliseconds)."""

    ttfb_ms: Optional[int]
    """Time to first byte (milliseconds)."""


class EventOutcome(TypedDict, total=False):
    """Request outcome."""

    success: bool
    """Whether the request succeeded."""

    finish_reason: str
    """Finish reason from provider."""

    error: dict[str, Any]
    """Error details if failed. Keys: 'type', 'message', 'code', 'statusCode'"""


class EventContext(TypedDict, total=False):
    """Event context (user-provided)."""

    user_id: str
    """User identifier."""

    session_id: str
    """Session identifier."""

    trace_id: str
    """Trace ID for distributed tracing."""

    parent_event_id: str
    """Parent event ID (for nested/chained calls)."""

    span_name: str
    """Span name for framework operations."""

    tags: list[str]
    """Searchable tags."""

    metadata: dict[str, Any]
    """Custom metadata."""


class StreamingInfo(TypedDict, total=False):
    """Streaming information."""

    enabled: bool
    """Whether this was a streaming request."""

    chunk_count: int
    """Number of chunks received."""

    completed: bool
    """Whether stream completed normally."""

    interrupted_reason: str
    """If interrupted, reason. Values: 'client_cancel', 'timeout', 'error'"""


class PolicyResult(TypedDict, total=False):
    """Policy evaluation result."""

    version: int
    """Policy version evaluated against."""

    mode: PolicyMode
    """Policy mode at time of evaluation."""

    violations: list["PolicyViolation"]
    """Rules that were triggered."""


class OximyEvent(TypedDict, total=False):
    """Complete telemetry event."""

    id: str
    """Unique event ID. Format: evt_xxxxxxxxxxxxxxxxxxxxxx"""

    timestamp: str
    """ISO8601 timestamp when event was created."""

    source: EventSource
    """Source information."""

    raw: RawData
    """Raw request/response data."""

    normalized: NormalizedData
    """Normalized data."""

    timing: EventTiming
    """Timing information."""

    outcome: EventOutcome
    """Request outcome."""

    context: EventContext
    """User-provided context."""

    streaming: StreamingInfo
    """Streaming information."""

    policy: PolicyResult
    """Policy evaluation results (v0.2+)."""


# =============================================================================
# POLICY TYPES (v0.2+)
# =============================================================================

PolicySeverity = Literal["low", "medium", "high", "critical"]
"""Policy severity levels."""

PiiCategory = Literal["ssn", "credit_card", "phone", "email", "address", "name"]
"""PII categories for AI model detection."""


@dataclass
class PolicyDetection:
    """Detection details from AI-powered evaluation."""

    type: str
    """Type of detected content (e.g., 'ssn', 'credit_card', 'email')."""

    value: str
    """The detected value."""

    start: int
    """Start index in the content."""

    end: int
    """End index in the content."""

    confidence: float
    """Confidence score (0-1)."""


@dataclass
class PolicyViolation:
    """Policy violation details."""

    rule_id: str
    """Rule ID that was violated."""

    rule_name: str
    """Rule name."""

    action: Literal["block", "redact", "alert", "allow", "transform"]
    """Action taken."""

    severity: PolicySeverity
    """Violation severity."""

    matched: Optional[str] = None
    """What matched (for debugging)."""

    message: Optional[str] = None
    """Human-readable message."""

    detections: Optional[list[PolicyDetection]] = None
    """Detection details from SLM evaluation."""


@dataclass
class OximyError:
    """Oximy SDK error."""

    code: OximyErrorCode
    """Error code."""

    message: str
    """Human-readable message."""

    details: Optional[dict[str, Any]] = None
    """Additional details."""


class BlockActionOptions(TypedDict, total=False):
    """Options for block action."""

    include_rule_id: bool
    log_full_content: bool


class RedactActionOptions(TypedDict, total=False):
    """Options for redact action."""

    preserve_format: bool
    session_persistence: bool
    mask_pattern: str
    mask_char: str


class AlertActionOptions(TypedDict, total=False):
    """Options for alert action."""

    channels: list[str]
    priority: PolicySeverity


class PolicyActionBlock(TypedDict, total=False):
    """Block action."""

    type: Literal["block"]
    message: str
    options: BlockActionOptions


class PolicyActionRedact(TypedDict, total=False):
    """Redact action."""

    type: Literal["redact"]
    method: Literal["simple", "pseudoanonymize", "mask"]
    replacement: str
    options: RedactActionOptions


class PolicyActionAlert(TypedDict, total=False):
    """Alert action."""

    type: Literal["alert"]
    options: AlertActionOptions


class PolicyActionTransform(TypedDict):
    """Transform action."""

    type: Literal["transform"]
    template: str


class PolicyActionAllow(TypedDict):
    """Allow action."""

    type: Literal["allow"]


PolicyAction = (
    PolicyActionBlock
    | PolicyActionRedact
    | PolicyActionAlert
    | PolicyActionTransform
    | PolicyActionAllow
)


class RegexOptions(TypedDict, total=False):
    """Options for regex matching."""

    multiline: bool
    dot_all: bool


class AiModelOptions(TypedDict, total=False):
    """Options for AI model-based detection."""

    strict_mode: bool
    context_aware: bool
    confidence_boost: float


class AiCustomOptions(TypedDict, total=False):
    """Options for custom AI detection."""

    max_tokens: int
    temperature: float


class PolicyMatchRegex(TypedDict, total=False):
    """Regex match condition."""

    type: Literal["regex"]
    pattern: str
    flags: str
    options: RegexOptions


class PolicyMatchDenyList(TypedDict, total=False):
    """Deny list match condition."""

    type: Literal["deny_list"]
    values: list[str]
    case_sensitive: bool


class PolicyMatchAllowList(TypedDict, total=False):
    """Allow list match condition."""

    type: Literal["allow_list"]
    values: list[str]
    case_sensitive: bool


class PolicyMatchContains(TypedDict, total=False):
    """Contains match condition."""

    type: Literal["contains"]
    values: list[str]
    case_sensitive: bool


class PolicyMatchTokenLimit(TypedDict):
    """Token limit match condition."""

    type: Literal["token_limit"]
    max_tokens: int


class PolicyMatchRateLimit(TypedDict, total=False):
    """Rate limit match condition."""

    type: Literal["rate_limit"]
    limit: int
    window: str
    key: str


class PolicyMatchCostLimit(TypedDict, total=False):
    """Cost limit match condition."""

    type: Literal["cost_limit"]
    max_cost_usd: float
    window: str
    key: str


class PolicyMatchAiModel(TypedDict, total=False):
    """AI model match condition."""

    type: Literal["ai_model"]
    model: str
    threshold: float
    categories: list[PiiCategory]
    options: AiModelOptions


class PolicyMatchAiCustom(TypedDict, total=False):
    """Custom AI match condition."""

    type: Literal["ai_custom"]
    prompt: str
    threshold: float
    options: AiCustomOptions


PolicyMatch = (
    PolicyMatchRegex
    | PolicyMatchDenyList
    | PolicyMatchAllowList
    | PolicyMatchContains
    | PolicyMatchTokenLimit
    | PolicyMatchRateLimit
    | PolicyMatchCostLimit
    | PolicyMatchAiModel
    | PolicyMatchAiCustom
)


class PolicyTarget(TypedDict):
    """Policy target - what content the rule evaluates."""

    scope: Literal["input", "output", "tool_call", "tool_result", "mcp"]
    path: str


class PolicyRuleSource(TypedDict, total=False):
    """Policy rule source - provenance tracking."""

    type: Literal["insight", "manual", "template"]
    insight_id: str
    insight_type: str
    generated_at: str


@dataclass
class PolicyRule:
    """Policy rule definition."""

    id: str
    enabled: bool
    name: str
    description: Optional[str] = None
    tier: Literal["local", "slm"] = "local"
    target: dict[str, Any] = field(default_factory=dict)
    match: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    severity: PolicySeverity = "medium"
    source: Optional[dict[str, Any]] = None


@dataclass
class PolicyConfig:
    """Policy configuration."""

    version: int
    mode: PolicyMode
    rules: list[PolicyRule]


# =============================================================================
# API RESPONSE TYPES
# =============================================================================


class InitResponse(TypedDict, total=False):
    """Response from /v1/init."""

    project_id: str
    project_name: str
    config_version: int
    settings: dict[str, Any]
    policy: Optional[dict[str, Any]]


class EventResponse(TypedDict):
    """Response from POST /v1/events."""

    received: bool
    event_id: str
    config_version: int


# =============================================================================
# INTERNAL TYPES
# =============================================================================


@dataclass
class OximyState:
    """Internal SDK state."""

    config: OximyConfig
    """SDK configuration."""

    settings: Optional[ProjectSettings] = None
    """Project settings from server."""

    initialized: bool = False
    """Whether SDK is initialized."""

    policy: Optional[PolicyConfig] = None
    """Policy configuration (v0.2+)."""


# Exception class for policy errors
class OximyPolicyError(Exception):
    """Policy error thrown when a request is blocked."""

    def __init__(self, violation: PolicyViolation):
        self.code = "policy_blocked"
        self.violation = violation
        message = violation.message or f"Request blocked by policy: {violation.rule_name}"
        super().__init__(message)
