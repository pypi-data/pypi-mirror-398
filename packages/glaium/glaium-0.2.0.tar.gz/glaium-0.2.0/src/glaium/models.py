"""Pydantic models for Glaium SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# =============================================================================
# Registration Models
# =============================================================================


class AgentInput(BaseModel):
    """Declared input for an agent."""

    name: str
    source: str | dict[str, str] = "external"
    """Either 'external' or {'agent': '<agent_id>', 'output': '<output_name>'}"""


class AgentOutput(BaseModel):
    """Declared output for an agent."""

    name: str


class AgentConnection(BaseModel):
    """Connection between agents."""

    input: str
    """Input name to receive data on."""
    from_agent: str
    """Source agent ID."""
    from_output: str
    """Source output name."""


class RegistrationRequest(BaseModel):
    """Request to register an agent with the optimizer."""

    agent_id: str
    declared_inputs: list[AgentInput] = Field(default_factory=list)
    declared_outputs: list[AgentOutput] = Field(default_factory=list)
    connections: list[AgentConnection] = Field(default_factory=list)
    formula: str | None = None
    token_ttl_hours: int = Field(default=48, ge=1, le=8760)
    dimensions: list[str] = Field(
        default_factory=list,
        description="Dimension fields for data grouping (e.g., ['country', 'platform'])",
    )
    lookback_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days of historical data to fetch for analysis",
    )

    # Identity fields (for UI and platform integration)
    name: str = Field(
        ...,
        description="Human-readable agent name (e.g., 'User Acquisition')",
    )
    objective_function: str = Field(
        ...,
        description="Agent's goal/system prompt for LLM reasoning",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of what this agent does",
    )
    color: str | None = Field(
        default=None,
        description="Optional hex color for UI display (e.g., '#3b82f6')",
    )
    icon: str | None = Field(
        default=None,
        description="Optional icon name for UI display (e.g., 'users')",
    )


class RegistrationResponse(BaseModel):
    """Response from agent registration."""

    status: Literal["registered"]
    agent_token: str


# =============================================================================
# Optimization Models (renamed from Direction)
# =============================================================================


class Objective(BaseModel):
    """An optimization objective for the agent."""

    metric: str
    """Target metric name (e.g., 'installs', 'revenue')."""
    target: float
    """Target value to achieve."""
    operator: Literal[">=", "<=", "==", ">", "<"]
    """Comparison operator."""


class Constraint(BaseModel):
    """A constraint on agent behavior."""

    metric: str
    """Constraint metric name."""
    operator: str
    """Comparison operator."""
    is_bottleneck: bool = False
    """True if this agent is the system bottleneck."""
    limit: float | None = None
    """Current baseline value (if bottleneck)."""
    required: float | None = None
    """Organization goal requirement."""
    current: float | None = None
    """Currently observed value."""
    gap: float | None = None
    """Gap between required and current (required - current)."""
    overproducing: bool | None = None
    """True if producing more than downstream needs."""
    downstream_needs: float | None = None
    """What downstream agents need."""
    excess: float | None = None
    """Excess production (current - downstream_needs)."""


class SearchSpaceParam(BaseModel):
    """Parameter range for optimization search space."""

    min: float
    max: float
    avg: float
    last: float


class UpstreamStatus(str, Enum):
    """Health status of upstream agents."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STRUGGLING = "struggling"
    UNKNOWN = "unknown"


class InventoryStatus(BaseModel):
    """Inventory status between connected agents."""

    to_agent: str
    """Downstream agent ID."""
    metric: str
    """Metric name."""
    produced: float
    """Cumulative output produced."""
    consumed: float
    """Cumulative consumption by downstream."""
    inventory: float
    """Buffer: produced - consumed."""


class Optimization(BaseModel):
    """
    Optimization response from the optimizer.

    Contains objectives, constraints, search space, and scheduling info.
    """

    objectives: list[Objective] = Field(default_factory=list)
    """What the agent should optimize toward."""
    constraints: list[Constraint] = Field(default_factory=list)
    """Constraints on agent behavior."""
    search_space: dict[str, SearchSpaceParam] = Field(default_factory=dict)
    """Observable parameter ranges for tuning."""
    upstream_status: dict[str, UpstreamStatus] = Field(default_factory=dict)
    """Health status of upstream agents."""
    downstream_inventory: list[InventoryStatus] = Field(default_factory=list)
    """Inventory buffers with downstream agents."""

    # Scheduling
    next_cycle_at: datetime | None = None
    """Exact datetime for next cycle (if set by optimizer)."""
    cycle_interval: int | None = None
    """Seconds between cycles (if set by optimizer)."""

    # Organization-level settings
    enable_llm_reasoning: bool = Field(
        default=False,
        description="Whether to use LLM reasoning (from org settings). If False, use AnalyticalReasoner.",
    )
    objective_function: str | None = Field(
        default=None,
        description="Custom objective function/system prompt if user modified it in UI.",
    )


# =============================================================================
# Event Models
# =============================================================================


class CycleStartEvent(BaseModel):
    """Event indicating cycle start."""

    event: Literal["cycle_start"] = "cycle_start"
    cycle_number: int
    timestamp: datetime | None = None


class CycleEndEvent(BaseModel):
    """Event indicating cycle completion with results."""

    event: Literal["cycle_end"] = "cycle_end"
    cycle_number: int
    inputs: dict[str, Any] = Field(default_factory=dict)
    """Actual input values used in this cycle."""
    outputs: dict[str, Any] = Field(default_factory=dict)
    """Actual output results from this cycle."""


class CycleInterruptEvent(BaseModel):
    """Event indicating cycle was interrupted."""

    event: Literal["cycle_interrupt"] = "cycle_interrupt"
    cycle_number: int
    reason: str


class AnomalyEvent(BaseModel):
    """Event reporting detected anomaly."""

    event: Literal["anomaly"] = "anomaly"
    metric: str
    expected: float
    actual: float


class HandsUpSeverity(str, Enum):
    """Severity levels for human escalation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HandsUpEvent(BaseModel):
    """Event requesting human intervention."""

    event: Literal["hands_up"] = "hands_up"
    severity: HandsUpSeverity
    reason: str
    context: dict[str, Any] = Field(default_factory=dict)
    proposed_action: dict[str, Any] | None = None


# Union type for all events
Event = CycleStartEvent | CycleEndEvent | CycleInterruptEvent | AnomalyEvent | HandsUpEvent


class EventResponse(BaseModel):
    """Response from event submission."""

    status: Literal["processed", "received"]
    message: str | None = None


# =============================================================================
# Cycle Context (for high-level agent framework)
# =============================================================================


class CycleContext(BaseModel):
    """Context passed to cycle callbacks."""

    cycle_number: int
    """Current cycle number."""
    optimization: Optimization
    """Current optimization from optimizer."""
    scheduled_at: datetime
    """When this cycle was scheduled to run."""
    inputs: dict[str, Any] = Field(default_factory=dict)
    """Available inputs for this cycle."""

    class Config:
        arbitrary_types_allowed = True
