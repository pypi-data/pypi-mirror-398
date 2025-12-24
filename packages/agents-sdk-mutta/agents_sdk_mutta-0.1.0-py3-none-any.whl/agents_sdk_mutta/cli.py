"""
Main CLI entry point for agents-sdk-mutta.

Usage:
    mutta startproject
    mutta startservice <name>
"""

import click
from rich.console import Console

from .commands.startproject import startproject
from .commands.startservice import startservice

console = Console()


@click.group()
@click.version_option()
def main():
    """
    Mutta - OpenAI Agents SDK Scaffolding Tool
    
    Scaffold agent projects following Mutta conventions.
    """
    pass


# Register commands
main.add_command(startproject)
main.add_command(startservice)


if __name__ == "__main__":
    main()

