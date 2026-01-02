"""LLM-based Reasoner for Glaium agents.

Uses Large Language Models (Claude, GPT, etc.) for reasoning and recommendation
generation. This is an alternative to the AnalyticalReasoner for cases where:
- Formulas are not well-defined
- Complex qualitative reasoning is needed
- Multi-factor analysis benefits from LLM understanding

Example:
    ```python
    from glaium import Agent
    from glaium.reasoners import LLMReasoner

    # Basic usage (uses default optimization prompt)
    reasoner = LLMReasoner(
        model="claude-3-haiku-20240307",
        api_key="your-api-key",
    )

    # Custom domain-specific prompt
    reasoner = LLMReasoner(
        model="claude-3-haiku-20240307",
        api_key="your-api-key",
        system_prompt="You are a financial portfolio optimization expert.",
        task_instructions=\"\"\"
        Analyze the portfolio allocation against risk tolerance.
        Consider market volatility and correlation between assets.
        Recommend rebalancing actions to optimize Sharpe ratio.
        \"\"\",
    )

    @agent.on_cycle
    def on_cycle(ctx):
        result = reasoner.analyze(
            optimization=ctx.optimization,
            raw_data=fetch_data(),
        )
        return {"outputs": result.predicted_outputs}
    ```
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Literal

from glaium.models import Optimization
from glaium.reasoners.base import BaseReasoner
from glaium.reasoners.models import (
    Analysis,
    Anomaly,
    Breach,
    OrganizationModel,
    Recommendation,
    ReasonerOutput,
    Trend,
)

logger = logging.getLogger(__name__)


class LLMReasoner(BaseReasoner):
    """
    LLM-based reasoner for agent decision-making.

    Uses a Large Language Model to analyze input data against optimization
    objectives and generate recommendations.

    Supports:
    - Claude (Anthropic)
    - GPT (OpenAI)
    - Other compatible providers
    """

    def __init__(
        self,
        organization_id: str | None = None,
        model: OrganizationModel | None = None,
        llm_model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
        provider: Literal["anthropic", "openai"] = "anthropic",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        task_instructions: str | None = None,
    ):
        """
        Initialize the LLM reasoner.

        Args:
            organization_id: Organization ID for model loading.
            model: Pre-loaded organization model (optional).
            llm_model: LLM model identifier (default: claude-3-haiku).
            api_key: API key for the LLM provider.
            provider: LLM provider ('anthropic' or 'openai').
            temperature: LLM temperature for response variability.
            max_tokens: Maximum tokens in LLM response.
            system_prompt: Custom system prompt for domain-specific reasoning.
                If not provided, uses default optimization agent prompt.
            task_instructions: Custom task instructions to replace default
                analysis steps. If not provided, uses standard optimization
                analysis (anomalies, trends, recommendations).
        """
        super().__init__(organization_id, model)
        self.llm_model = llm_model
        self.api_key = api_key
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.task_instructions = task_instructions

    def analyze(
        self,
        optimization: Optimization,
        raw_data: list[dict[str, Any]] | None = None,
        inputs: dict[str, Any] | None = None,
        historical: list[dict[str, Any]] | None = None,
        dimensions: list[str] | None = None,
        date_field: str = "yyyymmdd",
    ) -> ReasonerOutput:
        """
        Analyze inputs and generate recommendations using LLM.

        Args:
            optimization: Current optimization objectives and constraints.
            raw_data: Raw daily data rows (preferred).
            inputs: Current input metric values (legacy mode).
            historical: Historical data for trend analysis (legacy mode).
            dimensions: Dimension fields to group by.
            date_field: Name of the date field in raw_data.

        Returns:
            ReasonerOutput containing analysis and recommendations.
        """
        # Prepare input data
        if raw_data is not None:
            data_context = self._prepare_raw_data(raw_data, dimensions, date_field)
        else:
            data_context = self._prepare_legacy_data(inputs, historical)

        # Build LLM prompt
        prompt = self._build_prompt(optimization, data_context)

        # Call LLM
        try:
            response = self._call_llm(prompt)
            result = self._parse_response(response, optimization)
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            # Return minimal output on failure
            result = ReasonerOutput(
                analysis=Analysis(),
                recommendations=[],
                predicted_outputs={},
                metadata={"error": str(e), "llm_model": self.llm_model},
            )

        return result

    def _prepare_raw_data(
        self,
        raw_data: list[dict[str, Any]],
        dimensions: list[str] | None,
        date_field: str,
    ) -> dict[str, Any]:
        """Prepare raw data for LLM prompt."""
        # Aggregate and summarize data
        if not raw_data:
            return {"summary": "No data available", "rows": []}

        # Get latest values
        latest_row = raw_data[-1] if raw_data else {}

        # Calculate basic statistics
        numeric_cols = {}
        for key in raw_data[0].keys():
            if key == date_field or (dimensions and key in dimensions):
                continue
            values = [row.get(key) for row in raw_data if isinstance(row.get(key), (int, float))]
            if values:
                numeric_cols[key] = {
                    "current": values[-1] if values else 0,
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": "increasing" if len(values) > 1 and values[-1] > values[0] else "decreasing",
                }

        return {
            "latest_values": latest_row,
            "statistics": numeric_cols,
            "row_count": len(raw_data),
            "dimensions": dimensions or [],
        }

    def _prepare_legacy_data(
        self,
        inputs: dict[str, Any] | None,
        historical: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Prepare legacy inputs/historical format for LLM prompt."""
        return {
            "latest_values": inputs or {},
            "historical_rows": len(historical) if historical else 0,
        }

    def _build_prompt(
        self,
        optimization: Optimization,
        data_context: dict[str, Any],
    ) -> str:
        """Build the LLM prompt for analysis."""
        # Format objectives
        objectives_text = self._format_objectives(optimization)

        # Format constraints
        constraints_text = self._format_constraints(optimization)

        # Format search space
        search_space_text = self._format_search_space(optimization)

        # Format data
        data_text = json.dumps(data_context, indent=2, default=str)

        # Use custom system prompt or default
        system_intro = self.system_prompt or "You are an AI optimization agent. Analyze the following data and objectives to generate recommendations."

        # Use custom task instructions or default
        if self.task_instructions:
            task_section = f"""## YOUR TASK
{self.task_instructions}

After your analysis, provide your response in the JSON format below."""
        else:
            task_section = """## YOUR TASK
1. Analyze the current data against the objectives and constraints
2. Identify any anomalies, trends, or threshold breaches
3. Generate specific, actionable recommendations
4. Predict output values after recommendations are applied"""

        prompt = f"""{system_intro}

## OPTIMIZATION OBJECTIVE
{objectives_text}

## CONSTRAINTS
{constraints_text}

## SEARCH SPACE (adjustable parameters)
{search_space_text}

## CURRENT DATA
{data_text}

{task_section}

## RESPONSE FORMAT
Respond with valid JSON in this exact format:
{{
    "analysis": {{
        "anomalies": [
            {{"metric": "...", "value": 0.0, "expected": 0.0, "deviation_pct": 0.0}}
        ],
        "trends": [
            {{"metric": "...", "direction": "increasing|decreasing", "strength": "strong|moderate|weak"}}
        ],
        "breaches": [
            {{"metric": "...", "target": 0.0, "current": 0.0, "gap_pct": 0.0}}
        ]
    }},
    "recommendations": [
        {{
            "action_type": "adjust_budget|increase_bid|decrease_bid|reallocate|other",
            "target": "metric_name",
            "current_value": 0.0,
            "recommended_value": 0.0,
            "reasoning": "Brief explanation",
            "confidence": 0.0
        }}
    ],
    "predicted_outputs": {{
        "metric_name": 0.0
    }},
    "reasoning": "Overall analysis summary"
}}

IMPORTANT: Only include fields with valid data. Do not include empty arrays if there are no items.
"""
        return prompt

    def _format_objectives(self, optimization: Optimization) -> str:
        """Format optimization objectives for prompt."""
        lines = []
        if optimization.objective:
            lines.append(f"Primary Objective: {optimization.objective.type.upper()} {optimization.objective.metric}")
            if optimization.objective.target:
                lines.append(f"Target: {optimization.objective.target}")

        if optimization.secondary_objectives:
            lines.append("\nSecondary Objectives:")
            for obj in optimization.secondary_objectives:
                lines.append(f"  - {obj.type.upper()} {obj.metric}")

        return "\n".join(lines) if lines else "No specific objectives defined."

    def _format_constraints(self, optimization: Optimization) -> str:
        """Format constraints for prompt."""
        lines = []
        if optimization.constraints:
            for constraint in optimization.constraints:
                lines.append(f"- {constraint.metric} {constraint.operator} {constraint.value}")

        return "\n".join(lines) if lines else "No constraints defined."

    def _format_search_space(self, optimization: Optimization) -> str:
        """Format search space for prompt."""
        lines = []
        if optimization.search_space:
            for name, param in optimization.search_space.items():
                lines.append(f"- {name}: range [{param.min}, {param.max}], current: {param.last}")

        return "\n".join(lines) if lines else "No adjustable parameters defined."

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API."""
        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic (Claude) API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required for LLMReasoner. "
                "Install with: pip install anthropic"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        # Build request with optional system prompt
        request_kwargs = {
            "model": self.llm_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Add system prompt if provided (Claude supports system as separate field)
        if self.system_prompt:
            request_kwargs["system"] = self.system_prompt

        message = client.messages.create(**request_kwargs)

        # Extract text content
        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI (GPT) API."""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package is required for LLMReasoner with openai provider. "
                "Install with: pip install openai"
            )

        # Use custom system prompt or default
        system_message = self.system_prompt or "You are an AI optimization agent."

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.llm_model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    def _parse_response(
        self,
        response: str,
        optimization: Optimization,
    ) -> ReasonerOutput:
        """Parse LLM response into ReasonerOutput."""
        # Extract JSON from response
        try:
            # Try to find JSON in response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return ReasonerOutput(
                analysis=Analysis(),
                recommendations=[],
                predicted_outputs={},
                metadata={"parse_error": str(e), "raw_response": response[:500]},
            )

        # Parse analysis
        analysis_data = data.get("analysis", {})
        anomalies = []
        for a in analysis_data.get("anomalies", []):
            try:
                anomalies.append(Anomaly(
                    metric=a.get("metric", "unknown"),
                    date=datetime.now(),
                    value=float(a.get("value", 0)),
                    expected=float(a.get("expected", 0)),
                    lower_bound=float(a.get("expected", 0)) * 0.9,
                    upper_bound=float(a.get("expected", 0)) * 1.1,
                ))
            except (TypeError, ValueError):
                continue

        trends = []
        for t in analysis_data.get("trends", []):
            try:
                trends.append(Trend(
                    metric=t.get("metric", "unknown"),
                    direction=t.get("direction", "increasing"),
                    slope=0.0,  # LLM doesn't provide slope
                    r_squared=0.0,
                    period_days=7,
                ))
            except (TypeError, ValueError):
                continue

        breaches = []
        for b in analysis_data.get("breaches", []):
            try:
                target = float(b.get("target", 0))
                current = float(b.get("current", 0))
                breaches.append(Breach(
                    metric=b.get("metric", "unknown"),
                    target=target,
                    operator=">=",  # Default
                    current=current,
                    gap=abs(target - current),
                ))
            except (TypeError, ValueError):
                continue

        analysis = Analysis(
            anomalies=anomalies,
            trends=trends,
            threshold_breaches=breaches,
        )

        # Parse recommendations
        recommendations = []
        for r in data.get("recommendations", []):
            try:
                current = float(r.get("current_value", 0))
                recommended = float(r.get("recommended_value", 0))
                change = recommended - current
                change_pct = (change / current * 100) if current != 0 else 0

                recommendations.append(Recommendation(
                    action_type=r.get("action_type", "adjust"),
                    target=r.get("target", "unknown"),
                    current_value=current,
                    recommended_value=recommended,
                    change=change,
                    change_pct=change_pct,
                    reasoning=r.get("reasoning", "LLM recommendation"),
                    confidence=float(r.get("confidence", 0.7)),
                    source="hybrid",  # LLM is considered hybrid source
                ))
            except (TypeError, ValueError):
                continue

        # Parse predicted outputs
        predicted_outputs = {}
        for key, value in data.get("predicted_outputs", {}).items():
            try:
                predicted_outputs[key] = float(value)
            except (TypeError, ValueError):
                predicted_outputs[key] = 0.0

        return ReasonerOutput(
            analysis=analysis,
            recommendations=recommendations,
            predicted_outputs=predicted_outputs,
            metadata={
                "llm_model": self.llm_model,
                "provider": self.provider,
                "reasoning": data.get("reasoning", ""),
            },
        )
