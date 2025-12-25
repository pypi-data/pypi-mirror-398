"""Pydantic models for discovery output schema.

This module defines the stable observation layer - the contract that downstream
phases (learn, generate, eval) depend on. Changes here should be versioned carefully.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# =============================================================================
# ENUMS - Stable vocabulary for observations
# =============================================================================


class SourceType(str, Enum):
    """Where an input value comes from."""

    INLINE = "inline"  # Hardcoded string literal
    VARIABLE = "variable"  # From a variable (trace to assignment)
    CONFIG = "config"  # From config/env (process.env, os.environ)
    DATABASE = "database"  # From database query
    API = "api"  # From external API call
    FILE = "file"  # From file system
    USER_INPUT = "user_input"  # From request/user at runtime
    TEMPLATE = "template"  # From template engine
    UNKNOWN = "unknown"  # Could not determine


class Provider(str, Enum):
    """AI provider/SDK."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    BEDROCK = "bedrock"
    MISTRAL = "mistral"
    OPENROUTER = "openrouter"
    UNKNOWN = "unknown"


class CallType(str, Enum):
    """Type of AI API call."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    UNKNOWN = "unknown"


class ValidationType(str, Enum):
    """Type of output validation."""

    ZOD = "zod"
    PYDANTIC = "pydantic"
    JSONSCHEMA = "jsonschema"
    MANUAL = "manual"
    NONE = "none"


class ConditionalType(str, Enum):
    """Type of conditional statement."""

    IF = "if"
    SWITCH = "switch"
    MATCH = "match"
    TERNARY = "ternary"


class SinkType(str, Enum):
    """Where the model output flows to."""

    HTTP_RESPONSE = "http_response"  # Returned in API response
    DB_WRITE = "db_write"  # Saved to database
    EMAIL_SEND = "email_send"  # Sent in email
    VENDOR_DISPATCH = "vendor_dispatch"  # Triggers external API/service
    ROUTING_BRANCH = "routing_branch"  # Controls code flow/logic
    ERROR_LOG = "error_log"  # Logged as error/warning
    USER_DISPLAY = "user_display"  # Shown directly to user
    UNKNOWN = "unknown"


class RiskTier(str, Enum):
    """Risk tier for interpretation layer."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScenarioComplexity(str, Enum):
    """Complexity of scenario testing needed."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DetectionMethod(str, Enum):
    """How the AI call was detected."""

    SDK_VERIFIED = "sdk_verified"  # Found via OpenAI/Anthropic SDKs
    HEURISTIC = "heuristic"  # Found via AI footprint signatures


# =============================================================================
# STABLE OBSERVATION MODELS
# =============================================================================


class Location(BaseModel):
    """Source code location."""

    file: str = Field(..., description="File path relative to repo root")
    line: int = Field(..., description="Line number (1-indexed)")
    column: Optional[int] = Field(None, description="Column number (0-indexed)")
    function: Optional[str] = Field(None, description="Containing function name")
    class_name: Optional[str] = Field(None, description="Containing class name")


class InputSource(BaseModel):
    """Describes where an input value comes from."""

    source_type: SourceType = Field(..., description="Category of input source")
    source_hint: Optional[str] = Field(
        None, description="Code pattern that reveals source, e.g., fetchPrompt('classifier-v2')"
    )
    inline_content: Optional[str] = Field(None, description="If inline, the actual string content (truncated if long)")
    variable_name: Optional[str] = Field(None, description="If from variable, the variable name")


class ContextVariable(BaseModel):
    """A variable injected into the AI call as context."""

    name: str = Field(..., description="Variable name in code")
    source_type: SourceType = Field(..., description="Where this variable comes from")
    source_hint: Optional[str] = Field(None, description="Code pattern that reveals source")
    shape_hint: Optional[str] = Field(None, description="Inferred shape: string, object, array, unknown")
    type_reference: Optional[str] = Field(None, description="If typed, the type/interface name")


class InputObservations(BaseModel):
    """Observations about what goes INTO the AI call."""

    system_prompt: Optional[InputSource] = Field(None, description="System prompt source, if present")
    messages: list[InputSource] = Field(default_factory=list, description="Message sources")
    context_variables: list[ContextVariable] = Field(default_factory=list, description="Variables injected as context")
    template_engine: Optional[str] = Field(None, description="Template engine if detected: handlebars, jinja, fstring")


class ValidationInfo(BaseModel):
    """Information about output validation."""

    type: ValidationType = Field(..., description="Type of validation")
    schema_location: Optional[Location] = Field(None, description="Where the schema is defined")
    schema_name: Optional[str] = Field(None, description="Name of schema/model if identifiable")


class OutputObservations(BaseModel):
    """Observations about what comes OUT of the AI call."""

    assigned_to: Optional[str] = Field(None, description="Variable name the output is assigned to")
    expected_format: Optional[str] = Field(None, description="Expected format: json, text, structured")
    response_format_specified: bool = Field(False, description="Whether response_format parameter is set")
    validation: Optional[ValidationInfo] = Field(None, description="Validation applied to output, if any")


class UsageObservations(BaseModel):
    """Observations about WHERE the output flows."""

    used_in_conditional: bool = Field(False, description="Whether output is used in if/switch/match")
    conditional_location: Optional[Location] = Field(None, description="Location of the conditional using output")
    conditional_type: Optional[ConditionalType] = Field(
        None, description="Type of conditional: if, switch, match, ternary"
    )
    returned_from_function: bool = Field(False, description="Whether output is returned from containing function")
    passed_to_functions: list[str] = Field(default_factory=list, description="Functions the output is passed to")
    assigned_to_property: Optional[str] = Field(None, description="Object property the output is assigned to")
    sinks: list[SinkType] = Field(default_factory=list, description="Categorized sinks where output flows")


# =============================================================================
# INTERPRETATION LAYER (versioned, can evolve)
# =============================================================================


class Interpretation(BaseModel):
    """Interpretation of observations - versioned separately from stable schema."""

    version: str = Field("0.1.0", description="Interpretation schema version")
    risk_tier: RiskTier = Field(..., description="Overall risk tier")
    scenario_complexity: ScenarioComplexity = Field(..., description="Complexity of scenario testing needed")
    observations_summary: list[str] = Field(
        default_factory=list, description="Human-readable summary of key observations"
    )
    suggested_focus: list[str] = Field(default_factory=list, description="Suggested areas to focus testing")


# =============================================================================
# TOP-LEVEL MODELS
# =============================================================================


class AiCallObservation(BaseModel):
    """Complete observation of a single AI call site."""

    id: str = Field(..., description="Unique identifier for this call site")
    location: Location = Field(..., description="Source code location")
    provider: Provider = Field(..., description="AI provider")
    call_type: CallType = Field(..., description="Type of API call")
    detection_method: DetectionMethod = Field(DetectionMethod.SDK_VERIFIED, description="How the call was detected")
    confidence: float = Field(1.0, description="Detection confidence (0.0 - 1.0)")

    inputs: InputObservations = Field(default_factory=InputObservations, description="Input observations")
    outputs: OutputObservations = Field(default_factory=OutputObservations, description="Output observations")
    usage: UsageObservations = Field(default_factory=UsageObservations, description="Usage/flow observations")

    interpretation: Optional[Interpretation] = Field(
        None, description="Risk interpretation (optional, versioned separately)"
    )


class Artifact(BaseModel):
    """A discovered artifact (prompt file, schema, etc.)."""

    type: str = Field(..., description="Artifact type: prompt_source, schema, etc.")
    reference: str = Field(..., description="How to access this artifact")
    location: Optional[Location] = Field(None, description="File location if applicable")
    used_by: list[str] = Field(default_factory=list, description="IDs of AI calls that use this artifact")


class RepoMetadata(BaseModel):
    """Metadata about the scanned repository."""

    root: str = Field(..., description="Absolute path to repo root")
    files_scanned: int = Field(..., description="Number of files scanned")
    languages: list[str] = Field(default_factory=list, description="Languages detected")


class ProjectSignals(BaseModel):
    """Signals about the project's tech stack."""

    frameworks: list[str] = Field(
        default_factory=list, description="Detected frameworks: nextjs, fastapi, express, etc."
    )
    ai_sdks: list[str] = Field(default_factory=list, description="AI SDKs found: openai, anthropic, etc.")
    validation_libraries: list[str] = Field(default_factory=list, description="Validation libs: zod, pydantic, etc.")


class DiscoveryOutput(BaseModel):
    """Top-level discovery output - the stable contract."""

    version: str = Field("1.0.0", description="Schema version")
    tool_version: str = Field("0.1.2", description="Flightline CLI version")
    repo_commit: Optional[str] = Field(None, description="Current repo commit hash")
    scanned_at: datetime = Field(default_factory=datetime.utcnow, description="When the scan was performed")

    repo: RepoMetadata = Field(..., description="Repository metadata")
    project_signals: ProjectSignals = Field(default_factory=ProjectSignals, description="Project tech stack signals")

    nodes: list[AiCallObservation] = Field(default_factory=list, description="Discovered AI call sites")
    artifacts: list[Artifact] = Field(default_factory=list, description="Discovered artifacts (prompts, schemas)")
