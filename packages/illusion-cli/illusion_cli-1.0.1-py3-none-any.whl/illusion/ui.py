import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

class UI:
    def __init__(self, project_manager, api_client, context_store, git_manager):
        self.console = Console(soft_wrap=True)
        self.pm = project_manager
        self.api_client = api_client
        self.context_store = context_store
        self.git_manager = git_manager
        self.last_prompt = None  # Track last prompt for clarification

    def run(self):
        self.console.print(Panel("Welcome to ILLUSION: Your Agentic Programming Assistant", style="bold green"))
        while True:
            command = Prompt.ask("[bold cyan]illusion>[/]", default="help").strip().lower()
            if command == "help":
                self.show_help()
            elif command == "exit":
                self.console.print("[green]Exiting ILLUSION. Goodbye![/]")
                break
            elif command.startswith("np "):
                project_name = command[3:].strip()
                if project_name:
                    self.console.print(self.pm.create_project(project_name))
                    self.git_manager.init_repo(self.pm.get_active_project())
                else:
                    self.console.print("[red]Error: Project name required.[/]")
            elif command.startswith("op "):
                project_name = command[3:].strip()
                if project_name:
                    self.console.print(self.pm.open_project(project_name))
                else:
                    self.console.print("[red]Error: Project name required.[/]")
            elif command == "config":
                # Use the config manager for configuration
                from illusion.config_manager import ConfigManager
                config_mgr = ConfigManager()
                config_mgr.run_config_interface()
            elif command == "illusion":
                if not self.pm.get_active_project():
                    self.console.print("[red]Error: No project open. Use 'op <project_name>' first.[/]")
                else:
                    self.run_chat_interface()
            else:
                self.console.print("[red]Unknown command. Type 'help' for available commands.[/]")

    def show_help(self):
        table = Table(title="ILLUSION Commands", style="bold magenta")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        table.add_row("np <project_name>", "Create a new project")
        table.add_row("op <project_name>", "Open an existing project")
        table.add_row("config", "View/edit settings (API key, LLM provider)")
        table.add_row("illusion", "Open chat interface for the active project")
        table.add_row("help", "Show this help menu")
        table.add_row("exit", "Exit ILLUSION")
        self.console.print(table)

    def run_chat_interface(self):
        project_name = self.pm.get_active_project().name
        self.console.print(Panel(f"Chat Interface for {project_name}", style="bold blue"))
        self.last_prompt = None
        while True:
            prompt = Prompt.ask(f"[bold blue]illusion[{project_name}]>[/]", default="exit").strip()
            if prompt.lower() == "exit":
                self.console.print("[green]Exiting chat interface.[/]")
                break
            history = self.context_store.get_chat_history(self.pm.get_active_project())
            # If last response was a clarification, append user input as clarification
            if self.last_prompt and history and history[-1].get("clarify", False):
                combined_prompt = f"{self.last_prompt}\nClarification: {prompt}"
            else:
                combined_prompt = prompt
                self.last_prompt = prompt
            response = self.api_client.process_prompt(combined_prompt, self.pm.get_active_project(), history)
            if response.get("clarify", False):
                self.console.print(Panel(f"[yellow]Clarification needed: {response['question']}[/]", title="Clarification", border_style="yellow"))
                history.append({"prompt": combined_prompt, "response": response["question"], "clarify": True, "status": "pending"})
                self.context_store.save_chat_history(self.pm.get_active_project(), combined_prompt, response["question"])
                continue
            if "Error" in response["message"] or "Failed" in response["message"]:
                self.console.print(f"[red]{response['message']}[/]")
            else:
                self.console.print(f"[green]{response['message']}[/]")
            if response.get("files"):
                for file_path, content in response["files"].items():
                    self.console.print(f"[yellow]Generating {file_path}[/]")
                    result = self.pm.write_file(file_path, content)
                    self.console.print(f"[green]{result}[/]")
                self.console.print(self.git_manager.commit_changes(self.pm.get_active_project(), list(response["files"].keys())))
                if response.get("executable", False):
                    for file_path in response["files"]:
                        if file_path.endswith((".py", ".sh")):
                            self.console.print(self.pm.execute_file(file_path))
            else:
                self.console.print("[yellow]No files generated.[/]")
            self.context_store.save_chat_history(self.pm.get_active_project(), combined_prompt, response["message"])
