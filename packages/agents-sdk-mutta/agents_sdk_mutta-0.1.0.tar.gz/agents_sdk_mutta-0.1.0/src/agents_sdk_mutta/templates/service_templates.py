"""Templates for agent service files."""


def get_init_template(service_name: str) -> str:
    """Generate __init__.py for a service."""
    base_name = service_name.replace("_agents", "")
    class_name = "".join(word.title() for word in base_name.split("_")) + "Manager"
    
    return f'''"""
{service_name} - Agent service following Mutta conventions.

Usage:
    from agents_sdk.{service_name} import {class_name}
    
    manager = {class_name}()
    result = await manager.run("your request")
"""

from .manager import {class_name}

__all__ = ["{class_name}"]
'''


def get_manager_template(service_name: str, base_name: str) -> str:
    """Generate manager.py template."""
    class_name = "".join(word.title() for word in base_name.split("_")) + "Manager"
    
    return f'''"""
{class_name} - Orchestrates the {base_name} service workflow.

This is the main entry point for the service. It coordinates agents
in a linear, predictable flow following Mutta conventions.
"""

from __future__ import annotations

import asyncio
from typing import Optional, Callable, Any

from agents import Runner, trace, gen_trace_id

# Import your agents here
# from .agents.planner_agent import planner_agent, PlanOutput
# from .agents.executor_agent import executor_agent


class {class_name}:
    """
    Orchestrates the complete {base_name} workflow.
    
    Follows the Manager pattern:
    1. Each phase runs sequentially
    2. Clear progress tracking
    3. Error handling at each phase
    """
    
    def __init__(self):
        """Initialize the manager with any shared resources."""
        pass
    
    async def run(
        self,
        user_request: str,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> Any:
        """
        Main orchestration method.
        
        Args:
            user_request: The user's input request
            progress_callback: Optional callback(phase, progress_pct, message)
        
        Returns:
            The final structured output from the workflow
        """
        trace_id = gen_trace_id()
        
        with trace("{class_name} Workflow", trace_id=trace_id):
            # Phase 1: Planning
            if progress_callback:
                progress_callback("Planning", 25, "Analyzing request...")
            # plan = await self._plan(user_request)
            
            # Phase 2: Execution
            if progress_callback:
                progress_callback("Executing", 50, "Processing...")
            # results = await self._execute(plan)
            
            # Phase 3: Output
            if progress_callback:
                progress_callback("Finalizing", 75, "Generating output...")
            # output = await self._finalize(results)
            
            if progress_callback:
                progress_callback("Complete", 100, "Done!")
            
            # TODO: Replace with actual implementation
            return {{"message": "Implement your workflow here", "request": user_request}}
    
    # async def _plan(self, user_request: str) -> PlanOutput:
    #     """Phase 1: Create execution plan."""
    #     result = await Runner.run(planner_agent, f"Request: {{user_request}}")
    #     return result.final_output_as(PlanOutput)
    
    # async def _execute(self, plan: PlanOutput) -> list:
    #     """Phase 2: Execute the plan."""
    #     # Can run in parallel if steps are independent
    #     tasks = [
    #         asyncio.create_task(self._execute_step(step))
    #         for step in plan.steps
    #     ]
    #     return await asyncio.gather(*tasks)
    
    def run_sync(self, user_request: str) -> Any:
        """Sync wrapper for Django/web contexts."""
        return asyncio.run(self.run(user_request))


# Convenience function for direct usage
def run_{base_name}_sync(user_request: str) -> Any:
    """Run the {base_name} service synchronously."""
    manager = {class_name}()
    return manager.run_sync(user_request)
'''


TOOLS_TEMPLATE = '''"""
Shared tools for this service.

Define function tools that agents can use. Follow these rules:
1. Use @function_tool decorator
2. Clear docstrings with Args section
3. Use Pydantic models for complex inputs
4. NEVER call a decorated tool from another decorated tool

Example:
    @function_tool
    def search_database(query: str, limit: int = 10) -> str:
        """Search the database for matching records.
        
        Args:
            query: The search query string.
            limit: Maximum results to return.
        """
        return "results..."
"""

from agents import function_tool


# Example tool - uncomment and modify as needed
# @function_tool
# def example_tool(input_text: str) -> str:
#     """Process the input text.
#     
#     Args:
#         input_text: The text to process.
#     """
#     return f"Processed: {input_text}"


# For tools that call internal functions, use this pattern:
# def _internal_process(item: str) -> str:
#     """Internal implementation without decorator."""
#     return f"Processed {item}"
#
# @function_tool
# def process_item(item: str) -> str:
#     """Process a single item."""
#     return _internal_process(item)
#
# @function_tool  
# def process_items(items: list[str]) -> str:
#     """Process multiple items."""
#     results = [_internal_process(item) for item in items]
#     return "\\n".join(results)
'''


UTILITIES_TEMPLATE = '''"""
Utility functions for the manager.

These are helper functions that are NOT given to agents.
Use for:
- Data formatting
- Pre/post processing
- Deterministic operations
- Data retrieval

Do NOT put agent tools here - use tools.py instead.
"""

from typing import Any
import json


def format_for_agent(data: Any) -> str:
    """Format data as a string for agent input."""
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2)
    return str(data)


def parse_agent_output(output: Any) -> dict:
    """Parse and validate agent output."""
    if hasattr(output, 'model_dump'):
        return output.model_dump()
    if isinstance(output, dict):
        return output
    return {"raw": str(output)}


def calculate_progress(completed: int, total: int) -> int:
    """Calculate progress percentage."""
    if total == 0:
        return 0
    return int((completed / total) * 100)
'''


AGENTS_INIT_TEMPLATE = '''"""
Agents for this service.

Each agent should be in its own file following this pattern:
1. INSTRUCTIONS as uppercase constant
2. Pydantic models for output
3. Agent definition with output_type

Example:
    from .planner_agent import planner_agent, PlanOutput
"""

# Import your agents here for easy access
# from .planner_agent import planner_agent, PlanOutput
# from .executor_agent import executor_agent, ExecutorOutput
'''


def get_example_agent_template(base_name: str) -> str:
    """Generate an example agent template."""
    agent_name = f"{base_name.title().replace('_', '')}Agent"
    
    return f'''"""
Example Agent - Template for creating agents.

Follow this structure for all agents:
1. INSTRUCTIONS as uppercase constant
2. Pydantic models for structured output
3. Agent definition with output_type
"""

from pydantic import BaseModel, Field
from openai.types.shared import Reasoning

from agents import Agent, ModelSettings


# 1. INSTRUCTIONS (uppercase constant)
EXAMPLE_AGENT_INSTRUCTIONS = """
You are a helpful assistant for the {base_name} service.

Your role is to:
- [Describe what this agent does]
- [List key responsibilities]
- [Specify output format expectations]

Always provide structured, actionable responses.
"""


# 2. PYDANTIC MODELS for structured output
class ExampleOutput(BaseModel):
    """Structured output from this agent."""
    
    summary: str = Field(description="Brief summary of the result")
    details: list[str] = Field(default=[], description="Detailed findings or steps")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")


# 3. AGENT DEFINITION
example_agent = Agent(
    name="{agent_name}",
    instructions=EXAMPLE_AGENT_INSTRUCTIONS,
    model="gpt-5",  # or gpt-5-mini, gpt-5.2 for complex tasks
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium"),  # low, medium, high, xhigh (5.2 only)
    ),
    output_type=ExampleOutput,
)


# Usage example (in manager.py):
# from .agents.example_agent import example_agent, ExampleOutput
#
# result = await Runner.run(example_agent, "Your prompt here")
# output = result.final_output_as(ExampleOutput)
# print(output.summary)
'''

