"""Interactive mode for ORQ CLI."""

import json
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orq.client import get_client
from orq.config import get_api_key, load_config, save_config
from orq.utils import output, print_error, print_success, print_info

console = Console()


def interactive_setup() -> bool:
    """Run initial setup if API key is not configured."""
    if get_api_key():
        return True

    console.print(Panel.fit(
        "[bold]Welcome to ORQ CLI[/bold]\n\n"
        "No API key found. Let's set one up.",
        border_style="blue"
    ))

    api_key = questionary.password(
        "Enter your ORQ API key:",
    ).ask()

    if not api_key:
        return False

    config = load_config()
    config["api_key"] = api_key
    save_config(config)
    print_success("API key saved")
    return True


def show_main_menu() -> Optional[str]:
    """Show the main menu."""
    console.print()
    return questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Deployments", value="deployments"),
            questionary.Choice("Datasets", value="datasets"),
            questionary.Choice("Files", value="files"),
            questionary.Choice("Knowledge Bases", value="knowledge"),
            questionary.Choice("Prompts", value="prompts"),
            questionary.Choice("Contacts", value="contacts"),
            questionary.Choice("Feedback", value="feedback"),
            questionary.Choice("Configuration", value="config"),
            questionary.Separator(),
            questionary.Choice("Exit", value="exit"),
        ],
        style=questionary.Style([
            ('selected', 'fg:cyan bold'),
            ('pointer', 'fg:cyan bold'),
        ])
    ).ask()


def deployments_menu():
    """Deployments submenu."""
    while True:
        action = questionary.select(
            "Deployments:",
            choices=[
                questionary.Choice("List deployments", value="list"),
                questionary.Choice("Invoke deployment", value="invoke"),
                questionary.Choice("Stream deployment", value="stream"),
                questionary.Choice("Get deployment config", value="config"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "list":
                result = client.deployments.list(limit=20)
                output(result, columns=["key", "description"], title="Deployments")

            elif action == "invoke":
                result = client.deployments.list(limit=50)
                if not result or not result.data:
                    print_info("No deployments found")
                    continue

                key = questionary.select(
                    "Select deployment:",
                    choices=[d.key for d in result.data]
                ).ask()
                if not key:
                    continue

                add_message = questionary.confirm("Add a message?", default=True).ask()
                messages = None
                if add_message:
                    content = questionary.text("Enter message:").ask()
                    if content:
                        messages = [{"role": "user", "content": content}]

                console.print("[dim]Invoking...[/dim]")
                response = client.deployments.invoke(key=key, messages=messages)
                if response and response.choices:
                    console.print(Panel(
                        response.choices[0].message.content,
                        title="Response",
                        border_style="green"
                    ))

            elif action == "stream":
                result = client.deployments.list(limit=50)
                if not result or not result.data:
                    print_info("No deployments found")
                    continue

                key = questionary.select(
                    "Select deployment:",
                    choices=[d.key for d in result.data]
                ).ask()
                if not key:
                    continue

                content = questionary.text("Enter message:").ask()
                messages = [{"role": "user", "content": content}] if content else None

                console.print("[dim]Streaming...[/dim]")
                console.print()
                with client.deployments.stream(key=key, messages=messages) as stream:
                    for event in stream:
                        if event.choices:
                            for choice in event.choices:
                                if choice.delta and choice.delta.content:
                                    console.print(choice.delta.content, end="")
                console.print("\n")

            elif action == "config":
                result = client.deployments.list(limit=50)
                if not result or not result.data:
                    print_info("No deployments found")
                    continue

                key = questionary.select(
                    "Select deployment:",
                    choices=[d.key for d in result.data]
                ).ask()
                if not key:
                    continue

                config = client.deployments.get_config(key=key)
                output(config, format="json")

        except Exception as e:
            print_error(str(e))


def datasets_menu():
    """Datasets submenu."""
    while True:
        action = questionary.select(
            "Datasets:",
            choices=[
                questionary.Choice("List datasets", value="list"),
                questionary.Choice("Create dataset", value="create"),
                questionary.Choice("View dataset", value="view"),
                questionary.Choice("Delete dataset", value="delete"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "list":
                result = client.datasets.list(limit=20)
                output(result, columns=["id", "display_name"], title="Datasets")

            elif action == "create":
                name = questionary.text("Dataset name:").ask()
                if name:
                    result = client.datasets.create(request={"display_name": name})
                    print_success(f"Created dataset: {result.id}")

            elif action == "view":
                result = client.datasets.list(limit=50)
                if not result or not result.data:
                    print_info("No datasets found")
                    continue

                dataset_id = questionary.select(
                    "Select dataset:",
                    choices=[questionary.Choice(f"{d.display_name or d.id}", value=d.id) for d in result.data]
                ).ask()
                if dataset_id:
                    dataset = client.datasets.retrieve(dataset_id=dataset_id)
                    output(dataset, format="json")

            elif action == "delete":
                result = client.datasets.list(limit=50)
                if not result or not result.data:
                    print_info("No datasets found")
                    continue

                dataset_id = questionary.select(
                    "Select dataset to delete:",
                    choices=[questionary.Choice(f"{d.display_name or d.id}", value=d.id) for d in result.data]
                ).ask()
                if dataset_id:
                    if questionary.confirm(f"Delete {dataset_id}?", default=False).ask():
                        client.datasets.delete(dataset_id=dataset_id)
                        print_success("Dataset deleted")

        except Exception as e:
            print_error(str(e))


def files_menu():
    """Files submenu."""
    while True:
        action = questionary.select(
            "Files:",
            choices=[
                questionary.Choice("List files", value="list"),
                questionary.Choice("Upload file", value="upload"),
                questionary.Choice("View file details", value="view"),
                questionary.Choice("Delete file", value="delete"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "list":
                result = client.files.list(limit=20)
                output(result, columns=["id", "file_name", "purpose"], title="Files")

            elif action == "upload":
                file_path = questionary.path("File path:").ask()
                if file_path:
                    purpose = questionary.select(
                        "Purpose:",
                        choices=["retrieval", "knowledge_datasource", "batch"]
                    ).ask()
                    with open(file_path, "rb") as f:
                        content = f.read()
                    result = client.files.create(
                        file={"file_name": file_path.split("/")[-1], "content": content},
                        purpose=purpose
                    )
                    print_success(f"Uploaded: {result.id}")

            elif action == "view":
                result = client.files.list(limit=50)
                if not result or not result.data:
                    print_info("No files found")
                    continue

                file_id = questionary.select(
                    "Select file:",
                    choices=[questionary.Choice(f"{f.file_name or f.id}", value=f.id) for f in result.data]
                ).ask()
                if file_id:
                    file_info = client.files.get(file_id=file_id)
                    output(file_info, format="json")

            elif action == "delete":
                result = client.files.list(limit=50)
                if not result or not result.data:
                    print_info("No files found")
                    continue

                file_id = questionary.select(
                    "Select file to delete:",
                    choices=[questionary.Choice(f"{f.file_name or f.id}", value=f.id) for f in result.data]
                ).ask()
                if file_id:
                    if questionary.confirm(f"Delete {file_id}?", default=False).ask():
                        client.files.delete(file_id=file_id)
                        print_success("File deleted")

        except Exception as e:
            print_error(str(e))


def knowledge_menu():
    """Knowledge bases submenu."""
    while True:
        action = questionary.select(
            "Knowledge Bases:",
            choices=[
                questionary.Choice("List knowledge bases", value="list"),
                questionary.Choice("Search knowledge base", value="search"),
                questionary.Choice("View knowledge base", value="view"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "list":
                result = client.knowledge.list(limit=20)
                output(result, columns=["id", "key", "description"], title="Knowledge Bases")

            elif action == "search":
                result = client.knowledge.list(limit=50)
                if not result or not result.data:
                    print_info("No knowledge bases found")
                    continue

                kb_id = questionary.select(
                    "Select knowledge base:",
                    choices=[questionary.Choice(f"{kb.key}", value=kb.id) for kb in result.data]
                ).ask()
                if kb_id:
                    query = questionary.text("Search query:").ask()
                    if query:
                        results = client.knowledge.search(knowledge_id=kb_id, query=query)
                        output(results, format="json")

            elif action == "view":
                result = client.knowledge.list(limit=50)
                if not result or not result.data:
                    print_info("No knowledge bases found")
                    continue

                kb_id = questionary.select(
                    "Select knowledge base:",
                    choices=[questionary.Choice(f"{kb.key}", value=kb.id) for kb in result.data]
                ).ask()
                if kb_id:
                    kb = client.knowledge.retrieve(knowledge_id=kb_id)
                    output(kb, format="json")

        except Exception as e:
            print_error(str(e))


def prompts_menu():
    """Prompts submenu."""
    while True:
        action = questionary.select(
            "Prompts:",
            choices=[
                questionary.Choice("List prompts", value="list"),
                questionary.Choice("View prompt", value="view"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "list":
                result = client.prompts.list(limit=20)
                output(result, columns=["id", "key", "description"], title="Prompts")

            elif action == "view":
                result = client.prompts.list(limit=50)
                if not result or not result.data:
                    print_info("No prompts found")
                    continue

                prompt_id = questionary.select(
                    "Select prompt:",
                    choices=[questionary.Choice(f"{p.key or p.id}", value=p.id) for p in result.data]
                ).ask()
                if prompt_id:
                    prompt = client.prompts.retrieve(prompt_id=prompt_id)
                    output(prompt, format="json")

        except Exception as e:
            print_error(str(e))


def contacts_menu():
    """Contacts submenu."""
    while True:
        action = questionary.select(
            "Contacts:",
            choices=[
                questionary.Choice("Create contact", value="create"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "create":
                external_id = questionary.text("External ID:").ask()
                if not external_id:
                    continue
                display_name = questionary.text("Display name (optional):").ask()
                email = questionary.text("Email (optional):").ask()

                kwargs = {"external_id": external_id}
                if display_name:
                    kwargs["display_name"] = display_name
                if email:
                    kwargs["email"] = email

                result = client.contacts.create(**kwargs)
                print_success(f"Created contact: {result.id}")
                output(result, format="json")

        except Exception as e:
            print_error(str(e))


def feedback_menu():
    """Feedback submenu."""
    while True:
        action = questionary.select(
            "Feedback:",
            choices=[
                questionary.Choice("Submit feedback", value="create"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        try:
            client = get_client()

            if action == "create":
                trace_id = questionary.text("Trace ID:").ask()
                if not trace_id:
                    continue
                field = questionary.text("Field name:").ask()
                if not field:
                    continue
                value = questionary.text("Value:").ask()

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
                output(result, format="json")

        except Exception as e:
            print_error(str(e))


def config_menu():
    """Configuration submenu."""
    while True:
        config = load_config()

        action = questionary.select(
            "Configuration:",
            choices=[
                questionary.Choice("Show configuration", value="show"),
                questionary.Choice("Set API key", value="api_key"),
                questionary.Choice("Set environment", value="environment"),
                questionary.Choice("Set output format", value="output_format"),
                questionary.Separator(),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back" or action is None:
            break

        if action == "show":
            table = Table(title="Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            for key, value in config.items():
                if key == "api_key" and value:
                    display = value[:20] + "..."
                else:
                    display = str(value) if value else "(not set)"
                table.add_row(key, display)
            console.print(table)

        elif action == "api_key":
            api_key = questionary.password("New API key:").ask()
            if api_key:
                config["api_key"] = api_key
                save_config(config)
                print_success("API key updated")

        elif action == "environment":
            env = questionary.select(
                "Environment:",
                choices=["production", "staging", "development"]
            ).ask()
            if env:
                config["environment"] = env
                save_config(config)
                print_success(f"Environment set to {env}")

        elif action == "output_format":
            fmt = questionary.select(
                "Output format:",
                choices=["table", "json", "yaml"]
            ).ask()
            if fmt:
                config["output_format"] = fmt
                save_config(config)
                print_success(f"Output format set to {fmt}")


def run_interactive():
    """Run interactive mode."""
    console.print(Panel.fit(
        "[bold cyan]ORQ CLI[/bold cyan] - Interactive Mode\n"
        "Navigate with arrow keys, enter to select",
        border_style="cyan"
    ))

    if not interactive_setup():
        return

    menu_handlers = {
        "deployments": deployments_menu,
        "datasets": datasets_menu,
        "files": files_menu,
        "knowledge": knowledge_menu,
        "prompts": prompts_menu,
        "contacts": contacts_menu,
        "feedback": feedback_menu,
        "config": config_menu,
    }

    while True:
        choice = show_main_menu()

        if choice == "exit" or choice is None:
            console.print("[dim]Goodbye![/dim]")
            break

        handler = menu_handlers.get(choice)
        if handler:
            handler()
