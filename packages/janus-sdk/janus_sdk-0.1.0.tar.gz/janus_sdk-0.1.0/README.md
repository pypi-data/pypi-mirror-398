# Janus Sentinel SDK

## Compliance & Policy Checks for AI Agents

Janus is the industry-standard SDK for ensuring AI agents comply with safety policies, regulatory requirements (SB-1047), and operational constraints. It provides a simple, high-performance interface for pre-action checks and post-action reporting.

### Installation

```bash
pip install janus-sdk
```

### Usage

#### Synchronous Client

```python
from janus import JanusClient

# Initialize client
client = JanusClient(
    tenant_id="your_tenant_id",
    api_key="janus_xyz",
    fail_open=False  # Default: fail closed on connection errors
)

# 1. Check if action is allowed
result = client.check(
    action="payment.process",
    params={"amount": 5000, "currency": "USD"},
    agent_id="payment-bot-01"
)

if result.allowed:
    # 2. Execute action
    process_payment(...)
    
    # 3. Report outcome
    client.report(
        result,
        status="success",
        result={"transaction_id": "tx_123"}
    )
elif result.requires_approval:
    print(f"Approval required: {result.reason}")
else:
    print(f"Action denied: {result.reason}")
```

#### Decorators (Easier Integration)

```python
from janus import JanusClient, janus_guard

client = JanusClient(...)

@janus_guard(client, action="email.send", agent_id="email-bot")
def send_email(to, subject, body):
    # This function is automatically guarded.
    # If policy check fails, it raises PermissionError.
    return mailer.send(to, subject, body)
```

### Async Support

Janus fully supports `async`/`await` for non-blocking operations:

```python
from janus import AsyncJanusClient

async with AsyncJanusClient(...) as client:
    res = await client.check("database.drop", params={"table": "users"})
    if not res.allowed:
        raise PermissionError(res.reason)
```

### License

MIT
