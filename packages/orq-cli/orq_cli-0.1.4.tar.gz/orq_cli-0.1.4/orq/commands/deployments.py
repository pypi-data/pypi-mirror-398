"""Deployment commands for ORQ CLI."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.text import Text

from orq.client import get_client
from orq.utils import output, print_error, print_streaming

app = typer.Typer(help="Manage and invoke deployments")
console = Console()


@app.command("list")
def list_deployments(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of deployments to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List all deployments."""
    try:
        client = get_client(api_key, env)
        result = client.deployments.list(limit=limit)
        output(
            result,
            format=output_format,
            columns=["key", "description", "created"],
            title="Deployments"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


def parse_var(var: str) -> tuple:
    """Parse a key=value variable string."""
    if "=" not in var:
        raise ValueError(f"Invalid variable format: {var}. Use key=value")
    key, value = var.split("=", 1)
    # Try to parse as JSON for numbers, bools, objects
    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass  # Keep as string
    return key.strip(), value


@app.command("invoke")
def invoke_deployment(
    key: str = typer.Argument(..., help="Deployment key"),
    var: Optional[list[str]] = typer.Option(None, "--var", "-v", help="Variable as key=value (can be used multiple times)"),
    inputs: Optional[str] = typer.Option(None, "--inputs", help="JSON string of inputs (alternative to --var)"),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="JSON string of context"),
    metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="JSON string of metadata"),
    messages: Optional[str] = typer.Option(None, "--messages", help="JSON array of messages for chat"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: table, json, yaml"),
):
    """Invoke a deployment and get a response.

    Variables can be passed in two ways:

      Using --var (recommended):
        orq deployments invoke my-key -v firstname=John -v city=Paris

      Using --inputs (JSON):
        orq deployments invoke my-key --inputs '{"firstname": "John"}'
    """
    try:
        client = get_client(api_key, env)

        kwargs = {"key": key}

        # Build inputs from --var flags
        if var:
            parsed_inputs = {}
            for v in var:
                k, val = parse_var(v)
                parsed_inputs[k] = val
            kwargs["inputs"] = parsed_inputs

        # Or use JSON inputs (overrides --var if both provided)
        if inputs:
            kwargs["inputs"] = json.loads(inputs)

        if context:
            kwargs["context"] = json.loads(context)
        if metadata:
            kwargs["metadata"] = json.loads(metadata)
        if messages:
            kwargs["messages"] = json.loads(messages)

        result = client.deployments.invoke(**kwargs)

        if result and result.choices:
            if output_format == "json":
                output(result, format="json")
            else:
                for choice in result.choices:
                    if choice.message and choice.message.content:
                        console.print(choice.message.content)
        else:
            output(result, format=output_format)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("stream")
def stream_deployment(
    key: str = typer.Argument(..., help="Deployment key"),
    var: Optional[list[str]] = typer.Option(None, "--var", "-v", help="Variable as key=value (can be used multiple times)"),
    inputs: Optional[str] = typer.Option(None, "--inputs", help="JSON string of inputs (alternative to --var)"),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="JSON string of context"),
    metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="JSON string of metadata"),
    messages: Optional[str] = typer.Option(None, "--messages", help="JSON array of messages for chat"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Stream a deployment response in real-time.

    Variables can be passed using --var:
      orq deployments stream my-key -v firstname=John -v city=Paris
    """
    try:
        client = get_client(api_key, env)

        kwargs = {"key": key}

        # Build inputs from --var flags
        if var:
            parsed_inputs = {}
            for v in var:
                k, val = parse_var(v)
                parsed_inputs[k] = val
            kwargs["inputs"] = parsed_inputs

        if inputs:
            kwargs["inputs"] = json.loads(inputs)
        if context:
            kwargs["context"] = json.loads(context)
        if metadata:
            kwargs["metadata"] = json.loads(metadata)
        if messages:
            kwargs["messages"] = json.loads(messages)

        with client.deployments.stream(**kwargs) as stream:
            for event in stream:
                if event.choices:
                    for choice in event.choices:
                        if choice.delta and choice.delta.content:
                            console.print(choice.delta.content, end="")
        console.print()
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get-config")
def get_config(
    key: str = typer.Argument(..., help="Deployment key"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Get deployment configuration."""
    try:
        client = get_client(api_key, env)
        result = client.deployments.get_config(key=key)
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


def extract_variables(text: str) -> list[str]:
    """Extract {{variable}} placeholders from text."""
    import re
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    return list(set(re.findall(pattern, text)))


@app.command("info")
def deployment_info(
    key: str = typer.Argument(..., help="Deployment key"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Show deployment info including required variables.

    This command shows a summary of the deployment configuration
    and extracts any {{variable}} placeholders from the prompts.
    """
    from rich.panel import Panel
    from rich.table import Table

    try:
        client = get_client(api_key, env)
        config = client.deployments.get_config(key=key)

        # Extract variables from all messages
        all_variables = []
        if config.messages:
            for msg in config.messages:
                if msg.content:
                    all_variables.extend(extract_variables(msg.content))
        all_variables = sorted(set(all_variables))

        # Build info display
        console.print(Panel(f"[bold cyan]{key}[/bold cyan]", title="Deployment"))

        # Config table
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Field", style="dim")
        info_table.add_column("Value")

        info_table.add_row("Provider", str(config.provider) if config.provider else "-")
        info_table.add_row("Model", str(config.model) if config.model else "-")
        info_table.add_row("Version", str(config.version) if config.version else "-")

        if config.parameters:
            params = config.parameters
            if hasattr(params, 'temperature') and params.temperature is not None:
                info_table.add_row("Temperature", str(params.temperature))

        console.print(info_table)
        console.print()

        # Variables
        if all_variables:
            console.print("[bold]Required Variables:[/bold]")
            for var in all_variables:
                console.print(f"  -v {var}=<value>", style="green")
            console.print()
            console.print("[dim]Example:[/dim]")
            example_vars = " ".join([f"-v {v}=..." for v in all_variables[:3]])
            console.print(f"  orq invoke {key} {example_vars}")
        else:
            console.print("[dim]No variables detected in prompts[/dim]")

        console.print()

        # Show prompts
        if config.messages:
            console.print("[bold]Prompts:[/bold]")
            for msg in config.messages:
                role = msg.role if msg.role else "unknown"
                content = msg.content if msg.content else ""
                # Truncate long content
                if len(content) > 200:
                    content = content[:200] + "..."
                console.print(f"  [{role}] {content}", style="dim")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
