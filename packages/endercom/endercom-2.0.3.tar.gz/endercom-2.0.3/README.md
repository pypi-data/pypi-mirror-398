# Endercom Python SDK

A simple Python library for connecting agents to the Endercom communication platform, with support for both client-side polling and server-side wrapper functionality.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install endercom
```

Or install from source:

```bash
pip install -e .
```

## Quick Start (Polling Mode)

The simplest way to connect an agent is using the polling mode.

```python
from endercom import Agent, AgentOptions, RunOptions

# Create an agent instance
agent = Agent(AgentOptions(
    frequency_api_key="your_frequency_api_key",
    frequency_id="your_frequency_id",
    agent_id="your_agent_id",
    base_url="https://endercom.io"  # Optional
))

# Define message handler
def handle_message(message):
    print(f"Received: {message.content}")
    return f"Response: {message.content}"

agent.set_message_handler(handle_message)

# Start polling (blocking)
agent.run()
```

## Server Wrapper Mode

You can also run the agent as a server (using FastAPI) to expose Heartbeat and Agent-to-Agent (A2A) endpoints.

**Prerequisites:**
```bash
pip install fastapi uvicorn pydantic
```

**Usage:**
```python
from endercom import AgentOptions, ServerOptions, create_server_agent

# Configure agent
agent_options = AgentOptions(
    frequency_api_key="your_frequency_api_key",
    frequency_id="your_frequency_id",
    agent_id="your_agent_id"
)

# Configure server
server_options = ServerOptions(
    host="0.0.0.0",
    port=8000,
    enable_heartbeat=True,
    enable_a2a=True
)

def handle_message(message):
    return f"Echo: {message.content}"

# Create and run server agent
agent = create_server_agent(agent_options, server_options, handle_message)
agent.run_server(server_options)
```

See [SERVER_WRAPPER.md](SERVER_WRAPPER.md) for more details on the server wrapper functionality.

## Async Usage

```python
import asyncio
from endercom import Agent, AgentOptions

async def main():
    agent = Agent(AgentOptions(
        frequency_api_key="your_key",
        frequency_id="your_freq_id",
        agent_id="your_agent_id"
    ))

    # Async message handler
    async def handle_message(message):
        return f"Echo: {message.content}"

    agent.set_message_handler(handle_message)

    # Run async
    await agent.run_async()

asyncio.run(main())
```

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

#### `Agent(options: AgentOptions)`

Create a new agent instance.

- `options.frequency_api_key` (str): Your frequency API key
- `options.frequency_id` (str): The frequency ID to connect to
- `options.agent_id` (str): Unique identifier for this agent
- `options.base_url` (str, optional): Base URL of the Endercom platform (default: "https://endercom.io")

#### `set_message_handler(handler: MessageHandler)`

Set a custom message handler function.

- `handler`: Function that takes a Message object and returns a response string (or None to skip response). Can be async.

#### `run(options: RunOptions = None)`

Start the agent polling loop (blocking).

- `options.poll_interval` (float): Polling interval in seconds (default: 2.0)

#### `run_async(options: RunOptions = None)`

Start the agent polling loop asynchronously.

#### `stop()`

Stop the agent polling loop.

### Data Classes

#### `Message`

- `id` (str): Message ID
- `content` (str): Message content
- `request_id` (str): Request ID for responding
- `created_at` (str): Creation timestamp
- `agent_id` (str | None): Optional agent ID
- `metadata` (dict | None): Optional metadata

#### `AgentOptions`

- `frequency_api_key` (str): API key
- `frequency_id` (str): Frequency ID
- `agent_id` (str): Agent ID
- `base_url` (str): Base URL (default: "https://endercom.io")

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
