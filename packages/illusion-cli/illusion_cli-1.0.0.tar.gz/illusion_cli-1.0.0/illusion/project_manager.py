import os
from pathlib import Path
import subprocess
from rich.prompt import Confirm
import logging

class ProjectManager:
    def __init__(self):
        self.root_dir = self.get_illusion_dir()  # Use Illusion directory
        self.active_project = None
        logging.basicConfig(level=logging.INFO, filename=self.get_log_path())

    def get_log_path(self):
        if os.name == 'nt':  # Windows
            log_dir = Path(os.getenv('TEMP', 'C:\\Temp'))
        else:  # Unix-like
            log_dir = Path('/tmp')
        log_dir.mkdir(exist_ok=True)
        return log_dir / "illusion.log"

    def get_illusion_dir(self):
        """Get the Illusion projects directory."""
        if os.name == 'nt':  # Windows
            # Use Documents folder for visible location (more user-friendly than AppData)
            documents_dir = Path(os.getenv('USERPROFILE', 'C:\\Users\\Public')) / "Illusions"
            illusion_dir = documents_dir
        else:  # Unix-like (Linux, Mac)
            illusion_dir = Path.home() / "Illusions"
        illusion_dir.mkdir(exist_ok=True)
        return illusion_dir

    def create_project(self, project_name):
        project_dir = self.root_dir / project_name
        try:
            project_dir.mkdir(exist_ok=False)
            (project_dir / ".illusion").mkdir()
            (project_dir / "README.md").write_text(f"# {project_name}\n\nCreated by ILLUSION")
            (project_dir / ".gitignore").write_text("*.pyc\n__pycache__/\n.illusion/vector.db")
            (project_dir / "src").mkdir()
            self.active_project = project_dir
            logging.debug(f"Created project {project_name} at {project_dir}")
            return f"Created project '{project_name}'"
        except FileExistsError:
            logging.error(f"Project {project_name} already exists")
            return f"Error: Project '{project_name}' already exists"
        except Exception as e:
            logging.error(f"Create project error: {str(e)}")
            return f"Error creating project: {str(e)}"

    def open_project(self, project_name):
        project_dir = self.root_dir / project_name
        if project_dir.exists() and (project_dir / ".illusion").exists():
            self.active_project = project_dir
            logging.debug(f"Opened project {project_name}")
            return f"Opened project '{project_name}'"
        logging.error(f"Project {project_name} does not exist")
        return f"Error: Project '{project_name}' does not exist or is invalid"

    def get_active_project(self):
        return self.active_project

    def write_file(self, file_path, content):
        full_path = self.active_project / file_path
        try:
            logging.debug(f"Writing file {full_path}: {content[:100]}...")
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not content or not isinstance(content, str):
                logging.error(f"Invalid content for {file_path}")
                return f"Error writing {file_path}: Invalid content"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            logging.debug(f"Created file {file_path}")
            return f"Created {file_path}"
        except Exception as e:
            logging.error(f"Write file error for {file_path}: {str(e)}")
            return f"Error writing {file_path}: {str(e)}"

    def execute_file(self, file_path):
        full_path = self.active_project / file_path
        try:
            logging.debug(f"Attempting to execute {file_path}")
            if file_path.endswith(".py"):
                python_cmd = "python3" if os.name != 'nt' else "python"
                cmd = [python_cmd, str(full_path)]
            elif file_path.endswith(".sh"):
                shell_cmd = "bash" if os.name != 'nt' else "cmd"
                cmd = [shell_cmd, "/c", str(full_path)] if os.name == 'nt' else [shell_cmd, str(full_path)]
            else:
                logging.error(f"{file_path} is not executable")
                return f"Error: {file_path} is not executable"
            if Confirm.ask(f"Run {file_path}?"):
                result = subprocess.run(cmd, cwd=self.active_project, capture_output=True, text=True)
                logging.debug(f"Execution result for {file_path}: {result.stdout or result.stderr}")
                return f"Executed {file_path}: {result.stdout or result.stderr}"
            logging.debug(f"Skipped execution of {file_path}")
            return f"Skipped execution of {file_path}"
        except Exception as e:
            logging.error(f"Execute file error for {file_path}: {str(e)}")
            return f"Error executing {file_path}: {str(e)}"
