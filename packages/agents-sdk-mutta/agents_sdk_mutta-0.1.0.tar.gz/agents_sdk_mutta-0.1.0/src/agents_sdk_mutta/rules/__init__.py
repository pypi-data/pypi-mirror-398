"""
Mutta convention rules for the OpenAI Agents SDK.

These .mdc rule files are installed to the IDE's rules directory during `mutta startproject`.
"""

from pathlib import Path

# Path to this rules directory
RULES_DIR = Path(__file__).parent

# Rule file names
RULE_FILES = [
    "openai-agents-sdk.mdc",
    "agent_services.mdc", 
    "agent-additional.mdc",
    "mutta-cli.mdc",
]


def get_rule_path(rule_name: str) -> Path:
    """Get the full path to a rule file."""
    return RULES_DIR / rule_name


def get_all_rules() -> list[tuple[str, Path]]:
    """Get all rule files as (filename, path) tuples."""
    return [(name, get_rule_path(name)) for name in RULE_FILES]


def read_rule(rule_name: str) -> str:
    """Read the content of a rule file."""
    rule_path = get_rule_path(rule_name)
    return rule_path.read_text(encoding="utf-8")

