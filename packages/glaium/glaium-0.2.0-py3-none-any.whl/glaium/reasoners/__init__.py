"""
Glaium Reasoners - Reasoning engines for agent decision-making.

Provides two reasoning implementations:
- AnalyticalReasoner: Uses formulas, statistics, and ML models (no LLM)
- LLMReasoner: Uses LLM (Claude, GPT) for reasoning

Example:
    ```python
    from glaium import Agent, CycleContext
    from glaium.reasoners import AnalyticalReasoner, LLMReasoner

    # Analytical reasoner (formula-based)
    analytical = AnalyticalReasoner(organization_id="org-123")

    # LLM reasoner (Claude/GPT-based)
    llm = LLMReasoner(
        model="claude-3-haiku-20240307",
        api_key="your-api-key",
    )

    @agent.on_cycle
    def on_cycle(ctx: CycleContext) -> dict:
        inputs = fetch_data()

        # Choose reasoner based on optimization settings
        if ctx.optimization.enable_llm_reasoning:
            result = llm.analyze(optimization=ctx.optimization, inputs=inputs)
        else:
            result = analytical.analyze(optimization=ctx.optimization, inputs=inputs)

        return {
            "inputs": inputs,
            "outputs": result.predicted_outputs,
        }
    ```
"""

from glaium.reasoners.analytical import AnalyticalReasoner
from glaium.reasoners.base import BaseReasoner, Reasoner
from glaium.reasoners.llm import LLMReasoner
from glaium.reasoners.models import (
    Analysis,
    Anomaly,
    Breach,
    MetricFormula,
    OrganizationModel,
    Recommendation,
    ReasonerOutput,
    SolverResult,
    Trend,
)

__all__ = [
    # Reasoners
    "Reasoner",
    "BaseReasoner",
    "AnalyticalReasoner",
    "LLMReasoner",
    # Output models
    "ReasonerOutput",
    "Analysis",
    "Anomaly",
    "Trend",
    "Breach",
    "Recommendation",
    "SolverResult",
    # Configuration models
    "MetricFormula",
    "OrganizationModel",
]
