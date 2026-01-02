"""
Glaium SDK - Build autonomous agents that optimize toward organizational goals.

Core Usage:
    ```python
    from glaium import Client, Agent, Optimization

    # Low-level client
    client = Client()
    reg = client.register(agent_id="my-agent", declared_outputs=[{"name": "revenue"}])
    agent_client = client.with_token(reg.agent_token)
    optimization = agent_client.get_optimization()

    # High-level agent framework
    agent = Agent(agent_id="my-agent", declared_outputs=[{"name": "revenue"}])

    @agent.on_optimization
    def handle(opt):
        print(f"Objectives: {opt.objectives}")

    @agent.on_cycle
    def cycle(ctx):
        return {"outputs": {"revenue": 1000}, "effectiveness": 0.8}

    agent.run()
    ```

Optional Extras:
    ```python
    from glaium.extras import DataClient, Memory, Verification, HandsUp
    ```

Reasoners (for non-LLM agents):
    ```python
    from glaium.reasoners import AnalyticalReasoner, ReasonerOutput

    reasoner = AnalyticalReasoner(organization_id="org-123")
    result = reasoner.analyze(optimization=ctx.optimization, inputs=data)
    ```
"""

from glaium._version import __version__
from glaium.agent import Agent, CycleResult
from glaium.client import Client
from glaium.exceptions import (
    AgentError,
    AlreadyRunningError,
    APIError,
    AuthenticationError,
    ConnectionError,
    CycleError,
    GlaiumError,
    NotFoundError,
    NotRegisteredError,
    RateLimitError,
    ServerError,
    TimeoutError,
    TokenExpiredError,
    ValidationError,
)
from glaium.models import (
    AgentConnection,
    AgentInput,
    AgentOutput,
    AnomalyEvent,
    Constraint,
    CycleContext,
    CycleEndEvent,
    CycleInterruptEvent,
    CycleStartEvent,
    Event,
    EventResponse,
    HandsUpEvent,
    HandsUpSeverity,
    InventoryStatus,
    Objective,
    Optimization,
    RegistrationRequest,
    RegistrationResponse,
    SearchSpaceParam,
    UpstreamStatus,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "Client",
    "Agent",
    "CycleResult",
    # Models
    "Optimization",
    "Objective",
    "Constraint",
    "SearchSpaceParam",
    "UpstreamStatus",
    "InventoryStatus",
    "CycleContext",
    # Registration
    "AgentInput",
    "AgentOutput",
    "AgentConnection",
    "RegistrationRequest",
    "RegistrationResponse",
    # Events
    "Event",
    "EventResponse",
    "CycleStartEvent",
    "CycleEndEvent",
    "CycleInterruptEvent",
    "AnomalyEvent",
    "HandsUpEvent",
    "HandsUpSeverity",
    # Exceptions
    "GlaiumError",
    "AuthenticationError",
    "TokenExpiredError",
    "APIError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "NotFoundError",
    "AgentError",
    "NotRegisteredError",
    "AlreadyRunningError",
    "CycleError",
    "ConnectionError",
    "TimeoutError",
]
