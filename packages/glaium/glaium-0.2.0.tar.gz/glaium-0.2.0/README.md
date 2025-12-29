# Glaium SDK

Python SDK for building autonomous agents that optimize toward organizational goals using the Glaium Optimizer.

[![PyPI version](https://badge.fury.io/py/glaium.svg)](https://badge.fury.io/py/glaium)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What's New in v0.1.10

- **Opt-in anonymization**: `anonymize` parameter added to `retrieve()` (default `False`)
- **De-anonymization support**: `deanonymize()` method in `DataClient` to reveal anonymized KPI values
- **Secure API routing**: SDK routes through the API gateway for proper authorization

See [CHANGELOG](https://bitbucket.org/glaium/sdk/src/master/CHANGELOG.md) for full release history.

## Installation

```bash
pip install glaium
```

## Quick Start

### High-Level Agent Framework

The easiest way to create an agent:

```python
from glaium import Agent

# Create an agent
agent = Agent(
    agent_id="sales-agent",
    declared_outputs=[{"name": "deals_closed"}],
)

# Handle optimization updates
@agent.on_optimization
def handle_optimization(optimization):
    print(f"Objectives: {optimization.objectives}")
    print(f"Constraints: {optimization.constraints}")

# Define your cycle logic
@agent.on_cycle
def run_cycle(ctx):
    # Your agent's work happens here
    deals = process_leads()

    return {
        "outputs": {"deals_closed": deals},
        "effectiveness": 0.75,
        "efficiency": 0.85,
    }

# Run the agent
agent.run()
```

### Low-Level Client

For more control, use the client directly:

```python
from glaium import Client, CycleEndEvent

# Create client (uses GLAIUM_API_KEY env var)
client = Client()

# Register your agent
registration = client.register(
    agent_id="my-agent",
    declared_inputs=[
        {"name": "leads", "source": {"agent": "marketing", "output": "qualified_leads"}}
    ],
    declared_outputs=[{"name": "deals_closed"}],
)

# Use the token for authenticated requests
agent_client = client.with_token(registration.agent_token)

# Get optimization (objectives, constraints, search space)
optimization = agent_client.get_optimization()
print(f"Target: {optimization.objectives[0].target}")

# Submit cycle results
agent_client.submit_event(CycleEndEvent(
    cycle_number=1,
    inputs={"leads": 100},
    outputs={"deals_closed": 15},
    effectiveness=0.75,
    efficiency=0.82,
))
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GLAIUM_API_KEY` | API key for authentication | (required) |
| `GLAIUM_BASE_URL` | Optimizer API base URL | `https://api.glaium.com` |

### Client Options

```python
from glaium import Client

client = Client(
    api_key="glaium_org123_ak_xxx",  # Or use env var
    base_url="https://api.glaium.com",
    max_retries=3,        # Retry failed requests
    retry_delay=1.0,      # Initial retry delay (seconds)
    retry_backoff=2.0,    # Exponential backoff multiplier
    timeout=30.0,         # Request timeout (seconds)
)
```

### Agent ID Naming Convention

The `agent_id` must be a **slug** - a URL-safe, lowercase identifier:

| ✅ Valid | ❌ Invalid |
|----------|-----------|
| `user-acquisition` | `User Acquisition` (spaces, uppercase) |
| `sales-agent` | `sales_agent` (underscores) |
| `monetization` | `Monetization!` (uppercase, special chars) |
| `retention-v2` | `retention v2` (spaces) |

**Rules:**
- Lowercase letters (`a-z`) and numbers (`0-9`) only
- Use hyphens (`-`) to separate words
- No spaces, underscores, or special characters
- Must be unique within your organization

### Agent Options

```python
from glaium import Agent

agent = Agent(
    agent_id="my-agent",          # Must be a slug (lowercase, hyphens)
    declared_inputs=[...],
    declared_outputs=[...],
    connections=[...],
    formula="output = input * rate",
    token_ttl_hours=48,           # Token validity
    poll_interval=60,             # Seconds between optimization polls
    default_cycle_interval=300,   # Default cycle interval if not set by optimizer
)
```

## Async Support

All methods have async variants:

```python
import asyncio
from glaium import Agent

agent = Agent(agent_id="async-agent", declared_outputs=[{"name": "result"}])

@agent.on_cycle
async def run_cycle(ctx):
    result = await process_async()
    return {"outputs": {"result": result}, "effectiveness": 0.9}

# Run async
asyncio.run(agent.run_async())
```

## Background Execution

Run the agent in a background thread:

```python
from glaium import Agent

agent = Agent(agent_id="background-agent", declared_outputs=[{"name": "result"}])

@agent.on_cycle
def run_cycle(ctx):
    return {"outputs": {"result": 42}, "effectiveness": 0.9}

# Start in background
thread = agent.start()

# Do other work...
import time
time.sleep(60)

# Stop the agent
agent.stop()
thread.join()
```

## Optimization Response

The optimizer provides objectives, constraints, and scheduling:

```python
@agent.on_optimization
def handle_optimization(opt):
    # Objectives - what to optimize toward
    for obj in opt.objectives:
        print(f"Metric: {obj.metric}, Target: {obj.target}, Operator: {obj.operator}")

    # Constraints - limits on behavior
    for constraint in opt.constraints:
        print(f"Constraint: {constraint.metric} {constraint.operator}")
        if constraint.is_bottleneck:
            print("  -> This agent is the system bottleneck!")

    # Search space - tunable parameter ranges
    for param, space in opt.search_space.items():
        print(f"Param: {param}, Range: [{space.min}, {space.max}]")

    # Scheduling
    if opt.next_cycle_at:
        print(f"Next cycle at: {opt.next_cycle_at}")
    elif opt.cycle_interval:
        print(f"Cycle every {opt.cycle_interval} seconds")
```

## Events

Submit different event types:

```python
from glaium import (
    CycleStartEvent,
    CycleEndEvent,
    CycleInterruptEvent,
    AnomalyEvent,
    HandsUpEvent,
)

# Cycle lifecycle
client.submit_event(CycleStartEvent(cycle_number=1))
client.submit_event(CycleEndEvent(
    cycle_number=1,
    inputs={"leads": 100},
    outputs={"deals": 15},
    effectiveness=0.75,
    efficiency=0.85,
))

# Interruption
client.submit_event(CycleInterruptEvent(
    cycle_number=1,
    reason="External API unavailable",
))

# Anomaly detection
client.submit_event(AnomalyEvent(
    metric="conversion_rate",
    expected=0.15,
    actual=0.05,
))

# Human escalation
client.submit_event(HandsUpEvent(
    severity="high",
    reason="Budget limit approaching",
    context={"current_spend": 9500, "limit": 10000},
    proposed_action={"pause_campaigns": ["camp_123"]},
))
```

## Optional Extras

Additional features available via `glaium.extras`:

### DataClient

Query metrics from the Data Service:

```python
from glaium.extras import DataClient

data = DataClient()

# Query metrics
result = await data.retrieve(
    organization_id=123,
    metrics=["spend", "installs", "cpi"],
    dimensions=["campaign_id"],
    period=["d-7", "d-1"],
)

# Convenience methods
campaigns = await data.get_campaign_performance(organization_id=123, days=7)
trends = await data.get_daily_trends(organization_id=123, metric="installs", days=14)
```

#### De-anonymization

Some KPIs return anonymized values (pattern: `{kpi}§§{hash}`) for privacy. Use `deanonymize()` to reveal original values:

```python
from glaium.extras import DataClient

data = DataClient(api_key="your-api-key")

# De-anonymize a string
text = "Revenue for app§§963D9D63B7701FC5 is $1000"
clear_text = await data.deanonymize(data=text)
# Returns: "Revenue for Contraction Tracker is $1000"

# De-anonymize query results
result = await data.retrieve(organization_id=123, metrics=["revenue"], dimensions=["app"])
clear_result = await data.deanonymize(data=result["data"])

# Sync version also available
clear_text = data.deanonymize_sync(data=text)
```

The organization is determined automatically from your API key, ensuring you can only de-anonymize your own organization's data.

### Memory

Persist context across cycles:

```python
from glaium.extras import Memory

memory = Memory(agent_id="my-agent", organization_id=123)

# Store memories
await memory.store(
    memory_type="decision",
    content="Increased bid by 15% due to high ROAS",
    importance=0.8,
    tags=["bid", "optimization"],
)

# Recall memories
past = await memory.recall(
    types=["decision", "outcome"],
    limit=10,
    min_importance=0.5,
)

# Build context for LLM
context = await memory.build_context()
```

### Verification

Risk-based decision verification:

```python
from glaium.extras import Verification, RiskLevel

verifier = Verification()

# Classify risk
risk = verifier.classify_risk(
    action_type="budget_change",
    parameters={"budget_change": 5000},
)

# Verify decision
result = await verifier.verify(
    prompt="Should we increase budget?",
    risk_level=risk,
)

if result.requires_human:
    # Escalate
    pass
```

### HandsUp

Human escalation helpers:

```python
from glaium.extras import HandsUp, HandsUpBuilder

# Raise directly
raise HandsUp(
    severity="high",
    category="low_confidence",
    reason="Cannot determine optimal action",
    proposed_action={"bid_change": 0.1},
)

# Use builder for common patterns
builder = HandsUpBuilder(agent_id="my-agent")

raise builder.low_confidence(confidence=0.45, decision="increase bid")
raise builder.budget_exceeded(current=95000, limit=100000, proposed_spend=8000)
raise builder.constraint_violated(constraint="CPI <= 2.50", actual_value=2.75)
```

## Error Handling

```python
from glaium import Client
from glaium.exceptions import (
    GlaiumError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
)

client = Client()

try:
    client.register(agent_id="my-agent", declared_outputs=[])
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except GlaiumError as e:
    print(f"Glaium error: {e}")
```

## Exception Hierarchy

```
GlaiumError
├── AuthenticationError
│   └── TokenExpiredError
├── APIError
│   ├── RateLimitError
│   ├── ServerError
│   ├── ValidationError
│   └── NotFoundError
├── AgentError
│   ├── NotRegisteredError
│   ├── AlreadyRunningError
│   └── CycleError
├── ConnectionError
└── TimeoutError
```

## Development

```bash
# Clone the repository
git clone git@bitbucket.org:glaium/sdk.git
cd sdk

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/glaium

# Linting
ruff check src/glaium
black src/glaium
```

## Releasing

The SDK uses automatic versioning from git tags. Version numbers are derived from tags (e.g., `v0.1.2` becomes version `0.1.2`).

### Release Workflow

1. **Develop and merge to master** - Regular pushes to master only run tests (no PyPI publish)

2. **When ready to release**, create and push a version tag:
   ```bash
   git tag v0.1.2
   git push --tags
   ```

3. **Pipeline auto-publishes** - Bitbucket Pipelines will:
   - Run tests
   - Build the package with the tag version
   - Publish to PyPI

### Version Format

Use semantic versioning: `vMAJOR.MINOR.PATCH`

- `v0.1.0` - Initial release
- `v0.1.1` - Patch/bugfix
- `v0.2.0` - New features (backward compatible)
- `v1.0.0` - Major release / breaking changes

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Issues: https://bitbucket.org/glaium/sdk/issues
- Email: support@glaium.com
