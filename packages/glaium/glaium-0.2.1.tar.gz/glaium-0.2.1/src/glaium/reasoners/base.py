"""Base protocol for Glaium reasoners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from glaium.models import Optimization
from glaium.reasoners.models import OrganizationModel, ReasonerOutput


@runtime_checkable
class Reasoner(Protocol):
    """
    Protocol for agent reasoners.

    Reasoners analyze input data against optimization objectives and generate
    recommendations to achieve those objectives.

    Two implementations are provided:
    - AnalyticalReasoner: Uses formulas, statistics, and ML models
    - LLMReasoner: Uses LLM (Claude) for reasoning

    Data Flow:
        Reasoners support two modes:
        1. Raw data mode: Pass raw_data with dimensions, reasoner handles transformation
        2. Pre-processed mode: Pass inputs + historical directly (legacy compatibility)
    """

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
        Analyze inputs and generate recommendations.

        Args:
            optimization: Current optimization objectives and constraints.
            raw_data: Raw daily data rows (preferred). If provided, inputs/historical
                are derived internally via _prepare_data().
            inputs: Current input metric values (legacy mode).
            historical: Historical data for trend/anomaly detection (legacy mode).
            dimensions: Dimension fields to group by (e.g., ["country", "platform"]).
            date_field: Name of the date field in raw_data (default: "yyyymmdd").

        Returns:
            ReasonerOutput containing analysis and recommendations.
        """
        ...


class BaseReasoner(ABC):
    """
    Abstract base class for reasoners.

    Provides common functionality for all reasoner implementations.
    """

    def __init__(
        self,
        organization_id: str | None = None,
        model: OrganizationModel | None = None,
    ):
        """
        Initialize the reasoner.

        Args:
            organization_id: Organization ID to load model for.
            model: Pre-loaded organization model (optional).
        """
        self.organization_id = organization_id
        self._model = model

    @property
    def model(self) -> OrganizationModel | None:
        """Get the organization model."""
        return self._model

    @model.setter
    def model(self, value: OrganizationModel) -> None:
        """Set the organization model."""
        self._model = value

    @abstractmethod
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
        Analyze inputs and generate recommendations.

        Args:
            optimization: Current optimization objectives and constraints.
            raw_data: Raw daily data rows (preferred). If provided, inputs/historical
                are derived internally via _prepare_data().
            inputs: Current input metric values (legacy mode).
            historical: Historical data for trend/anomaly detection (legacy mode).
            dimensions: Dimension fields to group by (e.g., ["country", "platform"]).
            date_field: Name of the date field in raw_data (default: "yyyymmdd").

        Returns:
            ReasonerOutput containing analysis and recommendations.
        """
        pass

    def _check_operator(self, value: float, operator: str, target: float) -> bool:
        """Check if a value satisfies an operator condition."""
        ops = {
            ">=": lambda v, t: v >= t,
            "<=": lambda v, t: v <= t,
            ">": lambda v, t: v > t,
            "<": lambda v, t: v < t,
            "==": lambda v, t: v == t,
        }
        return ops.get(operator, lambda v, t: False)(value, target)
