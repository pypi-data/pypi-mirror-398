"""High-level agent framework for Glaium SDK."""

from __future__ import annotations

import asyncio
import inspect
import logging
import signal
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from glaium.client import Client
from glaium.exceptions import AgentError, AlreadyRunningError, CycleError, NotRegisteredError
from glaium.models import (
    AgentConnection,
    AgentInput,
    AgentOutput,
    CycleContext,
    CycleEndEvent,
    CycleStartEvent,
    Optimization,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class CycleResult:
    """Result returned from a cycle callback."""

    outputs: dict[str, Any] = field(default_factory=dict)
    effectiveness: float = 0.0
    efficiency: float = 0.0
    inputs: dict[str, Any] = field(default_factory=dict)


class Agent:
    """
    High-level agent framework with decorator-based callbacks.

    Manages the agent lifecycle: registration, optimization polling,
    cycle execution, and event reporting.

    Example:
        ```python
        from glaium import Agent

        agent = Agent(
            agent_id="sales-agent",
            declared_outputs=[{"name": "deals_closed"}],
        )

        @agent.on_optimization
        def handle_optimization(optimization):
            print(f"New objectives: {optimization.objectives}")

        @agent.on_cycle
        def run_cycle(ctx):
            # Your agent logic
            return {
                "outputs": {"deals_closed": 15},
                "effectiveness": 0.75,
                "efficiency": 0.85,
            }

        # Run the agent
        agent.run()
        ```
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        objective_function: str,
        declared_inputs: list[dict[str, Any] | AgentInput] | None = None,
        declared_outputs: list[dict[str, Any] | AgentOutput] | None = None,
        connections: list[dict[str, Any] | AgentConnection] | None = None,
        formula: str | None = None,
        token_ttl_hours: int = 48,
        dimensions: list[str] | None = None,
        lookback_days: int = 30,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        poll_interval: int = 60,
        default_cycle_interval: int = 300,
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = 3,
    ):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent.
            name: Human-readable agent name (e.g., 'User Acquisition').
            objective_function: Agent's goal/system prompt for LLM reasoning.
            declared_inputs: Inputs the agent accepts.
            declared_outputs: Outputs the agent produces.
            connections: Connections to other agents.
            formula: Optional computation formula.
            token_ttl_hours: Token validity period (1-8760 hours).
            dimensions: Dimension fields for data grouping (e.g., ['country', 'platform']).
            lookback_days: Number of days of historical data to fetch (1-365).
            description: Optional description of what this agent does.
            color: Optional hex color for UI display (e.g., '#3b82f6').
            icon: Optional icon name for UI display (e.g., 'users').
            poll_interval: Seconds between optimization polls.
            default_cycle_interval: Default seconds between cycles if not specified by optimizer.
            api_key: API key (or use GLAIUM_API_KEY env var).
            base_url: Base URL for optimizer API.
            max_retries: Max retries for API calls.
        """
        self.agent_id = agent_id
        self.name = name
        self.objective_function = objective_function
        self.declared_inputs = declared_inputs or []
        self.declared_outputs = declared_outputs or []
        self.connections = connections or []
        self.formula = formula
        self.token_ttl_hours = token_ttl_hours
        self.dimensions = dimensions or []
        self.lookback_days = lookback_days
        self.description = description
        self.color = color
        self.icon = icon
        self.poll_interval = poll_interval
        self.default_cycle_interval = default_cycle_interval

        # Client configuration
        self._api_key = api_key
        self._base_url = base_url
        self._max_retries = max_retries

        # State
        self._client: Client | None = None
        self._token: str | None = None
        self._current_optimization: Optimization | None = None
        self._cycle_number: int = 0
        self._running: bool = False
        self._stop_event: threading.Event = threading.Event()

        # Callbacks
        self._on_optimization_callback: Callable[[Optimization], Any] | None = None
        self._on_cycle_callback: Callable[[CycleContext], dict[str, Any] | CycleResult] | None = None
        self._on_error_callback: Callable[[Exception], Any] | None = None
        self._on_start_callback: Callable[[], Any] | None = None
        self._on_stop_callback: Callable[[], Any] | None = None

    # =========================================================================
    # Decorators
    # =========================================================================

    def on_optimization(self, func: F) -> F:
        """
        Decorator for handling new optimizations.

        Called when the optimizer provides new objectives/constraints.

        Example:
            ```python
            @agent.on_optimization
            def handle_optimization(optimization):
                print(f"Objectives: {optimization.objectives}")
            ```
        """
        self._on_optimization_callback = func
        return func

    def on_cycle(self, func: F) -> F:
        """
        Decorator for the main cycle logic.

        Called each cycle. Must return outputs and metrics.

        Example:
            ```python
            @agent.on_cycle
            def run_cycle(ctx):
                return {
                    "outputs": {"revenue": 1000},
                    "effectiveness": 0.8,
                    "efficiency": 0.9,
                }
            ```
        """
        self._on_cycle_callback = func
        return func

    def on_error(self, func: F) -> F:
        """
        Decorator for error handling.

        Called when an unhandled error occurs during cycle execution.

        Example:
            ```python
            @agent.on_error
            def handle_error(error):
                logging.error(f"Agent error: {error}")
            ```
        """
        self._on_error_callback = func
        return func

    def on_start(self, func: F) -> F:
        """
        Decorator for startup logic.

        Called once when the agent starts, after registration.
        """
        self._on_start_callback = func
        return func

    def on_stop(self, func: F) -> F:
        """
        Decorator for shutdown logic.

        Called when the agent stops.
        """
        self._on_stop_callback = func
        return func

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def is_registered(self) -> bool:
        """Check if the agent is registered."""
        return self._token is not None

    @property
    def is_running(self) -> bool:
        """Check if the agent is currently running."""
        return self._running

    @property
    def current_optimization(self) -> Optimization | None:
        """Get the current optimization."""
        return self._current_optimization

    @property
    def cycle_number(self) -> int:
        """Get the current cycle number."""
        return self._cycle_number

    # =========================================================================
    # Registration
    # =========================================================================

    def _ensure_client(self) -> Client:
        """Ensure client is created."""
        if self._client is None:
            self._client = Client(
                api_key=self._api_key,
                base_url=self._base_url,
                max_retries=self._max_retries,
            )
        return self._client

    def register(self) -> None:
        """Register the agent with the optimizer (sync)."""
        client = self._ensure_client()
        response = client.register(
            agent_id=self.agent_id,
            name=self.name,
            objective_function=self.objective_function,
            declared_inputs=self.declared_inputs,
            declared_outputs=self.declared_outputs,
            connections=self.connections,
            formula=self.formula,
            token_ttl_hours=self.token_ttl_hours,
            dimensions=self.dimensions,
            lookback_days=self.lookback_days,
            description=self.description,
            color=self.color,
            icon=self.icon,
        )
        self._token = response.agent_token
        self._client = client.with_token(self._token)
        logger.info(f"Agent '{self.agent_id}' registered successfully")

    async def register_async(self) -> None:
        """Register the agent with the optimizer (async)."""
        client = self._ensure_client()
        response = await client.register_async(
            agent_id=self.agent_id,
            name=self.name,
            objective_function=self.objective_function,
            declared_inputs=self.declared_inputs,
            declared_outputs=self.declared_outputs,
            connections=self.connections,
            formula=self.formula,
            token_ttl_hours=self.token_ttl_hours,
            dimensions=self.dimensions,
            lookback_days=self.lookback_days,
            description=self.description,
            color=self.color,
            icon=self.icon,
        )
        self._token = response.agent_token
        self._client = client.with_token(self._token)
        logger.info(f"Agent '{self.agent_id}' registered successfully")

    # =========================================================================
    # Cycle Execution
    # =========================================================================

    def _calculate_wait_time(self, optimization: Optimization) -> float:
        """Calculate how long to wait before next cycle."""
        now = datetime.now(timezone.utc)

        # If optimizer specified exact time
        if optimization.next_cycle_at:
            next_time = optimization.next_cycle_at
            if next_time.tzinfo is None:
                next_time = next_time.replace(tzinfo=timezone.utc)

            wait_seconds = (next_time - now).total_seconds()
            # If in the past, run immediately
            return max(0, wait_seconds)

        # If optimizer specified interval
        if optimization.cycle_interval:
            return optimization.cycle_interval

        # Fall back to default
        return self.default_cycle_interval

    def _run_cycle_sync(self) -> CycleResult | None:
        """Execute a single cycle (sync)."""
        if not self._client or not self._token:
            raise NotRegisteredError("Agent not registered. Call register() first.")

        if not self._on_cycle_callback:
            raise AgentError("No cycle callback defined. Use @agent.on_cycle decorator.")

        self._cycle_number += 1
        cycle_num = self._cycle_number

        try:
            # Submit cycle start event
            self._client.submit_event(CycleStartEvent(
                cycle_number=cycle_num,
                timestamp=datetime.now(timezone.utc),
            ))

            # Create context
            ctx = CycleContext(
                cycle_number=cycle_num,
                optimization=self._current_optimization or Optimization(),
                scheduled_at=datetime.now(timezone.utc),
                inputs={},  # Could be populated from upstream agents
            )

            # Execute callback
            if inspect.iscoroutinefunction(self._on_cycle_callback):
                # Async callback in sync context
                result = asyncio.run(self._on_cycle_callback(ctx))
            else:
                result = self._on_cycle_callback(ctx)

            # Normalize result
            if isinstance(result, CycleResult):
                cycle_result = result
            elif isinstance(result, dict):
                cycle_result = CycleResult(
                    outputs=result.get("outputs", {}),
                    effectiveness=result.get("effectiveness", 0.0),
                    efficiency=result.get("efficiency", 0.0),
                    inputs=result.get("inputs", {}),
                )
            else:
                cycle_result = CycleResult()

            # Submit cycle end event
            self._client.submit_event(CycleEndEvent(
                cycle_number=cycle_num,
                inputs=cycle_result.inputs,
                outputs=cycle_result.outputs,
                effectiveness=cycle_result.effectiveness,
                efficiency=cycle_result.efficiency,
            ))

            logger.debug(f"Cycle {cycle_num} completed: effectiveness={cycle_result.effectiveness}")
            return cycle_result

        except Exception as e:
            logger.error(f"Cycle {cycle_num} failed: {e}")
            if self._on_error_callback:
                self._on_error_callback(e)
            raise CycleError(str(e), cycle_number=cycle_num) from e

    async def _run_cycle_async(self) -> CycleResult | None:
        """Execute a single cycle (async)."""
        if not self._client or not self._token:
            raise NotRegisteredError("Agent not registered. Call register_async() first.")

        if not self._on_cycle_callback:
            raise AgentError("No cycle callback defined. Use @agent.on_cycle decorator.")

        self._cycle_number += 1
        cycle_num = self._cycle_number

        try:
            # Submit cycle start event
            await self._client.submit_event_async(CycleStartEvent(
                cycle_number=cycle_num,
                timestamp=datetime.now(timezone.utc),
            ))

            # Create context
            ctx = CycleContext(
                cycle_number=cycle_num,
                optimization=self._current_optimization or Optimization(),
                scheduled_at=datetime.now(timezone.utc),
                inputs={},
            )

            # Execute callback
            if inspect.iscoroutinefunction(self._on_cycle_callback):
                result = await self._on_cycle_callback(ctx)
            else:
                result = self._on_cycle_callback(ctx)

            # Normalize result
            if isinstance(result, CycleResult):
                cycle_result = result
            elif isinstance(result, dict):
                cycle_result = CycleResult(
                    outputs=result.get("outputs", {}),
                    effectiveness=result.get("effectiveness", 0.0),
                    efficiency=result.get("efficiency", 0.0),
                    inputs=result.get("inputs", {}),
                )
            else:
                cycle_result = CycleResult()

            # Submit cycle end event
            await self._client.submit_event_async(CycleEndEvent(
                cycle_number=cycle_num,
                inputs=cycle_result.inputs,
                outputs=cycle_result.outputs,
                effectiveness=cycle_result.effectiveness,
                efficiency=cycle_result.efficiency,
            ))

            logger.debug(f"Cycle {cycle_num} completed: effectiveness={cycle_result.effectiveness}")
            return cycle_result

        except Exception as e:
            logger.error(f"Cycle {cycle_num} failed: {e}")
            if self._on_error_callback:
                if inspect.iscoroutinefunction(self._on_error_callback):
                    await self._on_error_callback(e)
                else:
                    self._on_error_callback(e)
            raise CycleError(str(e), cycle_number=cycle_num) from e

    # =========================================================================
    # Run Methods
    # =========================================================================

    def run(self) -> None:
        """
        Run the agent in blocking mode.

        Registers, polls for optimizations, and executes cycles until stopped.
        """
        if self._running:
            raise AlreadyRunningError("Agent is already running")

        self._running = True
        self._stop_event.clear()

        # Set up signal handlers
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        def _signal_handler(sig: int, frame: Any) -> None:
            logger.info(f"Received signal {sig}, stopping agent...")
            self.stop()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        try:
            # Register if not already
            if not self.is_registered:
                self.register()

            # Call start callback
            if self._on_start_callback:
                self._on_start_callback()

            logger.info(f"Agent '{self.agent_id}' started")

            # Main loop
            last_poll = 0.0
            while not self._stop_event.is_set():
                now = time.time()

                # Poll for optimization updates
                if now - last_poll >= self.poll_interval:
                    try:
                        new_optimization = self._client.get_optimization()  # type: ignore
                        if new_optimization != self._current_optimization:
                            self._current_optimization = new_optimization
                            if self._on_optimization_callback:
                                self._on_optimization_callback(new_optimization)
                        last_poll = now
                    except Exception as e:
                        logger.warning(f"Failed to poll optimization: {e}")

                # Run cycle
                if self._current_optimization and self._on_cycle_callback:
                    try:
                        self._run_cycle_sync()
                    except CycleError:
                        pass  # Error already handled

                    # Wait for next cycle
                    wait_time = self._calculate_wait_time(self._current_optimization)
                    self._stop_event.wait(wait_time)
                else:
                    # No optimization yet, wait and retry
                    self._stop_event.wait(self.poll_interval)

        finally:
            self._running = False
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

            if self._on_stop_callback:
                self._on_stop_callback()

            logger.info(f"Agent '{self.agent_id}' stopped")

    async def run_async(self) -> None:
        """
        Run the agent in async mode.

        Registers, polls for optimizations, and executes cycles until stopped.
        """
        if self._running:
            raise AlreadyRunningError("Agent is already running")

        self._running = True
        self._stop_event.clear()

        try:
            # Register if not already
            if not self.is_registered:
                await self.register_async()

            # Call start callback
            if self._on_start_callback:
                if inspect.iscoroutinefunction(self._on_start_callback):
                    await self._on_start_callback()
                else:
                    self._on_start_callback()

            logger.info(f"Agent '{self.agent_id}' started (async)")

            # Main loop
            last_poll = 0.0
            while not self._stop_event.is_set():
                now = time.time()

                # Poll for optimization updates
                if now - last_poll >= self.poll_interval:
                    try:
                        new_optimization = await self._client.get_optimization_async()  # type: ignore
                        if new_optimization != self._current_optimization:
                            self._current_optimization = new_optimization
                            if self._on_optimization_callback:
                                if inspect.iscoroutinefunction(self._on_optimization_callback):
                                    await self._on_optimization_callback(new_optimization)
                                else:
                                    self._on_optimization_callback(new_optimization)
                        last_poll = now
                    except Exception as e:
                        logger.warning(f"Failed to poll optimization: {e}")

                # Run cycle
                if self._current_optimization and self._on_cycle_callback:
                    try:
                        await self._run_cycle_async()
                    except CycleError:
                        pass  # Error already handled

                    # Wait for next cycle
                    wait_time = self._calculate_wait_time(self._current_optimization)
                    await asyncio.sleep(wait_time)
                else:
                    # No optimization yet, wait and retry
                    await asyncio.sleep(self.poll_interval)

        finally:
            self._running = False

            if self._on_stop_callback:
                if inspect.iscoroutinefunction(self._on_stop_callback):
                    await self._on_stop_callback()
                else:
                    self._on_stop_callback()

            logger.info(f"Agent '{self.agent_id}' stopped")

    def start(self) -> threading.Thread:
        """
        Start the agent in a background thread.

        Returns:
            The thread running the agent.

        Example:
            ```python
            thread = agent.start()
            # ... do other work ...
            agent.stop()
            thread.join()
            ```
        """
        if self._running:
            raise AlreadyRunningError("Agent is already running")

        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        """Stop the agent."""
        if self._running:
            logger.info(f"Stopping agent '{self.agent_id}'...")
            self._stop_event.set()

    # =========================================================================
    # Cleanup
    # =========================================================================

    def close(self) -> None:
        """Close the agent and release resources."""
        self.stop()
        if self._client:
            self._client.close()
            self._client = None

    async def aclose(self) -> None:
        """Async close the agent and release resources."""
        self.stop()
        if self._client:
            await self._client.aclose()
            self._client = None

    def __enter__(self) -> "Agent":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> "Agent":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
