# agents-sdk-mutta

[![PyPI version](https://badge.fury.io/py/agents-sdk-mutta.svg)](https://pypi.org/project/agents-sdk-mutta/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20NC-orange.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)

**A CLI scaffolding tool for OpenAI Agents SDK projects following the Mutta conventions.**

Think of it like `django-admin` but for building multi-agent AI services with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python).

---

## Why Mutta?

Building production-ready multi-agent systems requires consistent patterns. Mutta provides:

- **Opinionated Structure** - No decision fatigue. One way to organize agents, tools, and services.
- **Manager Pattern** - Every service has a manager that orchestrates agents in predictable, linear workflows.
- **AI-First Rules** - Installs `.mdc` convention rules that AI coding assistants (Cursor, Claude, GitHub Copilot) understand.
- **Instant Scaffolding** - Go from zero to a working agent service in seconds.

---

## Quick Start

### Installation

```bash
pip install agents-sdk-mutta
```

### Initialize a Project

```bash
mutta startproject
```

This creates:
- `agents_sdk/` - Your agents directory with a README
- `.cursor/rules/` - Convention rules for AI assistants (or `.claude/rules/`, `.github/rules/`)

### Create a Service

```bash
mutta startservice research
```

This generates a complete service structure:

```
agents_sdk/research_agents/
|-- __init__.py
|-- manager.py           # Orchestrates the workflow
|-- tools.py             # Shared tools for agents
|-- utilities.py         # Helper functions
+-- agents/
    |-- __init__.py
    +-- example_agent.py # Template to get started
```

---

## Commands

| Command | Description |
|---------|-------------|
| `mutta startproject` | Initialize project with `agents_sdk/` folder and AI rules |
| `mutta startservice <name>` | Scaffold a new agent service |
| `mutta --help` | Show all available commands |

### Options

```bash
# Initialize in a specific directory
mutta startproject --path /path/to/project

# Verbose output when creating services
mutta startservice my_service --verbose
```

---

## The Mutta Conventions

### 1. Manager Pattern

Every service has a **Manager** class that orchestrates agents in a linear, predictable flow:

```python
class ResearchManager:
    async def run(self, query: str) -> ResearchReport:
        # Step 1: Plan the research
        plan = await Runner.run(planner_agent, query)
        
        # Step 2: Execute research
        findings = await Runner.run(researcher_agent, plan.output)
        
        # Step 3: Synthesize report
        report = await Runner.run(writer_agent, findings.output)
        
        return report.final_output
```

### 2. One Agent Per File

Each agent lives in its own file with a clear structure:

```python
# agents/planner_agent.py

PLANNER_INSTRUCTIONS = """
You are a research planning specialist...
"""

class PlanOutput(BaseModel):
    steps: list[str]
    focus_areas: list[str]

planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-5",
    output_type=PlanOutput
)
```

### 3. Pydantic Everything

All inputs and outputs use Pydantic models. Never use `Dict[str, Any]`:

```python
# Good
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

# Bad - Never do this
results: Dict[str, Any]
```

### 4. GPT-5 Series Models

Use GPT-5 models with appropriate reasoning levels:

| Use Case | Model | Reasoning |
|----------|-------|-----------|
| Complex planning | `gpt-5` | `high` |
| Standard tasks | `gpt-5` | `medium` |
| Simple extraction | `gpt-5-mini` | `low` |

---

## Installed Rules

When you run `mutta startproject`, these convention files are installed:

| File | Description |
|------|-------------|
| `openai-agents-sdk.mdc` | SDK overview, primitives, and concepts |
| `agent_services.mdc` | Service building conventions (the core rules) |
| `agent-additional.mdc` | Advanced patterns: streaming, LiteLLM, parallel execution |
| `mutta-cli.mdc` | How to use this CLI tool |

These rules are read by AI coding assistants to help you write code that follows Mutta conventions.

---

## Example: Building a Research Service

```bash
# 1. Initialize the project
mutta startproject

# 2. Create the research service
mutta startservice research

# 3. Edit the generated files
code agents_sdk/research_agents/
```

Then use your service:

```python
from agents_sdk.research_agents import ResearchManager

manager = ResearchManager()
report = await manager.run("What are the latest trends in quantum computing?")
print(report.summary)
```

---

## Development

```bash
# Clone the repository
git clone https://github.com/maestromaximo/agent-sdk-mutta.git
cd agent-sdk-mutta

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

---

## Requirements

- Python 3.10+
- Works with any project using the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)

---

## License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

- **Free** for personal use, research, education, and non-commercial projects
- **Commercial use** requires a separate license agreement

See [LICENSE](LICENSE) for the full text.

---

## Author

**Alejandro Garcia Polo**

- GitHub: [@maestromaximo](https://github.com/maestromaximo)
- Email: alejandrogarcia2423@hotmail.com

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
