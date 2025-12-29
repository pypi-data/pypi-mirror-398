"""Configuration constants for the AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

# Default language model configuration
DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_AGENT_RUN_TIMEOUT = 300

# User agent and version
SDK_NAME = "glaip-sdk"

# Reserved names that cannot be used for agents/tools
RESERVED_NAMES = {
    "system",
    "admin",
    "root",
    "test",
    "example",
    "demo",
    "sample",
}

# Agent creation/update constants
DEFAULT_AGENT_TYPE = "config"
DEFAULT_AGENT_FRAMEWORK = "langchain"
DEFAULT_AGENT_VERSION = "1.0"
DEFAULT_AGENT_PROVIDER = "openai"

# Tool creation/update constants
DEFAULT_TOOL_TYPE = "custom"
DEFAULT_TOOL_FRAMEWORK = "langchain"
DEFAULT_TOOL_VERSION = "1.0"

# MCP creation/update constants
DEFAULT_MCP_TYPE = "server"
DEFAULT_MCP_TRANSPORT = "stdio"

# Default error messages
DEFAULT_ERROR_MESSAGE = "Unknown error"

# Agent configuration fields used for CLI args and payload building
AGENT_CONFIG_FIELDS = (
    "name",
    "instruction",
    "model",
    "tools",
    "agents",
    "mcps",
    "timeout",
)
