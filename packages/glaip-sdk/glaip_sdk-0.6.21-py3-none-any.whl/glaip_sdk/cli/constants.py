"""CLI-specific constants for glaip-sdk.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

# Minimum length that forces multiline YAML strings to be rendered using the literal
# block style. This prevents long prompts and instructions from being inlined.
LITERAL_STRING_THRESHOLD = 200

# Masking configuration
MASKING_ENABLED = True
MASK_SENSITIVE_FIELDS = {
    "api_key",
    "apikey",
    "token",
    "access_token",
    "secret",
    "client_secret",
    "password",
    "private_key",
    "bearer",
}

# Table + pager behaviour
TABLE_SORT_ENABLED = True
PAGER_MODE = "auto"  # valid values: "auto", "on", "off"
PAGER_WRAP_LINES = False
PAGER_HEADER_ENABLED = True

# Update notification toggle
UPDATE_CHECK_ENABLED = True

# Agent instruction preview defaults
DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT = 800

# Remote runs defaults
DEFAULT_REMOTE_RUNS_PAGE_LIMIT = 20
