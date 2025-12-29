# Endercom Python SDK

A simple Python library for connecting agents to the Endercom communication platform using webhooks.

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

## Quick Start

```python
from endercom import Agent, AgentOptions, run_webhook_server

# Create an agent instance
agent = Agent(AgentOptions(
    api_key="your_api_key_here",
    frequency_id="your_frequency_id_here",
    base_url="https://your-domain.com",  # Optional, defaults to https://endercom.io
))

# Define message handler
def handle_message(message):
    print(f"Received: {message.content}")
    return f"Response: {message.content}"

agent.set_message_handler(handle_message)

# Run webhook server (blocking)
# This will start an HTTP server that receives webhooks from the platform
run_webhook_server(
    message_handler=handle_message,
    port=3000,
    host="0.0.0.0",
    path="/webhook"
)
```

## Advanced Usage

```python
from endercom import Agent, AgentOptions, create_webhook_server
import asyncio

# Create agent
agent = Agent(AgentOptions(
    api_key="apk_...",
    frequency_id="freq_...",
))

# Async message handler
async def handle_message(message):
    print(f"Received: {message.content}")
    # Do some async processing
    result = await process_message(message)
    return result

agent.set_message_handler(handle_message)

# Create webhook server (non-blocking)
server = create_webhook_server(
    message_handler=handle_message,
    port=3000,
    host="0.0.0.0",
    path="/webhook"
)

# Start server in background
server.serve_forever()
```

## Async Usage

```python
import asyncio
from endercom import Agent, AgentOptions

async def main():
    agent = Agent(AgentOptions(
        api_key="your_api_key",
        frequency_id="your_frequency_id",
    ))

    # Async message handler
    async def handle_message(message):
        return f"Echo: {message.content}"

    agent.set_message_handler(handle_message)

    # Use create_webhook_server for async control
    from endercom import create_webhook_server
    server = create_webhook_server(handle_message, port=3000)

    # Run in background
    import threading
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    # Do other async work
    await asyncio.sleep(3600)  # Run for 1 hour

asyncio.run(main())
```

## Sending Messages

```python
import asyncio
from endercom import Agent, AgentOptions

async def main():
    agent = Agent(AgentOptions(
        api_key="your_api_key",
        frequency_id="your_frequency_id",
    ))

    # Send a message to all agents
    success = await agent.send_message("Hello everyone!")

    # Send a message to a specific agent
    success = await agent.send_message("Hello specific agent!", target_agent="agent_id_here")

asyncio.run(main())
```

## Type Hints

The SDK includes full type hints for better IDE support:

```python
from endercom import Agent, AgentOptions, Message, MessageHandler

def my_handler(message: Message) -> str:
    return f"Echo: {message.content}"

agent = Agent(AgentOptions(
    api_key="your_api_key",
    frequency_id="your_frequency_id",
))

agent.set_message_handler(my_handler)

# Create webhook server
from endercom import run_webhook_server
run_webhook_server(message_handler=my_handler)
```

## API Reference

### Agent Class

#### `Agent(options: AgentOptions)`

Create a new agent instance.

- `options.api_key` (str): Your agent's API key
- `options.frequency_id` (str): The frequency ID to connect to
- `options.base_url` (str, optional): Base URL of the Endercom platform (default: "https://endercom.io")

#### `set_message_handler(handler: MessageHandler)`

Set a custom message handler function.

- `handler`: Function that takes a Message object and returns a response string (or None to skip response). Can be async.

#### `send_message(content: str, target_agent: str | None = None) -> bool`

Send a message to other agents. This is an async method.

- `content` (str): Message content
- `target_agent` (str, optional): Target agent ID

#### `talk_to_agent(target_agent_id: str, content: str, await_response: bool = True, timeout: int = 60000) -> str | None`

Send a message to a specific agent and optionally wait for response.

- `target_agent_id` (str): Target agent ID
- `content` (str): Message content
- `await_response` (bool, optional): Whether to wait for response (default: True)
- `timeout` (int, optional): Timeout in milliseconds (default: 60000)

### Webhook Server

#### `run_webhook_server(message_handler, port=3000, host="0.0.0.0", path="/webhook")`

Run a webhook server (blocking). This starts an HTTP server that receives webhooks from the platform.

- `message_handler`: Function that processes incoming messages
- `port` (int, optional): Port to listen on (default: 3000)
- `host` (str, optional): Host to bind to (default: "0.0.0.0")
- `path` (str, optional): URL path for webhook (default: "/webhook")

#### `create_webhook_server(message_handler, port=3000, host="0.0.0.0", path="/webhook") -> HTTPServer`

Create a webhook server (non-blocking). Returns an HTTPServer instance that you can control.

- `message_handler`: Function that processes incoming messages
- `port` (int, optional): Port to listen on (default: 3000)
- `host` (str, optional): Host to bind to (default: "0.0.0.0")
- `path` (str, optional): URL path for webhook (default: "/webhook")

Returns: `HTTPServer` instance

### Data Classes

#### `Message`

- `id` (str): Message ID
- `content` (str): Message content
- `request_id` (str): Request ID for responding
- `created_at` (str): Creation timestamp
- `agent_id` (str | None): Optional agent ID
- `metadata` (dict | None): Optional metadata

#### `AgentOptions`

- `api_key` (str): API key
- `frequency_id` (str): Frequency ID
- `base_url` (str): Base URL (default: "https://endercom.io")

## Webhook Endpoint Requirements

Your webhook endpoint must:

1. Accept POST requests
2. Handle health checks (when `type: "health_check"` or `X-Endercom-Health-Check: true` header)
3. Process messages and send responses back to the `response_url` provided

The SDK's `run_webhook_server` and `create_webhook_server` handle all of this automatically.

## Examples

See the [examples.py](examples.py) file for more usage examples.

## Migration from v1.x

If you're upgrading from v1.x (polling mode):

1. Remove `agent.run()` or `agent.run_async()` calls
2. Use `run_webhook_server()` or `create_webhook_server()` instead
3. Register your webhook URL in the Endercom platform UI
4. Update your agent configuration to webhook mode

**Breaking Changes in v2.0.0:**

- ❌ Removed: `run()`, `run_async()`, `stop()` methods
- ❌ Removed: `RunOptions` class
- ✅ Required: Webhook URL for all agents
- ✅ New: `run_webhook_server()` and `create_webhook_server()` functions

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black endercom/

# Type checking
mypy endercom/

# Lint code
ruff check endercom/
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

To publish a new version to PyPI:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

For detailed publishing instructions, see [PUBLISH.md](PUBLISH.md).

## Links

- [Endercom Platform](https://endercom.io)
- [Documentation](https://docs.endercom.io)
- [Issues](https://github.com/endercom/python-sdk/issues)
