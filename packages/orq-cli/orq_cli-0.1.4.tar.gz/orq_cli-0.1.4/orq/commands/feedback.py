"""Feedback commands for ORQ CLI."""

import json
from typing import Optional

import typer

from orq.client import get_client
from orq.utils import output, print_error, print_success

app = typer.Typer(help="Submit feedback for traces")


@app.command("create")
def create_feedback(
    trace_id: str = typer.Argument(..., help="Trace ID to attach feedback to"),
    field: str = typer.Option(..., "--field", "-f", help="Feedback field name"),
    value: str = typer.Option(..., "--value", "-v", help="Feedback value (JSON or string)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Submit feedback for a trace."""
    try:
        client = get_client(api_key, env)

        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value

        result = client.feedback.create(
            trace_id=trace_id,
            field=field,
            value=parsed_value
        )
        print_success("Feedback submitted")
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
