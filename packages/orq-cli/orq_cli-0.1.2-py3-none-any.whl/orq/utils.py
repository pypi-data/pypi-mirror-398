"""Utility functions for ORQ CLI output formatting."""

import json
from typing import Any, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

console = Console()


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    output = json.dumps(data, indent=2, default=str)
    syntax = Syntax(output, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def print_yaml(data: Any) -> None:
    """Print data as formatted YAML."""
    output = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    syntax = Syntax(output, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)


def print_table(
    data: List[dict],
    columns: List[str],
    title: Optional[str] = None
) -> None:
    """Print data as a rich table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")

    for col in columns:
        table.add_column(col.replace("_", " ").title())

    for row in data:
        values = []
        for col in columns:
            val = row.get(col, "")
            if val is None:
                val = ""
            elif isinstance(val, (dict, list)):
                val = json.dumps(val, default=str)[:50] + "..." if len(json.dumps(val, default=str)) > 50 else json.dumps(val, default=str)
            else:
                val = str(val)
            values.append(val)
        table.add_row(*values)

    console.print(table)


def output(
    data: Any,
    format: str = "table",
    columns: Optional[List[str]] = None,
    title: Optional[str] = None
) -> None:
    """Output data in the specified format."""
    if data is None:
        console.print("[yellow]No data returned[/yellow]")
        return

    if format == "json":
        if hasattr(data, "model_dump"):
            print_json(data.model_dump())
        elif hasattr(data, "__dict__"):
            print_json(data.__dict__)
        else:
            print_json(data)
    elif format == "yaml":
        if hasattr(data, "model_dump"):
            print_yaml(data.model_dump())
        elif hasattr(data, "__dict__"):
            print_yaml(data.__dict__)
        else:
            print_yaml(data)
    else:
        if isinstance(data, list):
            if columns and data:
                rows = []
                for item in data:
                    if hasattr(item, "model_dump"):
                        rows.append(item.model_dump())
                    elif hasattr(item, "__dict__"):
                        rows.append(item.__dict__)
                    else:
                        rows.append(item)
                print_table(rows, columns, title)
            else:
                print_json(data)
        elif hasattr(data, "data") and isinstance(data.data, list):
            if columns and data.data:
                rows = []
                for item in data.data:
                    if hasattr(item, "model_dump"):
                        rows.append(item.model_dump())
                    elif hasattr(item, "__dict__"):
                        rows.append(item.__dict__)
                    else:
                        rows.append(item)
                print_table(rows, columns, title)
            else:
                print_json([item.model_dump() if hasattr(item, "model_dump") else item for item in data.data])
        else:
            if hasattr(data, "model_dump"):
                print_json(data.model_dump())
            else:
                print_json(data)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green][OK][/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red][ERROR][/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow][WARN][/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue][INFO][/blue] {message}")


def print_streaming(content: str, end: str = "") -> None:
    """Print streaming content without newline."""
    console.print(content, end=end)
