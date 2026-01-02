"""
Callbotics SDK - Official Python SDK for Callbotics Voice AI Platform

This SDK provides a simple, intuitive interface for creating and managing
voice AI bots using the Callbotics platform.

Quick Start:
    >>> from callbotics_sdk import CallboticsClient
    >>>
    >>> # Initialize client (uses https://api.callbotics.ai by default)
    >>> client = CallboticsClient()
    >>> client.login("user@example.com", "password")
    >>>
    >>> # Create a complete bot in one line
    >>> bot = client.create_complete_bot(
    ...     name="Support Bot",
    ...     llm_api_key="your-openai-key",
    ...     prompt_background="You are a helpful support agent",
    ...     voice_api_key="your-rime-key",
    ...     transcriber_api_key="your-deepgram-key",
    ...     telephony_auth_token="your-telnyx-token",
    ...     telephony_connection_id="your-connection-id"
    ... )
    >>>
    >>> # Make a call
    >>> call = client.calls.create(
    ...     agent_id=bot["agent"]["id"],
    ...     to_number="+15551234567"
    ... )
"""

__version__ = "1.0.0"
__author__ = "Callbotics"

from .client import CallboticsClient
from .exceptions import (
    CallboticsException,
    AuthenticationError,
    APIError,
    ResourceNotFoundError,
    ValidationError,
    ConfigurationError,
    RateLimitError,
)

__all__ = [
    "CallboticsClient",
    "CallboticsException",
    "AuthenticationError",
    "APIError",
    "ResourceNotFoundError",
    "ValidationError",
    "ConfigurationError",
    "RateLimitError",
]
