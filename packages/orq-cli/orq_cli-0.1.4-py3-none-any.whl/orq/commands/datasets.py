"""Dataset commands for ORQ CLI."""

import json
from typing import Optional

import typer

from orq.client import get_client
from orq.utils import output, print_error, print_success

app = typer.Typer(help="Manage datasets and datapoints")


@app.command("list")
def list_datasets(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of datasets to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List all datasets."""
    try:
        client = get_client(api_key, env)
        result = client.datasets.list(limit=limit)
        output(
            result,
            format=output_format,
            columns=["id", "display_name", "created_at"],
            title="Datasets"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create")
def create_dataset(
    name: str = typer.Option(..., "--name", "-n", help="Dataset display name"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Create a new dataset."""
    try:
        client = get_client(api_key, env)
        result = client.datasets.create(request={"display_name": name})
        print_success(f"Dataset created with ID: {result.id}")
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_dataset(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Get dataset details."""
    try:
        client = get_client(api_key, env)
        result = client.datasets.retrieve(dataset_id=dataset_id)
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("update")
def update_dataset(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New display name"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Update a dataset."""
    try:
        client = get_client(api_key, env)
        kwargs = {"dataset_id": dataset_id}
        if name:
            kwargs["display_name"] = name
        result = client.datasets.update(**kwargs)
        print_success("Dataset updated")
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("delete")
def delete_dataset(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Delete a dataset."""
    try:
        if not force:
            confirm = typer.confirm(f"Delete dataset {dataset_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.datasets.delete(dataset_id=dataset_id)
        print_success(f"Dataset {dataset_id} deleted")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("clear")
def clear_dataset(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Clear all datapoints from a dataset."""
    try:
        if not force:
            confirm = typer.confirm(f"Clear all datapoints from dataset {dataset_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.datasets.clear(dataset_id=dataset_id)
        print_success(f"Dataset {dataset_id} cleared")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# Datapoint subcommands
datapoints_app = typer.Typer(help="Manage datapoints within a dataset")
app.add_typer(datapoints_app, name="datapoints")


@datapoints_app.command("list")
def list_datapoints(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of datapoints to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List datapoints in a dataset."""
    try:
        client = get_client(api_key, env)
        result = client.datasets.list_datapoints(dataset_id=dataset_id, limit=limit)
        output(
            result,
            format=output_format,
            columns=["id", "inputs", "expected_output"],
            title="Datapoints"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@datapoints_app.command("create")
def create_datapoint(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    inputs: Optional[str] = typer.Option(None, "--inputs", "-i", help="JSON inputs"),
    expected_output: Optional[str] = typer.Option(None, "--expected", "-e", help="Expected output"),
    messages: Optional[str] = typer.Option(None, "--messages", "-m", help="JSON array of messages"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env_opt: Optional[str] = typer.Option(None, "--env", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Create a datapoint in a dataset."""
    try:
        client = get_client(api_key, env_opt)
        kwargs = {"dataset_id": dataset_id}
        if inputs:
            kwargs["inputs"] = json.loads(inputs)
        if expected_output:
            kwargs["expected_output"] = expected_output
        if messages:
            kwargs["messages"] = json.loads(messages)

        result = client.datasets.create_datapoint(**kwargs)
        print_success(f"Datapoint created with ID: {result.id}")
        output(result, format=output_format)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@datapoints_app.command("get")
def get_datapoint(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    datapoint_id: str = typer.Argument(..., help="Datapoint ID"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Get a datapoint."""
    try:
        client = get_client(api_key, env)
        result = client.datasets.retrieve_datapoint(dataset_id=dataset_id, datapoint_id=datapoint_id)
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@datapoints_app.command("delete")
def delete_datapoint(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    datapoint_id: str = typer.Argument(..., help="Datapoint ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Delete a datapoint."""
    try:
        if not force:
            confirm = typer.confirm(f"Delete datapoint {datapoint_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.datasets.delete_datapoint(dataset_id=dataset_id, datapoint_id=datapoint_id)
        print_success(f"Datapoint {datapoint_id} deleted")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
