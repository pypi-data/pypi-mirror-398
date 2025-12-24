"""README template for agents_sdk folder."""

AGENTS_SDK_README = '''# agents_sdk/

This folder contains all agent services for this project, following the **Mutta** conventions.

## Structure

Each service follows this pattern:

```
agents_sdk/
├── {service_name}_agents/
│   ├── __init__.py              # Package exports
│   ├── manager.py               # Main orchestrator (REQUIRED)
│   ├── agents/                  # All agent definitions
│   │   ├── __init__.py
│   │   └── {role}_agent.py      # One agent per file
│   ├── tools.py                 # Optional: Shared tools
│   └── utilities.py             # Optional: Helper functions
```

## Creating a New Service

Use the Mutta CLI:

```bash
mutta startservice <name>
```

Example:
```bash
mutta startservice research
# Creates: agents_sdk/research_agents/
```

## Key Conventions

1. **Manager Pattern**: Every service has a manager that orchestrates agents linearly
2. **One Agent Per File**: Each agent lives in its own file
3. **Pydantic Models**: Use Pydantic for all inputs/outputs (never `Dict[str, Any]`)
4. **GPT-5 Series**: Prefer GPT-5 models with appropriate reasoning levels

## Example Usage

```python
from agents_sdk.research_agents import ResearchManager

manager = ResearchManager()
result = await manager.run("Research quantum computing trends")
print(result)
```

## Learn More

Check the rules in your IDE's rules folder for detailed conventions:
- `openai-agents-sdk.mdc` - SDK overview
- `agent-services.mdc` - Service conventions  
- `agent-additional.mdc` - Advanced patterns
'''

