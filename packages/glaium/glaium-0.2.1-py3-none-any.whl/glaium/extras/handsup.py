"""Human escalation (Hands-Up) helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from glaium.models import HandsUpEvent, HandsUpSeverity


@dataclass
class HandsUp(Exception):
    """
    Exception to raise when human intervention is needed.

    Raising this exception in an agent callback signals that the
    agent cannot proceed without human input.

    Example:
        ```python
        from glaium.extras import HandsUp

        @agent.on_cycle
        def run_cycle(ctx):
            confidence = calculate_confidence()

            if confidence < 0.5:
                raise HandsUp(
                    severity="high",
                    category="low_confidence",
                    reason="Cannot determine optimal action",
                    proposed_action={"bid_change": 0.1},
                )

            return {"outputs": {...}, "effectiveness": 0.9}
        ```
    """

    severity: str = "normal"
    """Severity: 'low', 'normal', 'high', 'critical'."""
    category: str = "general"
    """Category: 'low_confidence', 'constraint_violated', 'anomaly', 'budget', etc."""
    reason: str = ""
    """Human-readable explanation."""
    context: dict[str, Any] = field(default_factory=dict)
    """Additional context data."""
    proposed_action: dict[str, Any] | None = None
    """Proposed action for human to approve/modify."""
    expires_at: datetime | None = None
    """When this request expires."""

    def __post_init__(self) -> None:
        # Initialize Exception
        super().__init__(self.reason)

    def to_event(self) -> HandsUpEvent:
        """Convert to HandsUpEvent for submission."""
        return HandsUpEvent(
            severity=HandsUpSeverity(self.severity),
            reason=self.reason,
            context=self.context,
            proposed_action=self.proposed_action,
        )


class HandsUpBuilder:
    """
    Builder for creating HandsUp exceptions with common patterns.

    Example:
        ```python
        from glaium.extras import HandsUpBuilder

        builder = HandsUpBuilder(agent_id="my-agent")

        # Low confidence
        raise builder.low_confidence(
            confidence=0.45,
            decision="increase bid",
            threshold=0.7,
        )

        # Budget exceeded
        raise builder.budget_exceeded(
            current=95000,
            limit=100000,
            proposed_spend=8000,
        )

        # Constraint violated
        raise builder.constraint_violated(
            constraint="CPI <= 2.50",
            actual_value=2.75,
        )
        ```
    """

    def __init__(self, agent_id: str | None = None):
        """
        Initialize builder.

        Args:
            agent_id: Agent ID for context.
        """
        self.agent_id = agent_id

    def _base_context(self) -> dict[str, Any]:
        """Get base context dict."""
        ctx: dict[str, Any] = {"timestamp": datetime.utcnow().isoformat()}
        if self.agent_id:
            ctx["agent_id"] = self.agent_id
        return ctx

    def low_confidence(
        self,
        confidence: float,
        decision: str,
        threshold: float = 0.7,
        proposed_action: dict[str, Any] | None = None,
    ) -> HandsUp:
        """
        Create HandsUp for low confidence decision.

        Args:
            confidence: Actual confidence score.
            decision: The decision being made.
            threshold: Confidence threshold that wasn't met.
            proposed_action: Proposed action for approval.

        Returns:
            HandsUp exception.
        """
        return HandsUp(
            severity="normal" if confidence > 0.4 else "high",
            category="low_confidence",
            reason=f"Low confidence ({confidence:.0%}) for decision: {decision}. Threshold: {threshold:.0%}",
            context={
                **self._base_context(),
                "confidence": confidence,
                "threshold": threshold,
                "decision": decision,
            },
            proposed_action=proposed_action,
        )

    def budget_exceeded(
        self,
        current: float,
        limit: float,
        proposed_spend: float,
        currency: str = "USD",
    ) -> HandsUp:
        """
        Create HandsUp for budget limit exceeded.

        Args:
            current: Current spend.
            limit: Budget limit.
            proposed_spend: Proposed additional spend.
            currency: Currency code.

        Returns:
            HandsUp exception.
        """
        overage = (current + proposed_spend) - limit
        return HandsUp(
            severity="high" if overage > limit * 0.1 else "normal",
            category="budget",
            reason=f"Proposed spend ({currency} {proposed_spend:,.2f}) would exceed budget by {currency} {overage:,.2f}",
            context={
                **self._base_context(),
                "current_spend": current,
                "budget_limit": limit,
                "proposed_spend": proposed_spend,
                "overage": overage,
                "currency": currency,
            },
            proposed_action={"spend": proposed_spend},
        )

    def constraint_violated(
        self,
        constraint: str,
        actual_value: float,
        expected_value: float | None = None,
        proposed_action: dict[str, Any] | None = None,
    ) -> HandsUp:
        """
        Create HandsUp for constraint violation.

        Args:
            constraint: Constraint description (e.g., "CPI <= 2.50").
            actual_value: Actual observed value.
            expected_value: Expected/limit value.
            proposed_action: Proposed action.

        Returns:
            HandsUp exception.
        """
        return HandsUp(
            severity="high",
            category="constraint_violated",
            reason=f"Constraint '{constraint}' violated. Actual: {actual_value}",
            context={
                **self._base_context(),
                "constraint": constraint,
                "actual_value": actual_value,
                "expected_value": expected_value,
            },
            proposed_action=proposed_action,
        )

    def anomaly_detected(
        self,
        metric: str,
        expected: float,
        actual: float,
        deviation_pct: float | None = None,
    ) -> HandsUp:
        """
        Create HandsUp for anomaly detection.

        Args:
            metric: Metric name.
            expected: Expected value.
            actual: Actual value.
            deviation_pct: Deviation percentage.

        Returns:
            HandsUp exception.
        """
        if deviation_pct is None:
            deviation_pct = abs(actual - expected) / expected * 100 if expected else 0

        severity = "critical" if deviation_pct > 50 else "high" if deviation_pct > 25 else "normal"

        return HandsUp(
            severity=severity,
            category="anomaly",
            reason=f"Anomaly in {metric}: expected {expected:.2f}, got {actual:.2f} ({deviation_pct:.1f}% deviation)",
            context={
                **self._base_context(),
                "metric": metric,
                "expected": expected,
                "actual": actual,
                "deviation_pct": deviation_pct,
            },
        )

    def custom(
        self,
        severity: str,
        category: str,
        reason: str,
        context: dict[str, Any] | None = None,
        proposed_action: dict[str, Any] | None = None,
        expires_in_hours: int | None = None,
    ) -> HandsUp:
        """
        Create custom HandsUp.

        Args:
            severity: Severity level.
            category: Category.
            reason: Reason text.
            context: Additional context.
            proposed_action: Proposed action.
            expires_in_hours: Hours until expiry.

        Returns:
            HandsUp exception.
        """
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        return HandsUp(
            severity=severity,
            category=category,
            reason=reason,
            context={**self._base_context(), **(context or {})},
            proposed_action=proposed_action,
            expires_at=expires_at,
        )
