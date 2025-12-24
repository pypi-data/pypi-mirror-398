"""
startproject command - Initialize a new agents project.

Creates:
- agents_sdk/ folder with README
- Rules in .cursor/rules/, .claude/rules/, or .github/rules/
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from ..rules import get_all_rules
from ..templates import agents_sdk_readme

console = Console()


def find_or_create_rules_dir(base_path: Path) -> Path:
    """
    Find existing rules directory or create one.
    
    Priority: .cursor/rules/ > .claude/rules/ > .github/rules/
    """
    candidates = [
        base_path / ".cursor" / "rules",
        base_path / ".claude" / "rules", 
        base_path / ".github" / "rules",
    ]
    
    # Check if any exist
    for rules_dir in candidates:
        if rules_dir.exists():
            return rules_dir
    
    # Check if parent dirs exist (prefer .cursor if it exists)
    for rules_dir in candidates:
        parent = rules_dir.parent
        if parent.exists():
            rules_dir.mkdir(parents=True, exist_ok=True)
            return rules_dir
    
    # Create .cursor/rules/ by default
    default_rules_dir = candidates[0]
    default_rules_dir.mkdir(parents=True, exist_ok=True)
    return default_rules_dir


def create_agents_sdk_folder(base_path: Path) -> bool:
    """Create agents_sdk/ folder with README if it doesn't exist."""
    agents_sdk_dir = base_path / "agents_sdk"
    
    if agents_sdk_dir.exists():
        console.print(f"  [yellow]![/yellow]  agents_sdk/ already exists")
        return False
    
    agents_sdk_dir.mkdir(parents=True, exist_ok=True)
    
    # Create README
    readme_path = agents_sdk_dir / "README.md"
    readme_path.write_text(agents_sdk_readme.AGENTS_SDK_README, encoding="utf-8")
    
    console.print(f"  [green]+[/green]  Created agents_sdk/")
    console.print(f"  [green]+[/green]  Created agents_sdk/README.md")
    return True


def install_rules(rules_dir: Path) -> int:
    """Install the Mutta convention rules from the package's rules directory."""
    installed_count = 0
    
    for filename, source_path in get_all_rules():
        target_path = rules_dir / filename
        
        if target_path.exists():
            console.print(f"  [yellow]![/yellow]  {filename} already exists, skipping")
        else:
            # Copy the rule file content
            content = source_path.read_text(encoding="utf-8")
            target_path.write_text(content, encoding="utf-8")
            console.print(f"  [green]+[/green]  Created {filename}")
            installed_count += 1
    
    return installed_count


@click.command()
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
def startproject(path: Path, verbose: bool):
    """
    Initialize a new agents project with Mutta conventions.
    
    Creates agents_sdk/ folder and installs rules to your IDE's rules directory.
    """
    base_path = Path(path).resolve()
    
    console.print(Panel.fit(
        "[bold blue]Mutta - Starting Project[/bold blue]",
        subtitle=f"in {base_path}"
    ))
    console.print()
    
    # Step 1: Create agents_sdk/ folder
    console.print("[bold]Step 1:[/bold] Setting up agents_sdk/ folder")
    create_agents_sdk_folder(base_path)
    console.print()
    
    # Step 2: Find or create rules directory
    console.print("[bold]Step 2:[/bold] Setting up rules")
    rules_dir = find_or_create_rules_dir(base_path)
    relative_rules_dir = rules_dir.relative_to(base_path)
    console.print(f"  [dim]Using rules directory:[/dim] {relative_rules_dir}/")
    
    # Step 3: Install rules
    installed = install_rules(rules_dir)
    console.print()
    
    # Summary
    console.print(Panel.fit(
        f"[green]Project initialized![/green]\n\n"
        f"Next steps:\n"
        f"  1. Run [bold]mutta startservice <name>[/bold] to create a service\n"
        f"  2. Read the rules in {relative_rules_dir}/ for conventions",
        title="[bold]Done[/bold]"
    ))
