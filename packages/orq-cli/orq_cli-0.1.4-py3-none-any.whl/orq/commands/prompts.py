"""Prompt commands for ORQ CLI."""

from typing import Optional

import typer

from orq.client import get_client
from orq.utils import output, print_error

app = typer.Typer(help="Manage prompts")


@app.command("list")
def list_prompts(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of prompts to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List all prompts."""
    try:
        client = get_client(api_key, env)
        result = client.prompts.list(limit=limit)
        output(
            result,
            format=output_format,
            columns=["display_name", "domain_id", "description", "created"],
            title="Prompts"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_prompt(
    prompt_id: str = typer.Argument(..., help="Prompt ID (domain_id from list)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Get prompt details by ID (use domain_id from list command)."""
    try:
        client = get_client(api_key, env)
        result = client.prompts.retrieve(prompt_id=prompt_id)
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
