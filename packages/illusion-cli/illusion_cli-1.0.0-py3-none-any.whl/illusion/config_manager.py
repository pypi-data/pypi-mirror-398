import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import sys

class ConfigManager:
    def __init__(self):
        self.console = Console(soft_wrap=True)
        self.config_dir = self.get_config_dir()
        self.config_file = self.config_dir / "config.py"

    def get_config_dir(self):
        """Get the Illusion configuration directory."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.getenv('APPDATA', 'C:\\Users\\Public')) / "Illusion"
        else:  # Unix-like
            config_dir = Path.home() / ".illusion"
        config_dir.mkdir(exist_ok=True)
        return config_dir

    def get_default_config(self):
        """Return default configuration content."""
        return '''# ILLUSION Configuration File
# Paste your OpenRouter API key here
OPENROUTER_API_KEY = ""

# Choose the model you want to use (e.g., "deepseek/deepseek-r1:free", "anthropic/claude-3-haiku", etc.)
MODEL = "x-ai/grok-4.1-fast:free"

# LLM Provider (currently only openrouter is supported)
LLM_PROVIDER = "openrouter"
'''

    def create_default_config(self):
        """Create default configuration file."""
        try:
            self.config_file.write_text(self.get_default_config())
            self.console.print(f"[green]Created default config at: {self.config_file}[/]")
            return True
        except Exception as e:
            self.console.print(f"[red]Error creating config: {str(e)}[/]")
            return False

    def edit_config(self):
        """Edit configuration file."""
        if not self.config_file.exists():
            if not self.create_default_config():
                return

        # Read current config
        with open(self.config_file, "r") as f:
            content = f.read()

        # Display current config
        self.console.print(Panel(f"Current Configuration:\n{content}", title="Current Config", border_style="blue"))

        # Ask what to edit
        self.console.print("[bold yellow]Configuration Options:[/]")
        self.console.print("1. OpenRouter API Key")
        self.console.print("2. Model")
        self.console.print("3. LLM Provider")
        self.console.print("4. View current config")
        self.console.print("5. Exit")

        while True:
            choice = Prompt.ask("[bold cyan]Edit option (1-5)>[/]").strip()

            if choice == "1":
                api_key = Prompt.ask("[bold cyan]Enter OpenRouter API Key[/]")
                content = self.update_config_value(content, "OPENROUTER_API_KEY", f'"{api_key}"')
            elif choice == "2":
                model = Prompt.ask("[bold cyan]Enter Model[/]", default="x-ai/grok-4.1-fast:free")
                content = self.update_config_value(content, "MODEL", f'"{model}"')
            elif choice == "3":
                self.console.print("[yellow]Note: Currently only 'openrouter' provider is supported[/]")
                provider = Prompt.ask("[bold cyan]Enter LLM Provider[/]", default="openrouter")
                content = self.update_config_value(content, "LLM_PROVIDER", f'"{provider}"')
            elif choice == "4":
                self.console.print(Panel(f"Current Configuration:\n{content}", title="Current Config", border_style="blue"))
                continue
            elif choice == "5":
                break
            else:
                self.console.print("[red]Invalid choice. Please enter 1-5.[/]")
                continue

            # Save changes
            try:
                with open(self.config_file, "w") as f:
                    f.write(content)
                self.console.print(f"[green]Configuration updated successfully![/]")
                self.console.print(Panel(f"Updated Configuration:\n{content}", title="Updated Config", border_style="green"))
            except Exception as e:
                self.console.print(f"[red]Error saving config: {str(e)}[/]")

            break

    def update_config_value(self, content, key, new_value):
        """Update a configuration value in the content."""
        import re
        pattern = rf'({key}\s*=\s*).*'
        replacement = f'\\1{new_value}'
        return re.sub(pattern, replacement, content)

    def run_config_interface(self):
        """Run the configuration interface."""
        self.console.print(Panel("ILLUSION Configuration Manager", style="bold green"))

        if not self.config_file.exists():
            self.console.print("[yellow]No configuration file found. Creating default config...[/]")
            self.create_default_config()

        self.edit_config()
        self.console.print("[green]Configuration manager exiting.[/]")
