"""Data models for Glaium reasoners."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class Anomaly:
    """An anomaly detected in metric data."""

    metric: str
    """Metric name where anomaly was detected."""
    date: datetime
    """Date of the anomaly."""
    value: float
    """Actual observed value."""
    expected: float
    """Expected value (yhat from Prophet)."""
    lower_bound: float
    """Lower confidence bound."""
    upper_bound: float
    """Upper confidence bound."""

    @property
    def deviation_pct(self) -> float:
        """Percentage deviation from expected."""
        if self.expected == 0:
            return 0.0
        return ((self.value - self.expected) / self.expected) * 100


@dataclass
class Trend:
    """A trend detected in metric data."""

    metric: str
    """Metric name where trend was detected."""
    direction: Literal["increasing", "decreasing"]
    """Trend direction."""
    slope: float
    """Slope of the trend line."""
    r_squared: float
    """R-squared value (goodness of fit)."""
    period_days: int
    """Number of days in the trend window."""


@dataclass
class Breach:
    """A threshold breach against objectives or constraints."""

    metric: str
    """Metric that breached threshold."""
    target: float
    """Target value from objective/constraint."""
    operator: str
    """Comparison operator (>=, <=, ==, etc.)."""
    current: float
    """Current observed value."""
    gap: float
    """Absolute gap between current and target."""

    @property
    def gap_pct(self) -> float:
        """Gap as percentage of target."""
        if self.target == 0:
            return 0.0
        return (self.gap / abs(self.target)) * 100


@dataclass
class Analysis:
    """Results from the detection stage."""

    anomalies: list[Anomaly] = field(default_factory=list)
    """Anomalies detected in input data."""
    trends: list[Trend] = field(default_factory=list)
    """Trends detected in input data."""
    threshold_breaches: list[Breach] = field(default_factory=list)
    """Objective/constraint breaches detected."""


@dataclass
class SolverResult:
    """Result from the solver stage."""

    values: dict[str, float]
    """Recommended values for metrics/parameters."""
    source: Literal["formula", "ml", "hybrid"]
    """How the values were derived."""
    confidence: float
    """Confidence in the recommendation (0.0-1.0)."""
    formula_used: str | None = None
    """Formula used (for deterministic solutions)."""


@dataclass
class Recommendation:
    """A recommendation for action."""

    action_type: str
    """Type of action (e.g., 'adjust_budget', 'increase_bid')."""
    target: str
    """Target metric or parameter to act on."""
    current_value: float
    """Current value of the target."""
    recommended_value: float
    """Recommended new value."""
    change: float
    """Absolute change (recommended - current)."""
    change_pct: float
    """Percentage change."""
    reasoning: str
    """Human-readable explanation."""
    confidence: float
    """Confidence in the recommendation (0.0-1.0)."""
    source: Literal["formula", "ml", "hybrid"]
    """How the recommendation was derived."""


@dataclass
class ReasonerOutput:
    """Output from a reasoner."""

    analysis: Analysis
    """Detection results (anomalies, trends, breaches)."""
    recommendations: list[Recommendation]
    """Recommendations for action."""
    predicted_outputs: dict[str, float]
    """Predicted output values after recommendations are applied."""
    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata from the reasoner."""


@dataclass
class MetricFormula:
    """Formula definition for a metric."""

    id: str
    """Metric identifier."""
    formula: str
    """Formula expression (e.g., 'ua_spent / installs')."""
    formula_type: Literal["deterministic", "stochastic", "hybrid"]
    """Type of formula."""
    inverse_formulas: dict[str, str] = field(default_factory=dict)
    """Inverse formulas for solving (e.g., {'ua_spent': 'cpi * installs'})."""
    validity_condition: str | None = None
    """Condition for formula validity (e.g., 'installs > 0')."""
    boundaries: tuple[float | None, float | None] = (None, None)
    """Floor and cap boundaries (floor, cap)."""
    aggregation: str = "sum"
    """Aggregation method (sum, avg, etc.)."""


@dataclass
class OrganizationModel:
    """Organization model containing metric definitions."""

    organization_id: str
    """Organization identifier."""
    metrics: dict[str, MetricFormula]
    """Metric formulas by metric ID."""
    relationships: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Stochastic relationships between metrics."""

    def get_metric(self, metric_id: str) -> MetricFormula | None:
        """Get metric formula by ID."""
        return self.metrics.get(metric_id)

    def get_relationship(self, metric_id: str) -> dict[str, Any] | None:
        """Get stochastic relationship by target metric ID."""
        return self.relationships.get(metric_id)
