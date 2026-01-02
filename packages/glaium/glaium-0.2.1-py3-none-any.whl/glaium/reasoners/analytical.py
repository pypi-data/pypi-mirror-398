"""
AnalyticalReasoner - Non-LLM reasoning engine for Glaium agents.

Uses statistical methods, mathematical formulas, and ML models to generate
recommendations without sending data to external LLM APIs.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any, List, Tuple

import numpy as np
import pandas as pd

from glaium.models import Constraint, Objective, Optimization
from glaium.reasoners.base import BaseReasoner
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

logger = logging.getLogger(__name__)


# Reasoning templates for generating human-readable explanations
REASONING_TEMPLATES = {
    "formula": (
        "To achieve {target_metric} {operator} {target_value:.2f}, "
        "{metric} should be {direction} from {current:,.2f} to {recommended:,.2f} "
        "(formula: {formula})"
    ),
    "ml": (
        "Based on historical patterns, adjusting {metric} from {current:,.2f} to {recommended:,.2f} "
        "is predicted to move {target_metric} toward {target_value:.2f} "
        "(confidence: {confidence:.0%})"
    ),
    "hybrid": (
        "Using formula and ML prediction, {metric} should be {direction} "
        "from {current:,.2f} to {recommended:,.2f} to achieve {target_metric} {operator} {target_value:.2f}"
    ),
}

# Action type mapping based on metric names
ACTION_TYPE_MAP = {
    "ua_spent": "budget",
    "spend": "budget",
    "budget": "budget",
    "bid_multiplier": "bid",
    "bid": "bid",
    "ad_frequency": "frequency",
    "frequency": "frequency",
    "budget_allocation": "allocation",
}


class AnalyticalReasoner(BaseReasoner):
    """
    Non-LLM reasoner using formulas, statistics, and ML models.

    Runs a three-stage pipeline:
    1. DETECT: Anomaly detection (Prophet), trend analysis, threshold breaches
    2. SOLVE: Use inverse formulas (deterministic) or ML models (stochastic)
    3. RECOMMEND: Format solver results into actionable recommendations

    Example:
        ```python
        from glaium import Agent, CycleContext
        from glaium.reasoners import AnalyticalReasoner

        reasoner = AnalyticalReasoner(organization_id="org-123")

        @agent.on_cycle
        def on_cycle(ctx: CycleContext) -> dict:
            inputs = fetch_data()
            result = reasoner.analyze(
                optimization=ctx.optimization,
                inputs=inputs,
            )

            for rec in result.recommendations:
                logger.info(f"{rec.action_type}: {rec.reasoning}")

            return {
                "inputs": inputs,
                "outputs": result.predicted_outputs,
            }
        ```
    """

    def __init__(
        self,
        organization_id: str | None = None,
        model: OrganizationModel | None = None,
        optimizer_client: Any | None = None,
        prophet_config: dict[str, Any] | None = None,
    ):
        """
        Initialize the AnalyticalReasoner.

        Args:
            organization_id: Organization ID to load model for.
            model: Pre-loaded organization model (optional).
            optimizer_client: Client for querying Optimizer ML models.
            prophet_config: Configuration for Prophet anomaly detection.
        """
        super().__init__(organization_id=organization_id, model=model)
        self._optimizer_client = optimizer_client
        self._prophet_config = prophet_config or {
            "interval_width": 0.95,
            "changepoint_prior_scale": 0.05,
            "yearly_seasonality": True,
            "weekly_seasonality": True,
            "daily_seasonality": False,
        }

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
        Analyze data and generate recommendations.

        Runs the three-stage pipeline: Detect -> Solve -> Recommend.

        Accepts data in two modes:
        1. Raw data mode: Pass `raw_data` and optionally `dimensions`.
           The reasoner will transform it into inputs + historical internally.
        2. Pre-processed mode: Pass `inputs` and `historical` directly.
           Use this when you've already prepared the data.

        Args:
            optimization: Current optimization objectives and constraints.
            raw_data: Raw daily rows from Data Service (with date dimension).
            inputs: Current input metric values (pre-processed mode).
            historical: Historical data for trend/anomaly detection (pre-processed mode).
            dimensions: List of dimension names in raw_data (e.g., ["yyyymmdd", "campaign"]).
            date_field: Name of the date field in raw_data (default: "yyyymmdd").

        Returns:
            ReasonerOutput containing analysis and recommendations.
        """
        # Transform raw data if provided, otherwise use pre-processed inputs
        if raw_data is not None:
            inputs, historical = self._prepare_data(
                raw_data=raw_data,
                dimensions=dimensions or [],
                date_field=date_field,
            )
        else:
            inputs = inputs or {}
            historical = historical or []

        # Stage 1: Detection
        analysis = self._detect(optimization, inputs, historical)

        # Stage 2: Solve for optimal values
        solver_results = self._solve(optimization, inputs, analysis)

        # Stage 3: Build recommendations
        recommendations = self._recommend(analysis, solver_results, inputs, optimization)

        # Calculate predicted outputs
        predicted_outputs = self._calculate_predicted_outputs(
            inputs, recommendations, optimization
        )

        return ReasonerOutput(
            analysis=analysis,
            recommendations=recommendations,
            predicted_outputs=predicted_outputs,
            metadata={
                "reasoner": "analytical",
                "stages_completed": ["detect", "solve", "recommend"],
                "data_mode": "raw" if raw_data is not None else "pre-processed",
            },
        )

    # =========================================================================
    # Data Preparation
    # =========================================================================

    def _prepare_data(
        self,
        raw_data: list[dict[str, Any]],
        dimensions: list[str],
        date_field: str = "yyyymmdd",
    ) -> Tuple[dict[str, float], list[dict[str, Any]]]:
        """
        Transform raw daily data into inputs + historical for analysis.

        This method:
        1. Sorts data by date
        2. Converts date field to datetime 'ds' for Prophet compatibility
        3. Aggregates the latest day's values as "current inputs" for the solver
        4. Returns full time-series as "historical" for detection

        Args:
            raw_data: Raw rows from Data Service (with date dimension).
            dimensions: List of dimension names (e.g., ["yyyymmdd", "campaign"]).
            date_field: Name of the date field (default: "yyyymmdd").

        Returns:
            Tuple of (inputs, historical):
            - inputs: Latest day values aggregated (for solver stage)
            - historical: Time-series with 'ds' datetime (for detection stage)
        """
        if not raw_data:
            return {}, []

        # Sort by date
        sorted_data = sorted(
            raw_data,
            key=lambda x: str(x.get(date_field, ""))
        )

        # Convert date field to datetime 'ds' for Prophet
        historical = []
        for row in sorted_data:
            record = {**row}
            if date_field in row:
                try:
                    date_str = str(row[date_field])
                    # Handle both YYYYMMDD and YYYY-MM-DD formats
                    if "-" in date_str:
                        record["ds"] = datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        record["ds"] = datetime.strptime(date_str, "%Y%m%d")
                except ValueError:
                    # If date parsing fails, skip the ds field
                    pass
            historical.append(record)

        # Find latest date
        dates = [str(r.get(date_field, "")) for r in raw_data if date_field in r]
        if not dates:
            # No date field, aggregate all rows
            latest_rows = raw_data
        else:
            latest_date = max(dates)
            latest_rows = [r for r in raw_data if str(r.get(date_field)) == latest_date]

        # Aggregate latest day's values as "current inputs"
        inputs: dict[str, float] = {}
        for row in latest_rows:
            for key, val in row.items():
                # Skip dimension fields and non-numeric values
                if key in dimensions or key == date_field or key == "ds":
                    continue
                if isinstance(val, (int, float)) and val is not None:
                    inputs[key] = inputs.get(key, 0) + float(val)

        return inputs, historical

    def _aggregate_by_date(
        self,
        historical: list[dict[str, Any]],
        metrics: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Aggregate historical data by date for time-series analysis.

        Use this when you need daily totals across all dimensions
        (e.g., for overall trend analysis rather than per-campaign).

        Args:
            historical: Historical data with 'ds' datetime field.
            metrics: Optional list of metrics to aggregate. If None, aggregates all numeric fields.

        Returns:
            List of daily aggregated records with 'ds' and summed metrics.
        """
        if not historical:
            return []

        daily_totals: dict[datetime, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for row in historical:
            ds = row.get("ds")
            if ds is None:
                continue

            for key, val in row.items():
                if key == "ds":
                    continue
                if metrics is not None and key not in metrics:
                    continue
                if isinstance(val, (int, float)) and val is not None:
                    daily_totals[ds][key] += float(val)

        # Convert to list sorted by date
        result = []
        for ds in sorted(daily_totals.keys()):
            record = {"ds": ds, **daily_totals[ds]}
            result.append(record)

        return result

    # =========================================================================
    # Stage 1: Detection
    # =========================================================================

    def _detect(
        self,
        optimization: Optimization,
        inputs: dict[str, Any],
        historical: list[dict[str, Any]],
    ) -> Analysis:
        """Run detection stage: anomalies, trends, threshold breaches."""
        anomalies = []
        trends = []
        breaches = []

        # Detect anomalies using Prophet (if historical data available)
        if historical:
            anomalies = self._detect_anomalies(inputs, historical)
            trends = self._detect_trends(historical)

        # Detect threshold breaches against objectives
        breaches = self._detect_breaches(inputs, optimization)

        return Analysis(
            anomalies=anomalies,
            trends=trends,
            threshold_breaches=breaches,
        )

    def _detect_anomalies(
        self,
        inputs: dict[str, Any],
        historical: list[dict[str, Any]],
    ) -> list[Anomaly]:
        """
        Detect anomalies using Prophet confidence intervals.

        Falls back to z-score method if Prophet is not available.
        """
        anomalies = []

        for metric, current_value in inputs.items():
            if not isinstance(current_value, (int, float)):
                continue

            # Extract historical values for this metric
            hist_values = [
                h.get(metric) for h in historical
                if metric in h and isinstance(h.get(metric), (int, float))
            ]

            if len(hist_values) < 7:
                # Not enough data for statistical analysis
                continue

            # Try Prophet-based detection
            try:
                metric_anomalies = self._detect_anomalies_prophet(
                    metric, current_value, historical
                )
                anomalies.extend(metric_anomalies)
            except ImportError:
                # Fall back to z-score method
                anomaly = self._detect_anomaly_zscore(metric, current_value, hist_values)
                if anomaly:
                    anomalies.append(anomaly)
            except Exception as e:
                logger.warning(f"Prophet anomaly detection failed for {metric}: {e}")
                # Fall back to z-score method
                anomaly = self._detect_anomaly_zscore(metric, current_value, hist_values)
                if anomaly:
                    anomalies.append(anomaly)

        return anomalies

    def _detect_anomalies_prophet(
        self,
        metric: str,
        current_value: float,
        historical: list[dict[str, Any]],
    ) -> list[Anomaly]:
        """Detect anomalies using Facebook Prophet."""
        from prophet import Prophet

        # Prepare data for Prophet
        df = self._prepare_prophet_data(metric, historical)
        if df is None or len(df) < 7:
            return []

        # Get boundaries from model if available
        floor, cap = None, None
        if self.model:
            metric_formula = self.model.get_metric(metric)
            if metric_formula:
                floor, cap = metric_formula.boundaries

        # Configure Prophet
        growth = "logistic" if floor is not None or cap is not None else "linear"
        model = Prophet(
            growth=growth,
            interval_width=self._prophet_config.get("interval_width", 0.95),
            changepoint_prior_scale=self._prophet_config.get("changepoint_prior_scale", 0.05),
            yearly_seasonality=self._prophet_config.get("yearly_seasonality", True),
            weekly_seasonality=self._prophet_config.get("weekly_seasonality", True),
            daily_seasonality=self._prophet_config.get("daily_seasonality", False),
        )

        # Set floor/cap if using logistic growth
        if floor is not None:
            df["floor"] = floor
        if cap is not None:
            df["cap"] = cap

        # Fit and predict
        model.fit(df)
        forecast = model.predict(df)

        # Detect anomalies (values outside confidence bounds)
        anomalies = []
        for i, row in forecast.iterrows():
            actual = df.iloc[i]["y"]
            if actual < row["yhat_lower"] or actual > row["yhat_upper"]:
                anomalies.append(Anomaly(
                    metric=metric,
                    date=row["ds"].to_pydatetime(),
                    value=actual,
                    expected=row["yhat"],
                    lower_bound=row["yhat_lower"],
                    upper_bound=row["yhat_upper"],
                ))

        return anomalies

    def _prepare_prophet_data(
        self,
        metric: str,
        historical: list[dict[str, Any]],
    ) -> pd.DataFrame | None:
        """Prepare historical data for Prophet."""
        records = []
        for h in historical:
            if metric not in h:
                continue
            value = h.get(metric)
            if not isinstance(value, (int, float)):
                continue

            # Try to get date from common field names
            date = None
            for date_field in ["ds", "date", "yyyymmdd", "timestamp"]:
                if date_field in h:
                    date_val = h[date_field]
                    if isinstance(date_val, datetime):
                        date = date_val
                    elif isinstance(date_val, str):
                        try:
                            date = pd.to_datetime(date_val)
                        except Exception:
                            pass
                    break

            if date is not None:
                records.append({"ds": date, "y": float(value)})

        if not records:
            return None

        df = pd.DataFrame(records)
        df = df.sort_values("ds").reset_index(drop=True)
        return df

    def _detect_anomaly_zscore(
        self,
        metric: str,
        current_value: float,
        historical_values: list[float],
    ) -> Anomaly | None:
        """Detect anomaly using z-score method (fallback)."""
        if len(historical_values) < 2:
            return None

        mean = statistics.mean(historical_values)
        stdev = statistics.stdev(historical_values)

        if stdev == 0:
            return None

        z_score = (current_value - mean) / stdev

        # Anomaly if beyond 2 standard deviations
        if abs(z_score) > 2.0:
            return Anomaly(
                metric=metric,
                date=datetime.now(),
                value=current_value,
                expected=mean,
                lower_bound=mean - 2 * stdev,
                upper_bound=mean + 2 * stdev,
            )

        return None

    def _detect_trends(
        self,
        historical: list[dict[str, Any]],
        window: int = 7,
        r_squared_threshold: float = 0.7,
    ) -> list[Trend]:
        """Detect trends using linear regression."""
        trends = []

        # Get all numeric metrics
        if not historical:
            return trends

        sample = historical[0]
        numeric_metrics = [
            k for k, v in sample.items()
            if isinstance(v, (int, float)) and k not in ["ds", "date", "yyyymmdd"]
        ]

        for metric in numeric_metrics:
            values = [
                h.get(metric) for h in historical[-window:]
                if metric in h and isinstance(h.get(metric), (int, float))
            ]

            if len(values) < window:
                continue

            # Simple linear regression
            x = np.arange(len(values))
            y = np.array(values)

            # Calculate slope and R-squared
            x_mean = np.mean(x)
            y_mean = np.mean(y)

            numerator = np.sum((x - x_mean) * (y - y_mean))
            denominator = np.sum((x - x_mean) ** 2)

            if denominator == 0:
                continue

            slope = numerator / denominator

            # Calculate R-squared
            y_pred = slope * (x - x_mean) + y_mean
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y_mean) ** 2)

            if ss_tot == 0:
                continue

            r_squared = 1 - (ss_res / ss_tot)

            # Only report strong trends
            if r_squared >= r_squared_threshold:
                trends.append(Trend(
                    metric=metric,
                    direction="increasing" if slope > 0 else "decreasing",
                    slope=float(slope),
                    r_squared=float(r_squared),
                    period_days=window,
                ))

        return trends

    def _detect_breaches(
        self,
        inputs: dict[str, Any],
        optimization: Optimization,
    ) -> list[Breach]:
        """Detect threshold breaches against objectives and constraints."""
        breaches = []

        # Check objectives
        for objective in optimization.objectives:
            current = inputs.get(objective.metric)
            if current is None or not isinstance(current, (int, float)):
                continue

            if not self._check_operator(current, objective.operator, objective.target):
                breaches.append(Breach(
                    metric=objective.metric,
                    target=objective.target,
                    operator=objective.operator,
                    current=float(current),
                    gap=abs(float(current) - objective.target),
                ))

        # Check constraints
        for constraint in optimization.constraints:
            if constraint.required is None:
                continue

            current = constraint.current or inputs.get(constraint.metric)
            if current is None or not isinstance(current, (int, float)):
                continue

            if not self._check_operator(current, constraint.operator, constraint.required):
                breaches.append(Breach(
                    metric=constraint.metric,
                    target=constraint.required,
                    operator=constraint.operator,
                    current=float(current),
                    gap=abs(float(current) - constraint.required),
                ))

        return breaches

    # =========================================================================
    # Stage 2: Solver
    # =========================================================================

    def _solve(
        self,
        optimization: Optimization,
        inputs: dict[str, Any],
        analysis: Analysis,
    ) -> list[SolverResult]:
        """Solve for optimal values to achieve objectives."""
        results = []

        for objective in optimization.objectives:
            # Check if we have a breach for this objective
            breach = next(
                (b for b in analysis.threshold_breaches if b.metric == objective.metric),
                None,
            )

            if breach is None:
                # Objective already met
                continue

            # Try to solve for this objective
            result = self._solve_objective(objective, inputs)
            if result:
                results.append(result)

        return results

    def _solve_objective(
        self,
        objective: Objective,
        inputs: dict[str, Any],
    ) -> SolverResult | None:
        """Solve for a single objective."""
        if self.model is None:
            logger.warning("No organization model available for solving")
            return None

        metric_formula = self.model.get_metric(objective.metric)
        if metric_formula is None:
            logger.warning(f"No formula found for metric: {objective.metric}")
            return None

        formula_type = metric_formula.formula_type

        if formula_type == "deterministic":
            return self._solve_deterministic(objective, inputs, metric_formula)
        elif formula_type == "stochastic":
            return self._solve_stochastic(objective, inputs)
        elif formula_type == "hybrid":
            return self._solve_hybrid(objective, inputs, metric_formula)
        else:
            logger.warning(f"Unknown formula type: {formula_type}")
            return None

    def _solve_deterministic(
        self,
        objective: Objective,
        inputs: dict[str, Any],
        metric_formula: MetricFormula,
    ) -> SolverResult | None:
        """Solve using inverse formulas."""
        inverse_formulas = metric_formula.inverse_formulas
        if not inverse_formulas:
            logger.warning(f"No inverse formulas for {objective.metric}")
            return None

        solutions = {}
        formula_used = None

        for variable, formula in inverse_formulas.items():
            if variable in inputs:
                # We already have this value, check if we should recommend changing it
                pass

            # Build evaluation context
            context = {
                **{k: float(v) for k, v in inputs.items() if isinstance(v, (int, float))},
                objective.metric: objective.target,
            }

            # Check validity condition
            if metric_formula.validity_condition:
                try:
                    if not eval(metric_formula.validity_condition, {"__builtins__": {}}, context):
                        continue
                except Exception:
                    continue

            # Evaluate inverse formula
            try:
                value = eval(formula, {"__builtins__": {}}, context)
                solutions[variable] = float(value)
                formula_used = f"{variable} = {formula}"
            except Exception as e:
                logger.warning(f"Failed to evaluate formula {formula}: {e}")

        if not solutions:
            return None

        return SolverResult(
            values=solutions,
            source="formula",
            confidence=1.0,
            formula_used=formula_used,
        )

    def _solve_stochastic(
        self,
        objective: Objective,
        inputs: dict[str, Any],
    ) -> SolverResult | None:
        """Solve using Optimizer's ML model."""
        if self._optimizer_client is None:
            logger.warning("No optimizer client available for stochastic solving")
            return None

        relationship = self.model.get_relationship(objective.metric) if self.model else None
        controllable_params = relationship.get("modulated_by", []) if relationship else []

        try:
            response = self._optimizer_client.predict(
                target_metric=objective.metric,
                target_value=objective.target,
                current_inputs=inputs,
                controllable_params=controllable_params,
            )
            return SolverResult(
                values=response.get("recommended_values", {}),
                source="ml",
                confidence=response.get("confidence", 0.85),
            )
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return None

    def _solve_hybrid(
        self,
        objective: Objective,
        inputs: dict[str, Any],
        metric_formula: MetricFormula,
    ) -> SolverResult | None:
        """Solve using both deterministic and stochastic methods."""
        det_result = self._solve_deterministic(objective, inputs, metric_formula)
        stoch_result = self._solve_stochastic(objective, inputs)

        values = {}
        if det_result:
            values.update(det_result.values)
        if stoch_result:
            values.update(stoch_result.values)

        if not values:
            return None

        return SolverResult(
            values=values,
            source="hybrid",
            confidence=0.9,
            formula_used=det_result.formula_used if det_result else None,
        )

    # =========================================================================
    # Stage 3: Recommend
    # =========================================================================

    def _recommend(
        self,
        analysis: Analysis,
        solver_results: list[SolverResult],
        inputs: dict[str, Any],
        optimization: Optimization,
    ) -> list[Recommendation]:
        """Build recommendations from solver results."""
        recommendations = []

        for result in solver_results:
            for metric, recommended_value in result.values.items():
                current_value = inputs.get(metric)
                if current_value is None or not isinstance(current_value, (int, float)):
                    continue

                current_value = float(current_value)
                change = recommended_value - current_value

                if abs(change) < 0.001:
                    # No meaningful change
                    continue

                change_pct = (change / current_value * 100) if current_value != 0 else 0

                # Infer action type
                action_type = self._infer_action_type(metric, change)

                # Find related breach for context
                related_breach = self._find_related_breach(analysis, metric, optimization)

                # Generate reasoning
                reasoning = self._generate_reasoning(
                    metric=metric,
                    current=current_value,
                    recommended=recommended_value,
                    source=result.source,
                    breach=related_breach,
                    formula=result.formula_used,
                    confidence=result.confidence,
                )

                recommendations.append(Recommendation(
                    action_type=action_type,
                    target=metric,
                    current_value=current_value,
                    recommended_value=recommended_value,
                    change=change,
                    change_pct=change_pct,
                    reasoning=reasoning,
                    confidence=result.confidence,
                    source=result.source,
                ))

        return recommendations

    def _infer_action_type(self, metric: str, change: float) -> str:
        """Infer action type from metric name and change direction."""
        direction = "increase" if change > 0 else "decrease"

        # Look for matching action type
        for key, action in ACTION_TYPE_MAP.items():
            if key in metric.lower():
                return f"{direction}_{action}"

        return f"{direction}_parameter"

    def _find_related_breach(
        self,
        analysis: Analysis,
        metric: str,
        optimization: Optimization,
    ) -> Breach | None:
        """Find a breach related to this metric (through formula dependencies)."""
        # First check direct breach
        for breach in analysis.threshold_breaches:
            if breach.metric == metric:
                return breach

        # Check if metric is an input to any objective formula
        if self.model:
            for breach in analysis.threshold_breaches:
                formula = self.model.get_metric(breach.metric)
                if formula and metric in formula.formula:
                    return breach

        # Return first breach as fallback
        return analysis.threshold_breaches[0] if analysis.threshold_breaches else None

    def _generate_reasoning(
        self,
        metric: str,
        current: float,
        recommended: float,
        source: str,
        breach: Breach | None,
        formula: str | None,
        confidence: float,
    ) -> str:
        """Generate human-readable reasoning using templates."""
        direction = "increased" if recommended > current else "decreased"

        template = REASONING_TEMPLATES.get(source, REASONING_TEMPLATES["formula"])

        try:
            return template.format(
                metric=metric,
                current=current,
                recommended=recommended,
                direction=direction,
                target_metric=breach.metric if breach else "target",
                target_value=breach.target if breach else 0,
                operator=breach.operator if breach else "<=",
                formula=formula or "",
                confidence=confidence,
            )
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}")
            return f"{metric} should be {direction} from {current:,.2f} to {recommended:,.2f}"

    def _calculate_predicted_outputs(
        self,
        inputs: dict[str, Any],
        recommendations: list[Recommendation],
        optimization: Optimization,
    ) -> dict[str, float]:
        """Calculate predicted output values after applying recommendations."""
        predicted = {}

        # Start with current objective values
        for objective in optimization.objectives:
            current = inputs.get(objective.metric)
            if isinstance(current, (int, float)):
                predicted[objective.metric] = float(current)

        # Apply recommendations to predict new values
        if self.model:
            updated_inputs = {
                **{k: float(v) for k, v in inputs.items() if isinstance(v, (int, float))},
            }

            for rec in recommendations:
                updated_inputs[rec.target] = rec.recommended_value

            # Recalculate output metrics using formulas
            for objective in optimization.objectives:
                formula = self.model.get_metric(objective.metric)
                if formula and formula.formula_type == "deterministic":
                    try:
                        value = eval(
                            formula.formula,
                            {"__builtins__": {}},
                            updated_inputs,
                        )
                        predicted[objective.metric] = float(value)
                    except Exception as e:
                        logger.warning(f"Failed to predict {objective.metric}: {e}")

        return predicted
