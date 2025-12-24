# agents-sdk-mutta

[![PyPI version](https://badge.fury.io/py/agents-sdk-mutta.svg)](https://badge.fury.io/py/agents-sdk-mutta)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20NC-orange.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)

A CLI scaffolding tool for OpenAI Agents SDK projects following the **Mutta** conventions.

Think of it like `django-admin` but for building agent services with the OpenAI Agents SDK.

## Installation

```bash
pip install agents-sdk-mutta
```

## Commands

### `mutta startproject`

Initializes a new agents project in the current directory:

- Creates `agents_sdk/` folder with a README explaining the structure
- Adds the 3 Mutta convention rules to your IDE's rules folder:
  - `openai-agents-sdk.mdc` - SDK overview and concepts
  - `agent-services.mdc` - Service building conventions
  - `agent-additional.mdc` - Advanced patterns and LiteLLM

**Rules folder priority:** `.cursor/rules/` > `.claude/rules/` > `.github/rules/`

```bash
mutta startproject
```

### `mutta startservice <name>`

Creates a new agent service following Mutta conventions:

```bash
mutta startservice research
# Creates: agents_sdk/research_agents/
```

This generates:

```
agents_sdk/research_agents/
├── __init__.py
├── manager.py          # Service orchestrator template
├── tools.py            # Shared tools (with guidance comments)
├── utilities.py        # Helper functions (with guidance comments)
└── agents/
    ├── __init__.py
    └── example_agent.py  # Example agent template
```

### Options

```bash
# Specify a different base directory
mutta startproject --path /path/to/project

# Create service with verbose output
mutta startservice my_service --verbose
```

## Mutta Conventions

The Mutta framework follows these key principles:

1. **Manager Pattern**: Every service has a manager that orchestrates agents in a linear flow
2. **One Agent Per File**: Each agent lives in its own file with clear structure
3. **Pydantic Everything**: Use Pydantic models for all inputs/outputs (never `Dict[str, Any]`)
4. **GPT-5 Series**: Prefer GPT-5 models with appropriate reasoning levels

## Development

```bash
# Clone and install in development mode
git clone https://github.com/maestromaximo/agent-sdk-mutta.git
cd agent-sdk-mutta
pip install -e ".[dev]"

# Run tests
pytest
```

## License

This project is licensed under the Polyform Noncommercial License 1.0.0. This means it can be used freely for non-commercial research and personal use, but requires a separate agreement for any commercial applications.

See [LICENSE](LICENSE) for the full license text.

