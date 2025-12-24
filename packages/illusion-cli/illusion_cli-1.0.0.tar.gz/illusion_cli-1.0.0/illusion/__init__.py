"""ILLUSION: Your Agentic Programming Assistant

ILLUSION is a powerful agentic programming assistant that helps developers
create, manage, and interact with projects using natural language commands.
"""

from .main import run
from .project_manager import ProjectManager
from .api_client import APIClient
from .context_store import ContextStore
from .git_manager import GitManager
from .ui import UI

__version__ = "1.3.0"
__all__ = ["run", "ProjectManager", "APIClient", "ContextStore", "GitManager", "UI"]
