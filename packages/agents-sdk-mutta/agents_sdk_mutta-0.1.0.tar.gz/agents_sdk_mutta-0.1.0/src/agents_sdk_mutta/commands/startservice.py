"""
startservice command - Create a new agent service.

Creates the full service structure following Mutta conventions.
"""

import re
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from ..templates import service_templates

console = Console()


def normalize_service_name(name: str) -> str:
    """
    Normalize service name to follow conventions.
    
    - Converts to lowercase
    - Replaces hyphens/spaces with underscores
    - Adds _agents suffix if not present
    """
    # Lowercase and replace hyphens/spaces
    normalized = name.lower().replace("-", "_").replace(" ", "_")
    
    # Remove any non-alphanumeric chars (except underscore)
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    
    # Add _agents suffix if not present
    if not normalized.endswith("_agents"):
        normalized = f"{normalized}_agents"
    
    return normalized


def create_service_structure(base_path: Path, service_name: str, verbose: bool = False) -> bool:
    """Create the full service directory structure."""
    
    # Ensure agents_sdk/ exists
    agents_sdk_dir = base_path / "agents_sdk"
    if not agents_sdk_dir.exists():
        console.print("[yellow]![/yellow]  agents_sdk/ doesn't exist. Run 'mutta startproject' first.")
        console.print("    Creating it now...")
        agents_sdk_dir.mkdir(parents=True, exist_ok=True)
    
    # Create service directory
    service_dir = agents_sdk_dir / service_name
    
    if service_dir.exists():
        console.print(f"[red]x[/red]  Service '{service_name}' already exists!")
        return False
    
    # Create directory structure
    service_dir.mkdir(parents=True, exist_ok=True)
    agents_dir = service_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the base name (without _agents suffix)
    base_name = service_name.replace("_agents", "")
    
    # Create files
    files_to_create = [
        (service_dir / "__init__.py", service_templates.get_init_template(service_name)),
        (service_dir / "manager.py", service_templates.get_manager_template(service_name, base_name)),
        (service_dir / "tools.py", service_templates.TOOLS_TEMPLATE),
        (service_dir / "utilities.py", service_templates.UTILITIES_TEMPLATE),
        (agents_dir / "__init__.py", service_templates.AGENTS_INIT_TEMPLATE),
        (agents_dir / "example_agent.py", service_templates.get_example_agent_template(base_name)),
    ]
    
    for file_path, content in files_to_create:
        file_path.write_text(content, encoding="utf-8")
        if verbose:
            relative_path = file_path.relative_to(base_path)
            console.print(f"  [green]+[/green]  Created {relative_path}")
    
    return True


def display_structure(service_name: str):
    """Display the created structure as a tree."""
    tree = Tree(f"[bold]agents_sdk/{service_name}/[/bold]")
    tree.add("[dim]__init__.py[/dim]")
    tree.add("[cyan]manager.py[/cyan] - Main orchestrator")
    tree.add("[dim]tools.py[/dim] - Shared tools")
    tree.add("[dim]utilities.py[/dim] - Helper functions")
    
    agents = tree.add("[bold]agents/[/bold]")
    agents.add("[dim]__init__.py[/dim]")
    agents.add("[cyan]example_agent.py[/cyan] - Example agent template")
    
    console.print(tree)


@click.command()
@click.argument("name")
@click.option(
    "--path", "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
    help="Base path for the project (default: current directory)"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show verbose output"
)
def startservice(name: str, path: Path, verbose: bool):
    """
    Create a new agent service with the given NAME.
    
    The name will be normalized (lowercase, underscores) and 
    '_agents' suffix will be added if not present.
    
    Example:
        mutta startservice research
        mutta startservice my-cool-service
    """
    base_path = Path(path).resolve()
    service_name = normalize_service_name(name)
    
    console.print(Panel.fit(
        f"[bold blue]Mutta - Creating Service[/bold blue]\n"
        f"[dim]Name:[/dim] {name} -> [bold]{service_name}[/bold]",
        subtitle=f"in {base_path}"
    ))
    console.print()
    
    # Create the service
    success = create_service_structure(base_path, service_name, verbose)
    
    if not success:
        return
    
    console.print()
    console.print("[bold]Created structure:[/bold]")
    display_structure(service_name)
    console.print()
    
    # Next steps
    base_name = service_name.replace("_agents", "")
    console.print(Panel.fit(
        f"[green]Service created![/green]\n\n"
        f"Next steps:\n"
        f"  1. Edit [bold]manager.py[/bold] to define your workflow\n"
        f"  2. Create agents in [bold]agents/[/bold] folder\n"
        f"  3. Add tools to [bold]tools.py[/bold] if needed\n\n"
        f"Example usage:\n"
        f"  [dim]from agents_sdk.{service_name} import {base_name.title().replace('_', '')}Manager[/dim]",
        title="[bold]Done[/bold]"
    ))

