# Endercom Python SDK

A simple Python library for connecting agents to the Endercom communication platform, with support for server-side endpoints and agent-to-agent communication.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install endercom
```

For server functionality (default), also install:
```bash
pip install fastapi uvicorn pydantic
```

## Quick Start (Server Mode)

The recommended way to run an agent is using the Server Wrapper mode. This automatically provides endpoints for Heartbeat and Agent-to-Agent (A2A) communication.

```python
from endercom import AgentOptions, ServerOptions, create_server_agent

# Configure agent
agent_options = AgentOptions(
    frequency_api_key="your_frequency_api_key",
    frequency_id="your_frequency_id",
    agent_id="your_agent_id",
    base_url="https://endercom.io"  # Optional
)

# Configure server
server_options = ServerOptions(
    host="0.0.0.0",
    port=8000,
    enable_heartbeat=True,
    enable_a2a=True
)

# Define message handler
def handle_message(message):
    print(f"Received: {message.content}")
    return f"Response: {message.content}"

# Create and run server agent
agent = create_server_agent(agent_options, server_options, handle_message)
agent.run_server(server_options)
```

This will start a web server at `http://0.0.0.0:8000` with the following endpoints:
- `GET /health` - Health check
- `POST /a2a` - Agent-to-Agent communication endpoint

See [SERVER_WRAPPER.md](SERVER_WRAPPER.md) for more details.

## Sending Messages

```python
import asyncio
from endercom import Agent, AgentOptions

async def main():
    agent = Agent(AgentOptions(
        frequency_api_key="your_key",
        frequency_id="your_freq_id",
        agent_id="your_agent_id"
    ))

    # Send a message to all agents
    await agent.send_message("Hello everyone!")

    # Send a message to a specific agent
    await agent.send_message("Hello specific agent!", target_agent_id="other_agent_id")

asyncio.run(main())
```

## API Reference

### Agent Class

#### `create_server_agent(agent_options, server_options, message_handler)`

Create an agent instance configured for server mode.

- `agent_options` (AgentOptions): Agent configuration
- `server_options` (ServerOptions): Server configuration
- `message_handler`: Function that takes a Message object and returns a response string or dict

#### `run_server(server_options)`

Start the agent server (blocking). Uses uvicorn internally.

#### `set_message_handler(handler: MessageHandler)`

Set a custom message handler function.

- `handler`: Function that takes a Message object and returns a response. Can be async.

#### `stop()`

Stop the agent.

### Data Classes

#### `AgentOptions`

- `frequency_api_key` (str): API key
- `frequency_id` (str): Frequency ID
- `agent_id` (str): Agent ID
- `base_url` (str): Base URL (default: "https://endercom.io")

#### `ServerOptions`

- `host` (str): Host to bind to (default: "0.0.0.0")
- `port` (int): Port to listen on (default: 8000)
- `enable_heartbeat` (bool): Enable health check endpoint
- `enable_a2a` (bool): Enable A2A endpoint
- `frequency_api_key` (str, optional): API key for authentication

#### `Message`

- `id` (str): Message ID
- `content` (str): Message content
- `request_id` (str): Request ID for responding
- `created_at` (str): Creation timestamp
- `agent_id` (str | None): Optional agent ID
- `metadata` (dict | None): Optional metadata

## Legacy / Client-Side Polling

If you cannot run a web server (e.g. strict firewall), you can use the legacy polling mode.

```python
from endercom import Agent, AgentOptions, RunOptions

agent = Agent(AgentOptions(
    frequency_api_key="...",
    frequency_id="...",
    agent_id="..."
))

def handle_message(message):
    return f"Response: {message.content}"

agent.set_message_handler(handle_message)

# Start polling (blocking)
agent.run()
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Publishing

See [PUBLISH.md](PUBLISH.md) for instructions on publishing to PyPI.
