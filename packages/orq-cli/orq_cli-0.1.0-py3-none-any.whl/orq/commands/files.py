"""File commands for ORQ CLI."""

from pathlib import Path
from typing import Optional

import typer

from orq.client import get_client
from orq.utils import output, print_error, print_success

app = typer.Typer(help="Manage files for retrieval and knowledge bases")


@app.command("upload")
def upload_file(
    file_path: Path = typer.Argument(..., help="Path to file to upload", exists=True),
    purpose: str = typer.Option("retrieval", "--purpose", "-p", help="File purpose: retrieval, knowledge_datasource, batch"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Upload a file."""
    try:
        client = get_client(api_key, env)

        with open(file_path, "rb") as f:
            content = f.read()

        result = client.files.create(
            file={
                "file_name": file_path.name,
                "content": content,
            },
            purpose=purpose
        )
        print_success(f"File uploaded with ID: {result.id}")
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("list")
def list_files(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of files to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List all files."""
    try:
        client = get_client(api_key, env)
        result = client.files.list(limit=limit)
        output(
            result,
            format=output_format,
            columns=["id", "file_name", "purpose", "created_at"],
            title="Files"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_file(
    file_id: str = typer.Argument(..., help="File ID"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Get file details."""
    try:
        client = get_client(api_key, env)
        result = client.files.get(file_id=file_id)
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("delete")
def delete_file(
    file_id: str = typer.Argument(..., help="File ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Delete a file."""
    try:
        if not force:
            confirm = typer.confirm(f"Delete file {file_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.files.delete(file_id=file_id)
        print_success(f"File {file_id} deleted")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
