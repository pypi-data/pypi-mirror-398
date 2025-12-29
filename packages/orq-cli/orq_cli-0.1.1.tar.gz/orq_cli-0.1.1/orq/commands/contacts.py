"""Contact commands for ORQ CLI."""

import json
from typing import Optional

import typer

from orq.client import get_client
from orq.utils import output, print_error, print_success

app = typer.Typer(help="Manage contacts for usage tracking")


@app.command("create")
def create_contact(
    external_id: str = typer.Argument(..., help="External ID for the contact"),
    display_name: Optional[str] = typer.Option(None, "--name", "-n", help="Display name"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email address"),
    avatar_url: Optional[str] = typer.Option(None, "--avatar", help="Avatar URL"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="JSON metadata"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Create a new contact for usage tracking."""
    try:
        client = get_client(api_key, env)

        kwargs = {"external_id": external_id}
        if display_name:
            kwargs["display_name"] = display_name
        if email:
            kwargs["email"] = email
        if avatar_url:
            kwargs["avatar_url"] = avatar_url
        if tags:
            kwargs["tags"] = [t.strip() for t in tags.split(",")]
        if metadata:
            kwargs["metadata"] = json.loads(metadata)

        result = client.contacts.create(**kwargs)
        print_success(f"Contact created with ID: {result.id}")
        output(result, format=output_format)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
