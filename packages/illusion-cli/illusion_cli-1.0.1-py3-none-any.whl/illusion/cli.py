import sys
import os
from pathlib import Path
from .ui import UI
from .project_manager import ProjectManager
from .api_client import APIClient
from .context_store import ContextStore
from .git_manager import GitManager
from .config_manager import ConfigManager

def main():
    """Main entry point for the illusion command."""
    import sys

    # Handle subcommands
    if len(sys.argv) > 1:
        if sys.argv[1] == "--version" or sys.argv[1] == "-v":
            # Show version information
            from illusion import __version__
            print(f"illusion-cli version {__version__}")
            return
        elif sys.argv[1] == "config":
            # Run config command directly
            config_command()
            return

    # Normal execution
    from .main import run
    run()

def config_command():
    """Entry point for the illusion-config command."""
    config_mgr = ConfigManager()
    config_mgr.run_config_interface()

if __name__ == "__main__":
    main()
