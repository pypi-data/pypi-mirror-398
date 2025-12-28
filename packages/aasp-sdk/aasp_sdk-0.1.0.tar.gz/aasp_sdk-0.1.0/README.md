# AASP SDK

Official Python SDK for the AI Agent Security Platform (AASP).

Secure what your AI agents do, not just what they can access.

## Installation

```bash
pip install aasp-sdk
```

## Quick Start

```python
from aasp import AASPCallback
from langchain.agents import AgentExecutor

# Add AASP protection to your LangChain agent
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[AASPCallback(api_key="aasp_live_xxx")]
)

# All tool calls are now monitored!
executor.invoke({"input": "Process the invoice"})
```

## Features

- **Real-time Interception** - Catch every action before it executes
- **Policy Engine** - Define rules with regex patterns and conditions
- **Human-in-the-Loop** - Require approval for sensitive operations
- **Complete Audit Trail** - Log every action for compliance

## Documentation

Full documentation at [https://aasp-mvp.aminereg.com/docs](https://aasp-mvp.aminereg.com/docs)

## Requirements

- Python 3.10+
- httpx

## License

MIT
