"""Knowledge base commands for ORQ CLI."""

import json
from typing import Optional

import typer

from orq.client import get_client
from orq.utils import output, print_error, print_success

app = typer.Typer(help="Manage knowledge bases, datasources, and chunks")


@app.command("list")
def list_knowledge_bases(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of knowledge bases to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List all knowledge bases."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.list(limit=limit)
        output(
            result,
            format=output_format,
            columns=["id", "key", "description", "embedding_model"],
            title="Knowledge Bases"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("create")
def create_knowledge_base(
    key: str = typer.Option(..., "--key", "-k", help="Unique key for the knowledge base"),
    embedding_model: str = typer.Option(..., "--model", "-m", help="Embedding model to use"),
    path: str = typer.Option(..., "--path", "-p", help="Path/folder for the knowledge base"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Create a new knowledge base."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.create(
            key=key,
            embedding_model=embedding_model,
            path=path,
            description=description
        )
        print_success(f"Knowledge base created with ID: {result.id}")
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("get")
def get_knowledge_base(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Get knowledge base details."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.retrieve(knowledge_id=knowledge_id)
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("delete")
def delete_knowledge_base(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Delete a knowledge base."""
    try:
        if not force:
            confirm = typer.confirm(f"Delete knowledge base {knowledge_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.knowledge.delete(knowledge_id=knowledge_id)
        print_success(f"Knowledge base {knowledge_id} deleted")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("search")
def search_knowledge(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of results"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Search a knowledge base."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.search(
            knowledge_id=knowledge_id,
            query=query,
            limit=limit
        )
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# Datasource subcommands
datasources_app = typer.Typer(help="Manage datasources within a knowledge base")
app.add_typer(datasources_app, name="datasources")


@datasources_app.command("list")
def list_datasources(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of datasources to list"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List datasources in a knowledge base."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.list_datasources(knowledge_id=knowledge_id, limit=limit)
        output(
            result,
            format=output_format,
            columns=["id", "display_name", "status"],
            title="Datasources"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@datasources_app.command("create")
def create_datasource(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    display_name: Optional[str] = typer.Option(None, "--name", "-n", help="Display name"),
    file_id: Optional[str] = typer.Option(None, "--file-id", "-f", help="File ID to use as datasource"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Create a datasource in a knowledge base."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.create_datasource(
            knowledge_id=knowledge_id,
            display_name=display_name,
            file_id=file_id
        )
        print_success(f"Datasource created with ID: {result.id}")
        output(result, format=output_format)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@datasources_app.command("delete")
def delete_datasource(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    datasource_id: str = typer.Argument(..., help="Datasource ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Delete a datasource."""
    try:
        if not force:
            confirm = typer.confirm(f"Delete datasource {datasource_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.knowledge.delete_datasource(knowledge_id=knowledge_id, datasource_id=datasource_id)
        print_success(f"Datasource {datasource_id} deleted")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# Chunks subcommands
chunks_app = typer.Typer(help="Manage chunks within a datasource")
app.add_typer(chunks_app, name="chunks")


@chunks_app.command("list")
def list_chunks(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    datasource_id: str = typer.Argument(..., help="Datasource ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of chunks to list"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format: table, json, yaml"),
):
    """List chunks in a datasource."""
    try:
        client = get_client(api_key, env)
        result = client.knowledge.list_chunks(
            knowledge_id=knowledge_id,
            datasource_id=datasource_id,
            limit=limit,
            q=query
        )
        output(
            result,
            format=output_format,
            columns=["id", "content", "metadata"],
            title="Chunks"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@chunks_app.command("create")
def create_chunks(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    datasource_id: str = typer.Argument(..., help="Datasource ID"),
    chunks: str = typer.Option(..., "--chunks", "-c", help="JSON array of chunks with content and optional metadata"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format: json, yaml"),
):
    """Create chunks in a datasource."""
    try:
        client = get_client(api_key, env)
        chunk_data = json.loads(chunks)
        result = client.knowledge.create_chunks(
            knowledge_id=knowledge_id,
            datasource_id=datasource_id,
            request_body=chunk_data
        )
        print_success(f"Created {len(result)} chunks")
        output(result, format=output_format)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@chunks_app.command("delete")
def delete_chunk(
    knowledge_id: str = typer.Argument(..., help="Knowledge base ID"),
    datasource_id: str = typer.Argument(..., help="Datasource ID"),
    chunk_id: str = typer.Argument(..., help="Chunk ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ORQ_API_KEY"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment"),
):
    """Delete a chunk."""
    try:
        if not force:
            confirm = typer.confirm(f"Delete chunk {chunk_id}?")
            if not confirm:
                raise typer.Abort()

        client = get_client(api_key, env)
        client.knowledge.delete_chunk(
            knowledge_id=knowledge_id,
            datasource_id=datasource_id,
            chunk_id=chunk_id
        )
        print_success(f"Chunk {chunk_id} deleted")
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
