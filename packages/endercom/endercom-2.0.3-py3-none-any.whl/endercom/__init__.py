"""
Endercom Python SDK

A simple Python library for connecting agents to the Endercom communication platform,
with support for both client-side polling and server-side wrapper functionality.
"""

from .agent import Agent, Message, AgentOptions, RunOptions, ServerOptions, MessageHandler
from .agent import create_agent, create_server_agent

__version__ = "2.0.3"
__all__ = [
    "Agent",
    "Message",
    "AgentOptions",
    "RunOptions",
    "ServerOptions",
    "MessageHandler",
    "create_agent",
    "create_server_agent"
]

