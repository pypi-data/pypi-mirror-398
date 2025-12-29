"""Configuration commands for ORQ CLI."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from orq.config import load_config, save_config, CONFIG_FILE

app = typer.Typer(help="Manage CLI configuration")
console = Console()


@app.command("show")
def show_config():
    """Show current configuration."""
    config = load_config()

    table = Table(title=f"Configuration ({CONFIG_FILE})")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in config.items():
        if key == "api_key" and value:
            display_value = value[:20] + "..." if len(value) > 20 else value
        else:
            display_value = str(value) if value else "(not set)"
        table.add_row(key, display_value)

    console.print(table)


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)
    console.print(f"[green][OK][/green] Set {key}")


@app.command("get")
def get_config(
    key: str = typer.Argument(..., help="Configuration key to get"),
):
    """Get a configuration value."""
    config = load_config()
    value = config.get(key)
    if value is None:
        console.print(f"[yellow]{key} is not set[/yellow]")
    else:
        if key == "api_key":
            display_value = value[:20] + "..." if len(value) > 20 else value
        else:
            display_value = value
        console.print(display_value)


@app.command("unset")
def unset_config(
    key: str = typer.Argument(..., help="Configuration key to unset"),
):
    """Unset a configuration value."""
    config = load_config()
    if key in config:
        del config[key]
        save_config(config)
        console.print(f"[green][OK][/green] Unset {key}")
    else:
        console.print(f"[yellow]{key} was not set[/yellow]")


@app.command("path")
def config_path():
    """Show configuration file path."""
    console.print(str(CONFIG_FILE))
