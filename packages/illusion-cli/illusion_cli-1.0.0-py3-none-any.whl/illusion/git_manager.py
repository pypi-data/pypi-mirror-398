import os
from pathlib import Path
import subprocess

class GitManager:
    def __init__(self):
        pass

    def init_repo(self, project_dir):
        try:
            result = subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True, text=True)
            return "Initialized Git repository"
        except subprocess.CalledProcessError as e:
            return f"Error initializing Git: {e.stderr}"
        except FileNotFoundError:
            return "Git not installed or not in PATH"

    def commit_changes(self, project_dir, files):
        try:
            subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True, text=True)
            file_list = ", ".join(files) if files else "Updated files"
            message = f"Created {file_list}"
            subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True, capture_output=True, text=True)
            return f"Committed changes: {message}"
        except subprocess.CalledProcessError as e:
            return f"Error committing changes: {e.stderr}"
        except FileNotFoundError:
            return "Git not installed or not in PATH"
