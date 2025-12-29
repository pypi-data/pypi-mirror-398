"""Main CLI entry point for ORQ CLI."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from orq import __version__
from orq.commands import (
    config_cmd,
    contacts,
    datasets,
    deployments,
    feedback,
    files,
    knowledge,
    prompts,
)
from orq.interactive import run_interactive

console = Console()

app = typer.Typer(
    name="orq",
    help="CLI for orq.ai LLM Ops platform",
    invoke_without_command=True,
    rich_markup_mode="rich",
)

# Add subcommands
app.add_typer(deployments.app, name="deployments", help="Manage and invoke deployments")
app.add_typer(datasets.app, name="datasets", help="Manage datasets and datapoints")
app.add_typer(files.app, name="files", help="Manage files")
app.add_typer(knowledge.app, name="knowledge", help="Manage knowledge bases")
app.add_typer(prompts.app, name="prompts", help="Manage prompts")
app.add_typer(contacts.app, name="contacts", help="Manage contacts")
app.add_typer(feedback.app, name="feedback", help="Submit feedback")
app.add_typer(config_cmd.app, name="config", help="Manage CLI configuration")


def version_callback(value: bool):
    if value:
        console.print(f"orq-cli version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        is_eager=True,
        help="Run in interactive mode",
    ),
):
    """
    ORQ CLI - Command line interface for orq.ai LLM Ops platform.

    Use [bold cyan]orq --interactive[/bold cyan] for a guided experience.

    Configure your API key:
      [dim]orq config set api_key YOUR_KEY[/dim]

    Or use environment variable:
      [dim]export ORQ_API_KEY=YOUR_KEY[/dim]
    """
    if interactive:
        run_interactive()
        raise typer.Exit()

    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# Quick shortcuts for common operations
@app.command("invoke")
def quick_invoke(
    key: str = typer.Argument(..., help="Deployment key"),
    var: Optional[list[str]] = typer.Option(None, "--var", "-v", help="Variable as key=value (can be used multiple times)"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Message to send"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Quick invoke a deployment.

    Examples:
      orq invoke my-deployment -m "Hello"
      orq invoke my-deployment -v firstname=John -v city=Paris
      orq invoke my-deployment -v name=John -m "Hello" --stream
    """
    import json
    from orq.client import get_client
    from orq.utils import print_error

    try:
        client = get_client(api_key, env)

        kwargs = {"key": key}

        # Build inputs from --var flags
        if var:
            inputs = {}
            for v in var:
                if "=" not in v:
                    print_error(f"Invalid variable format: {v}. Use key=value")
                    raise typer.Exit(1)
                k, val = v.split("=", 1)
                try:
                    val = json.loads(val)
                except json.JSONDecodeError:
                    pass
                inputs[k.strip()] = val
            kwargs["inputs"] = inputs

        if message:
            kwargs["messages"] = [{"role": "user", "content": message}]

        if stream:
            with client.deployments.stream(**kwargs) as stream_response:
                for event in stream_response:
                    if event.choices:
                        for choice in event.choices:
                            if choice.delta and choice.delta.content:
                                console.print(choice.delta.content, end="")
            console.print()
        else:
            result = client.deployments.invoke(**kwargs)
            if result and result.choices:
                console.print(result.choices[0].message.content)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("list")
def quick_list(
    resource: str = typer.Argument(..., help="Resource type: deployments, datasets, files, knowledge, prompts"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of items"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format"),
):
    """Quick list resources (shortcut)."""
    from orq.client import get_client
    from orq.utils import output, print_error

    try:
        client = get_client(api_key, env)

        resource_map = {
            "deployments": (client.deployments.list, ["key", "description"]),
            "datasets": (client.datasets.list, ["id", "display_name"]),
            "files": (client.files.list, ["id", "file_name", "purpose"]),
            "knowledge": (client.knowledge.list, ["id", "key", "description"]),
            "prompts": (client.prompts.list, ["display_name", "domain_id", "description"]),
        }

        if resource not in resource_map:
            print_error(f"Unknown resource: {resource}. Use: {', '.join(resource_map.keys())}")
            raise typer.Exit(1)

        list_fn, columns = resource_map[resource]
        result = list_fn(limit=limit)
        output(result, format=output_format, columns=columns, title=resource.title())

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
