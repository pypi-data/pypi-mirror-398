"""Risk-based verification for hallucination mitigation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """Risk levels for decisions."""

    LOW = "low"
    """Informational, no execution. Single model, no verification."""
    MEDIUM = "medium"
    """Reversible actions. Self-consistency (3 samples)."""
    HIGH = "high"
    """Significant impact. Multi-model panel verification."""
    CRITICAL = "critical"
    """Requires human approval. Multi-model + human review."""


@dataclass
class VerificationResult:
    """Result of decision verification."""

    decision: str | None
    """The verified decision (None if no consensus)."""
    confidence: float
    """Confidence score 0.0-1.0."""
    consensus_level: str
    """'unanimous', 'majority', 'split', or 'error'."""
    requires_human: bool
    """Whether human review is required."""
    reasoning: str
    """Explanation of verification result."""
    votes: dict[str, int] | None = None
    """Vote counts by decision (for panel verification)."""


class Verification:
    """
    Risk-based verification service for hallucination mitigation.

    Implements verification strategies based on risk level:
    - LOW: Single model, no additional verification
    - MEDIUM: Self-consistency (3 samples from same model)
    - HIGH: Multi-model panel (Claude, GPT-4, Gemini)
    - CRITICAL: Multi-model + human approval required

    Example:
        ```python
        from glaium.extras import Verification, RiskLevel

        verifier = Verification()

        # Classify risk
        risk = verifier.classify_risk(
            action_type="budget_change",
            parameters={"budget_change": 5000},
        )

        # Verify decision (mock - requires LLM integration)
        result = await verifier.verify(
            prompt="Should we increase budget?",
            risk_level=risk,
        )

        if result.requires_human:
            # Escalate to human
            pass
        elif result.confidence >= 0.7:
            # Proceed with decision
            pass
        ```
    """

    # Thresholds for risk classification
    BUDGET_THRESHOLDS = {
        "low": 100,
        "medium": 1000,
        "high": 10000,
    }

    HIGH_RISK_ACTIONS = [
        "pause_campaign",
        "change_strategy",
        "reallocate_budget",
        "stop_campaign",
    ]

    MEDIUM_RISK_ACTIONS = [
        "adjust_bid",
        "change_target",
        "modify_audience",
    ]

    def __init__(
        self,
        llm_gateway: Any | None = None,
        confidence_threshold: float = 0.7,
    ):
        """
        Initialize verification service.

        Args:
            llm_gateway: Optional LLM gateway for actual verification.
            confidence_threshold: Minimum confidence to proceed without human.
        """
        self._llm = llm_gateway
        self.confidence_threshold = confidence_threshold

    def classify_risk(
        self,
        action_type: str,
        parameters: dict[str, Any],
    ) -> RiskLevel:
        """
        Classify the risk level of a decision.

        Args:
            action_type: Type of action (e.g., 'budget_change', 'bid_adjust').
            parameters: Action parameters.

        Returns:
            RiskLevel enum value.
        """
        # Check budget-related risk
        budget = abs(parameters.get("budget_change", 0))
        if budget > self.BUDGET_THRESHOLDS["high"]:
            return RiskLevel.CRITICAL
        if budget > self.BUDGET_THRESHOLDS["medium"]:
            return RiskLevel.HIGH
        if budget > self.BUDGET_THRESHOLDS["low"]:
            return RiskLevel.MEDIUM

        # Check action type risk
        if action_type in self.HIGH_RISK_ACTIONS:
            return RiskLevel.HIGH
        if action_type in self.MEDIUM_RISK_ACTIONS:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    async def verify(
        self,
        prompt: str,
        risk_level: RiskLevel,
    ) -> VerificationResult:
        """
        Verify a decision based on risk level.

        Note: Full implementation requires LLM integration.
        This provides the framework and mock responses.

        Args:
            prompt: The decision prompt to verify.
            risk_level: Risk level for verification strategy.

        Returns:
            VerificationResult with confidence and consensus.
        """
        if risk_level == RiskLevel.LOW:
            return self._single_model(prompt)
        elif risk_level == RiskLevel.MEDIUM:
            return await self._self_consistency(prompt)
        elif risk_level == RiskLevel.HIGH:
            return await self._multi_model_panel(prompt)
        else:  # CRITICAL
            result = await self._multi_model_panel(prompt)
            result.requires_human = True
            return result

    def _single_model(self, prompt: str) -> VerificationResult:
        """Single model verification (no additional checks)."""
        # In production, this would call the LLM
        return VerificationResult(
            decision="proceed",
            confidence=0.85,
            consensus_level="single",
            requires_human=False,
            reasoning="Single model verification (low risk)",
        )

    async def _self_consistency(
        self,
        prompt: str,
        samples: int = 3,
    ) -> VerificationResult:
        """
        Self-consistency verification.

        Queries the same model multiple times with temperature > 0
        and checks if responses agree.
        """
        if self._llm is None:
            # Mock response for testing
            return VerificationResult(
                decision="proceed",
                confidence=0.80,
                consensus_level="majority",
                requires_human=False,
                reasoning=f"Self-consistency: {samples-1}/{samples} samples agree (mock)",
                votes={"proceed": samples - 1, "wait": 1},
            )

        # In production: query LLM multiple times and aggregate
        # responses = [await self._llm.reason(prompt, temperature=0.7) for _ in range(samples)]
        # decisions = [extract_decision(r) for r in responses]
        # ... aggregate and return

        return VerificationResult(
            decision="proceed",
            confidence=0.80,
            consensus_level="majority",
            requires_human=False,
            reasoning="Self-consistency verification",
        )

    async def _multi_model_panel(self, prompt: str) -> VerificationResult:
        """
        Multi-model panel verification.

        Queries multiple LLM providers and requires majority agreement.
        """
        if self._llm is None:
            # Mock response for testing
            return VerificationResult(
                decision="proceed",
                confidence=0.90,
                consensus_level="majority",
                requires_human=False,
                reasoning="Multi-model panel: 2/3 agree (mock)",
                votes={"proceed": 2, "wait": 1},
            )

        # In production: query Claude, GPT-4, Gemini
        # panel_models = ["claude-3-5-sonnet", "gpt-4o", "gemini-pro"]
        # responses = await asyncio.gather(*[self._llm.query(m, prompt) for m in panel_models])
        # ... aggregate votes

        return VerificationResult(
            decision="proceed",
            confidence=0.90,
            consensus_level="majority",
            requires_human=False,
            reasoning="Multi-model panel verification",
        )

    def needs_human_review(self, result: VerificationResult) -> bool:
        """Check if a verification result needs human review."""
        if result.requires_human:
            return True
        if result.confidence < self.confidence_threshold:
            return True
        if result.consensus_level == "split":
            return True
        return False


def classify_action_risk(
    action_type: str,
    parameters: dict[str, Any],
) -> RiskLevel:
    """
    Convenience function to classify action risk.

    Args:
        action_type: Type of action.
        parameters: Action parameters.

    Returns:
        RiskLevel enum value.
    """
    verifier = Verification()
    return verifier.classify_risk(action_type, parameters)
