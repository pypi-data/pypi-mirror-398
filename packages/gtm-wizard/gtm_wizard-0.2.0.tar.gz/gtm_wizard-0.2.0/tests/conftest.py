"""Pytest configuration for GTM Wizard MCP server testing."""

import pytest

# Import the decorated handler functions directly
from gtm_wizard.server import (
    call_tool,
    get_prompt,
    list_prompts,
    list_resources,
    list_tools,
    read_resource,
)


@pytest.fixture
def list_tools_handler():
    """Fixture providing the list_tools handler."""
    return list_tools


@pytest.fixture
def call_tool_handler():
    """Fixture providing the call_tool handler."""
    return call_tool


@pytest.fixture
def list_resources_handler():
    """Fixture providing the list_resources handler."""
    return list_resources


@pytest.fixture
def read_resource_handler():
    """Fixture providing the read_resource handler."""
    return read_resource


@pytest.fixture
def list_prompts_handler():
    """Fixture providing the list_prompts handler."""
    return list_prompts


@pytest.fixture
def get_prompt_handler():
    """Fixture providing the get_prompt handler."""
    return get_prompt


@pytest.fixture
def rate_limiting_input():
    """Fixture providing sample rate limiting diagnosis input."""
    return {
        "api_name": "HubSpot",
        "symptoms": "Getting 429 errors when syncing contacts",
    }
