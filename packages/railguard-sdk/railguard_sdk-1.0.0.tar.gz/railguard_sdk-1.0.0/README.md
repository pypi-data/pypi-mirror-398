# RailGuard Python SDK

Python SDK for RailGuard AI Guardrails - validate and secure your LLM applications.

## Installation

```bash
pip install railguard-sdk
```

## Usage

```python
from railguard import create_client

# Initialize client
client = create_client(
    api_key="your-api-key",
    base_url="https://railguardapi-production.up.railway.app"
)

# Validate AI output
response = client.validate({
    "text": "Your AI output text",
    "agentId": "your-agent-id",
    "rules": ["no-pii", "no-toxicity"]
})

print(response)

# Get rules
rules = client.get_rules(agent_id="your-agent-id")

# Get validation history
validations = client.get_validations(agent_id="your-agent-id", limit=10)
```

## API Reference

### `create_client(api_key, base_url)`

Creates a new RailGuard client instance.

- `api_key` (str): Your RailGuard API key
- `base_url` (str, optional): API base URL. Defaults to `http://localhost:3001`

### `client.validate(request)`

Validates text against configured rules.

- `request` (dict): Validation request object

Returns: Validation response with results

### `client.get_rules(agent_id=None)`

Retrieves rules for an agent.

- `agent_id` (str, optional): Filter by agent ID

Returns: List of rules

### `client.get_validations(agent_id=None, limit=None)`

Retrieves validation history.

- `agent_id` (str, optional): Filter by agent ID
- `limit` (int, optional): Maximum number of results

Returns: List of validation records

## License

MIT
