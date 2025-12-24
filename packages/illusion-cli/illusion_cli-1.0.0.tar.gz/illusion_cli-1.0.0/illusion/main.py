"""Main entry point for the illusion package."""

from .cli import main
from .project_manager import ProjectManager
from .api_client import APIClient
from .context_store import ContextStore
from .git_manager import GitManager
from .ui import UI

def run():
    """Run the illusion application."""
    # Initialize modules
    pm = ProjectManager()
    api_client = APIClient()
    context_store = ContextStore()
    git_manager = GitManager()
    ui = UI(pm, api_client, context_store, git_manager)

    # Run the UI
    ui.run()

if __name__ == "__main__":
    run()
