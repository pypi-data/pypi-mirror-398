"""
Endercom Agent for Python

This module provides a simple interface for connecting Python agents
to the Endercom communication platform, with support for both client-side
polling and server-side wrapper functionality with heartbeat and a2a endpoints.
"""

import asyncio
import logging
import signal
import sys
import time
import os
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx is required. Install it with: pip install httpx"
    )

# Optional FastAPI support for server wrapper functionality
try:
    from fastapi import FastAPI, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message object received from the Endercom platform."""
    id: str
    content: str
    request_id: str
    created_at: str
    agent_id: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class AgentOptions:
    """Configuration options for an Agent."""
    frequency_api_key: str
    frequency_id: str
    agent_id: str
    base_url: str = "https://endercom.io"


@dataclass
class RunOptions:
    """Options for running the agent."""
    poll_interval: float = 2.0  # seconds


@dataclass
class ServerOptions:
    """Configuration options for server wrapper functionality."""
    host: str = "0.0.0.0"
    port: int = 8000
    enable_heartbeat: bool = True
    enable_a2a: bool = True
    frequency_api_key: Optional[str] = None  # For authentication


# Server request/response models (only available when FastAPI is installed)
if FASTAPI_AVAILABLE:
    class A2ARequest(BaseModel):
        """Request model for agent-to-agent communication."""
        content: Optional[str] = None
        message: Optional[str] = None

        def get_content(self) -> str:
            """Get the message content from either field."""
            return self.content or self.message or ""

    class HealthResponse(BaseModel):
        """Response model for health check."""
        status: str
        timestamp: str
        uptime_seconds: Optional[float] = None


MessageHandler = Callable[[Message], Optional[str]]


class Agent:
    """
    Endercom Agent for Python

    This class provides a simple interface for connecting Python agents
    to the Endercom communication platform, with support for both client-side
    polling and server-side wrapper functionality.
    """

    def __init__(self, options: AgentOptions):
        """
        Initialize a new Agent instance.

        Args:
            options: Agent configuration options
        """
        self.frequency_api_key = options.frequency_api_key
        self.frequency_id = options.frequency_id
        self.agent_id = options.agent_id
        self.base_url = options.base_url.rstrip('/')
        self.freq_base = f"{self.base_url}/api/{self.frequency_id}"
        self.message_handler: Optional[MessageHandler] = None
        self.running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None

        # Server wrapper properties
        self._app: Optional[FastAPI] = None
        self._startup_time: Optional[float] = None

    def set_message_handler(self, handler: MessageHandler) -> None:
        """
        Set a custom message handler function.

        Args:
            handler: Function that takes a message object and returns a response string
        """
        self.message_handler = handler

    def _default_message_handler(self, message: Message) -> str:
        """
        Default message handler that echoes the received message.

        Args:
            message: The received message

        Returns:
            Response string
        """
        logger.info(f"received: {message.content}")
        return f"Echo: {message.content}"

    async def _poll_messages(self) -> None:
        """Internal method to poll for messages."""
        if not self._client:
            return

        try:
            response = await self._client.get(
                f"{self.freq_base}/messages/poll",
                headers={
                    "Authorization": f"Bearer {self.frequency_api_key}",
                    "Content-Type": "application/json",
                    "X-Agent-Id": self.agent_id
                }
            )

            if response.is_success:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("messages"):
                    messages = data["data"]["messages"]
                    for msg_data in messages:
                        message = Message(
                            id=msg_data["id"],
                            content=msg_data["content"],
                            request_id=msg_data["request_id"],
                            created_at=msg_data["created_at"],
                            agent_id=msg_data.get("agent_id"),
                            metadata=msg_data.get("metadata") or {}
                        )
                        await self._handle_message(message)
            else:
                logger.error(f"Polling error: {response.status_code}")
        except Exception as error:
            logger.error(f"Network error: {error}", exc_info=True)

    async def _handle_message(self, message: Message) -> None:
        """
        Handle a received message.

        Args:
            message: The message to handle
        """
        try:
            # Use custom handler if set, otherwise use default
            handler = self.message_handler or self._default_message_handler
            response_content = handler(message)

            # Check if handler is async (returns a coroutine)
            if asyncio.iscoroutine(response_content):
                response_content = await response_content

            # If handler returns None, skip sending response
            if response_content is None:
                return

            # Check if there's a response_url in metadata (for talk endpoint)
            if message.metadata and message.metadata.get("response_url"):
                await self._respond_via_http(
                    message.metadata["response_url"],
                    message.metadata.get("request_id", message.request_id),
                    response_content
                )
            else:
                # Send response via normal message queue
                await self._respond_to_message(message.request_id, response_content)
        except Exception as error:
            logger.error(f"Error handling message: {error}", exc_info=True)

    async def _respond_via_http(self, response_url: str, request_id: str, content: str) -> None:
        """
        Send a response via HTTP POST to a response URL (for talk endpoint).

        Args:
            response_url: The URL to POST the response to
            request_id: The request ID
            content: The response content
        """
        if not self._client:
            return

        try:
            payload = {
                "request_id": request_id,
                "content": content
            }

            response = await self._client.post(
                response_url,
                headers={
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if not response.is_success:
                logger.error(f"HTTP response error: {response.status_code}")
        except Exception as error:
            logger.error(f"Network error sending HTTP response: {error}", exc_info=True)

    async def _respond_to_message(self, request_id: str, content: str) -> None:
        """
        Send a response to a message.

        Args:
            request_id: The request ID to respond to
            content: The response content
        """
        if not self._client:
            return

        try:
            payload = {
                "request_id": request_id,
                "content": content
            }

            response = await self._client.post(
                f"{self.freq_base}/messages/respond",
                headers={
                    "Authorization": f"Bearer {self.frequency_api_key}",
                    "Content-Type": "application/json",
                    "X-Agent-Id": self.agent_id
                },
                json=payload
            )

            if not response.is_success:
                logger.error(f"Response error: {response.status_code}")
        except Exception as error:
            logger.error(f"Network error sending response: {error}", exc_info=True)

    async def send_message(self, content: str, target_agent_id: Optional[str] = None) -> bool:
        """
        Send a message to other agents.

        Args:
            content: Message content
            target_agent_id: Target agent ID (optional, for routing to specific agent)

        Returns:
            True if successful, False otherwise
        """
        # Use existing client if available, otherwise create a temporary one
        if self._client:
            client = self._client
            should_close = False
        else:
            client = httpx.AsyncClient(timeout=30.0)
            should_close = True

        try:
            payload = {"content": content}

            if target_agent_id:
                payload["target_agent"] = target_agent_id

            response = await client.post(
                f"{self.freq_base}/messages/send",
                headers={
                    "Authorization": f"Bearer {self.frequency_api_key}",
                    "Content-Type": "application/json",
                    "X-Agent-Id": self.agent_id
                },
                json=payload
            )

            return response.is_success
        except Exception as error:
            logger.error(f"Error sending message: {error}", exc_info=True)
            return False
        finally:
            if should_close:
                await client.aclose()

    async def talk_to_agent(
        self,
        target_agent_id: str,
        content: str,
        await_response: bool = True,
        timeout: int = 60000
    ) -> Optional[str]:
        """
        Send a message to a specific agent using the talk endpoint and optionally wait for response.

        Args:
            target_agent_id: Target agent ID (user-provided identifier)
            content: Message content
            await_response: Whether to wait for response (default: True)
            timeout: Timeout in milliseconds (default: 60000 = 60 seconds)

        Returns:
            Response content if await_response is True, None otherwise
        """
        # Use existing client if available, otherwise create a temporary one
        if self._client:
            client = self._client
            should_close = False
        else:
            client = httpx.AsyncClient(timeout=float(timeout) / 1000 + 10)  # Add buffer for timeout
            should_close = True

        try:
            payload = {
                "content": content,
                "await": await_response,
                "timeout": timeout
            }

            response = await client.post(
                f"{self.base_url}/api/{self.frequency_id}/agents/{target_agent_id}/talk",
                headers={
                    "Authorization": f"Bearer {self.frequency_api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if not response.is_success:
                logger.error(f"Talk endpoint error: {response.status_code}")
                return None

            data = response.json()
            if not data.get("success"):
                logger.error(f"Talk endpoint error: {data.get('error')}")
                return None

            # If await_response is True, return the response content
            if await_response and data.get("data", {}).get("response"):
                return data["data"]["response"]["content"]

            return None
        except Exception as error:
            logger.error(f"Error talking to agent: {error}", exc_info=True)
            return None
        finally:
            if should_close:
                await client.aclose()

    async def _poll_loop(self, poll_interval: float) -> None:
        """Internal polling loop."""
        while self.running:
            await self._poll_messages()
            await asyncio.sleep(poll_interval)

    def run(self, options: Optional[RunOptions] = None) -> None:
        """
        Start the agent polling loop.

        Args:
            options: Configuration options
        """
        if self.running:
            logger.warning("Agent is already running")
            return

        run_options = options or RunOptions()
        poll_interval = run_options.poll_interval
        self.running = True

        logger.info(f"Agent started, polling every {poll_interval}s")
        logger.info("Press Ctrl+C to stop")

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Create async client and run
        async def main():
            async with httpx.AsyncClient(timeout=30.0) as client:
                self._client = client
                self._poll_task = asyncio.create_task(
                    self._poll_loop(poll_interval)
                )
                try:
                    await self._poll_task
                except asyncio.CancelledError:
                    pass

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stop()

    async def run_async(self, options: Optional[RunOptions] = None) -> None:
        """
        Start the agent polling loop asynchronously (for use in existing async contexts).

        Args:
            options: Configuration options
        """
        if self.running:
            logger.warning("Agent is already running")
            return

        run_options = options or RunOptions()
        poll_interval = run_options.poll_interval
        self.running = True

        logger.info(f"Agent started, polling every {poll_interval}s")

        async with httpx.AsyncClient(timeout=30.0) as client:
            self._client = client
            self._poll_task = asyncio.create_task(
                self._poll_loop(poll_interval)
            )
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

    def stop(self) -> None:
        """Stop the agent polling loop."""
        if not self.running:
            return

        self.running = False
        if self._poll_task:
            self._poll_task.cancel()

        logger.info("Agent stopped")

    # Server wrapper functionality
    async def _authenticate_frequency(
        self, authorization: Optional[str] = Header(None, alias="Authorization")
    ) -> str:
        """
        FastAPI dependency to authenticate requests using frequency API key.

        Expects: Authorization: Bearer {frequency_api_key}

        Raises:
            HTTPException(401): If authentication fails
        """
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Missing Authorization header. Provide: Authorization: Bearer {frequency_api_key}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract the API key from "Bearer {key}" format
        parts = authorization.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format. Use: Bearer {frequency_api_key}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        api_key = parts[1].strip()
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is empty",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Simple API key validation - just check if it matches the configured key
        if api_key != self.frequency_api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid frequency API key.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return api_key

    def create_server_wrapper(self, server_options: ServerOptions) -> "FastAPI":
        """
        Create a FastAPI server wrapper that exposes heartbeat and a2a endpoints.

        Args:
            server_options: Server configuration options

        Returns:
            FastAPI application instance

        Raises:
            ImportError: If FastAPI dependencies are not installed
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI dependencies are required for server wrapper functionality. "
                "Install them with: pip install fastapi uvicorn pydantic"
            )

        self._startup_time = time.time()
        self._app = FastAPI(
            title=f"Endercom Agent - {self.frequency_id}",
            description="Agent wrapper with heartbeat and a2a endpoints",
            version="1.0.0",
        )

        # Store server options for endpoints
        self._server_options = server_options

        # Add heartbeat endpoint if enabled
        if server_options.enable_heartbeat:
            @self._app.get("/health", response_model=HealthResponse)
            @self._app.get("/heartbeat", response_model=HealthResponse)
            async def health_check(_: str = Depends(self._authenticate_frequency)):
                """Health check endpoint to verify the service is running."""
                uptime = time.time() - self._startup_time if self._startup_time else 0
                return HealthResponse(
                    status="healthy",
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                    uptime_seconds=round(uptime, 2),
                )

        # Add a2a endpoint if enabled
        if server_options.enable_a2a:
            @self._app.post("/a2a")
            async def a2a_endpoint(
                request: A2ARequest,
                _: str = Depends(self._authenticate_frequency)
            ):
                """
                Agent-to-agent communication endpoint.

                Accepts a request with either 'content' or 'message' field containing
                the message to process.
                """
                content = request.get_content()
                if not content:
                    raise HTTPException(
                        status_code=400,
                        detail="Either 'content' or 'message' field is required in the request body"
                    )

                try:
                    # Create a mock message for processing
                    mock_message = Message(
                        id=f"a2a_{int(time.time() * 1000)}",
                        content=content,
                        request_id=f"a2a_req_{int(time.time() * 1000)}",
                        created_at=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                        agent_id=None,
                        metadata={}
                    )

                    # Process with message handler
                    handler = self.message_handler or self._default_message_handler
                    response_content = handler(mock_message)

                    # Handle async handlers
                    if asyncio.iscoroutine(response_content):
                        response_content = await response_content

                    return JSONResponse(content={
                        "success": True,
                        "response": response_content,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
                    })
                except Exception as error:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Message processing failed: {str(error)}"
                    ) from error

        # Add root endpoint with service information
        @self._app.get("/")
        async def root(_: str = Depends(self._authenticate_frequency)):
            """Root endpoint with service information."""
            return {
                "service": f"Endercom Agent - {self.agent_id}",
                "version": "1.0.0",
                "status": "running",
                "agent_id": self.agent_id,
                "frequency_id": self.frequency_id,
                "endpoints": {
                    "health": "/health or /heartbeat" if server_options.enable_heartbeat else "disabled",
                    "a2a": "POST /a2a" if server_options.enable_a2a else "disabled",
                },
                "base_url": self.base_url,
                "authentication": "All endpoints require frequency API key in Authorization header",
            }

        return self._app

    def run_server(self, server_options: ServerOptions) -> None:
        """
        Run the agent as a server wrapper with heartbeat and a2a endpoints.

        Args:
            server_options: Server configuration options
        """
        app = self.create_server_wrapper(server_options)

        logger.info(f"Starting Endercom Agent server wrapper")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"Frequency ID: {self.frequency_id}")
        logger.info(f"Frequency ID: {self.frequency_id}")
        logger.info(f"Host: {server_options.host}")
        logger.info(f"Port: {server_options.port}")
        logger.info(f"Heartbeat endpoint: {'enabled' if server_options.enable_heartbeat else 'disabled'}")
        logger.info(f"A2A endpoint: {'enabled' if server_options.enable_a2a else 'disabled'}")

        uvicorn.run(app, host=server_options.host, port=server_options.port)


def create_agent(options: AgentOptions) -> Agent:
    """
    Create a new Endercom agent.

    Args:
        options: Agent configuration options

    Returns:
        Agent instance
    """
    return Agent(options)


def create_server_agent(
    agent_options: AgentOptions,
    server_options: ServerOptions,
    message_handler: Optional[MessageHandler] = None
) -> Agent:
    """
    Create a new Endercom agent configured for server wrapper functionality.

    Args:
        agent_options: Agent configuration options
        server_options: Server configuration options
        message_handler: Optional message handler function

    Returns:
        Agent instance configured for server wrapper

    Raises:
        ImportError: If FastAPI dependencies are not installed
    """
    agent = Agent(agent_options)
    if message_handler:
        agent.set_message_handler(message_handler)
    return agent

