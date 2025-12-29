# Fulcrum Python SDK

> Intelligent AI Governance for Enterprise Agents

[![PyPI version](https://badge.fury.io/py/fulcrum-governance.svg)](https://badge.fury.io/py/fulcrum-governance)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Installation

```bash
pip install fulcrum-governance
```

## Quick Start

```python
from fulcrum import FulcrumClient

# Initialize client
client = FulcrumClient(
    host="your-fulcrum-server:50051",
    api_key="your-api-key"
)

# Wrap agent executions in governance envelopes
with client.envelope(workflow_id="customer-support-bot") as env:
    # Check if action is allowed before executing
    if env.guard("send_email", input_text=user_message):
        # Action approved - proceed
        result = send_email(user_message)
        env.log("email_sent", {"recipient": email, "status": "success"})
    else:
        # Action blocked by policy
        env.log("action_blocked", {"reason": "policy_violation"})
```

## Features

- **Policy Enforcement**: Real-time governance checks before agent actions
- **Cost Tracking**: Monitor and control LLM spending per workflow
- **Audit Trail**: Complete execution history for compliance
- **Fail-Safe Modes**: Configurable FAIL_OPEN or FAIL_CLOSED behavior

## Documentation

Full documentation: [https://docs.fulcrum.dev](https://docs.fulcrum.dev)

## License

Apache 2.0
