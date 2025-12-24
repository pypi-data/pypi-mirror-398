import sys
import os
import json
from pathlib import Path
from openai import OpenAI
import logging
import re

class APIClient:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, filename=self.get_log_path())
        # Use config manager to get configuration
        from illusion.config_manager import ConfigManager
        config_mgr = ConfigManager()
        config_file = config_mgr.config_file

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}. Please run 'illusion config' to set up your configuration.")

        # Import config dynamically
        sys.path.insert(0, str(config_file.parent))
        try:
            import config
            self.api_key = config.OPENROUTER_API_KEY
            self.model = config.MODEL
            self.provider = config.LLM_PROVIDER
        except ImportError as e:
            raise ImportError(f"Error importing config: {e}. Ensure config.py is properly formatted.")
        finally:
            sys.path.pop(0)

        # Set defaults if not configured
        if not self.api_key:
            raise ValueError("OpenRouter API key not set in config.py. Please run 'illusion config' to configure.")
        if not self.model:
            self.model = "x-ai/grok-4.1-fast:free"
        if not self.provider:
            self.provider = "openrouter"

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def get_log_path(self):
        if os.name == 'nt':  # Windows
            log_dir = Path(os.getenv('TEMP', 'C:\\Temp'))
        else:  # Unix-like
            log_dir = Path('/tmp')
        log_dir.mkdir(exist_ok=True)
        return log_dir / "illusion.log"

    def get_project_file_structure(self, project_dir):
        """Get a comprehensive file structure of the project."""
        structure = []
        src_dir = project_dir / "src"
        if src_dir.exists():
            for p in src_dir.rglob("*"):
                if p.is_file():
                    structure.append(str(p.relative_to(project_dir)))
        else:
            structure.append("No src/ directory yet.")
        if not structure:
            structure.append("Project is empty.")
        return "\n".join(structure)

    def get_project_file_contents(self, project_dir, max_length=1000):
        """Get contents of existing files in the project for context."""
        contents = []
        src_dir = project_dir / "src"
        if src_dir.exists():
            for p in src_dir.rglob("*"):
                if p.is_file():
                    try:
                        with open(p, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        if len(file_content) > max_length:
                            file_content = file_content[:max_length] + "... (truncated)"
                        contents.append(f"File: {p.relative_to(project_dir)}\nContent:\n{file_content}\n")
                    except Exception as e:
                        contents.append(f"File: {p.relative_to(project_dir)}\nError reading: {str(e)}\n")
        return "\n".join(contents) if contents else "No existing files."

    def process_prompt(self, prompt, project_dir, chat_history):
        try:
            # MCP: Include chat history, file structure, and current file contents
            from illusion.context_store import ContextStore
            cs = ContextStore()
            history_context = cs.get_context_summary(project_dir)
            file_structure = self.get_project_file_structure(project_dir)
            file_contents = self.get_project_file_contents(project_dir)
            system_prompt = (
                "You are an agentic programming assistant implementing Module Content Protocol (MCP). "
                "You have full context of the current project state. Use the provided file contents to make precise updates without losing existing functionality or styling. "
                "Generate code or perform CRUD operations for the project. "
                "Return a JSON object with: "
                "'message' (description of the action), "
                "'files' (dictionary of file paths relative to src/ and their FULL updated contents), "
                "'executable' (boolean, true if any file is executable like .py or .sh), "
                "'clarify' (boolean, true if clarification is needed), "
                "'question' (specific question if clarify is true). "
                "Place all files in the src/ directory (e.g., src/index.html, src/css/style.css). "
                "For executable files (.py, .sh), set executable: true. "
                "IMPORTANT: When updating existing files, provide the COMPLETE updated file content, not just changes. "
                "Preserve all existing code and styling unless explicitly asked to remove it. "
                "For example, if updating a button's color, keep all existing padding, classes, and other properties. "
                "If the prompt starts with 'Clarification:', treat it as a response to the previous question (e.g., 'Clarification: yes' means overwrite or proceed as requested). "
                "If the prompt conflicts with existing files, set clarify: true and ask a specific question (e.g., 'Overwrite src/index.html?'). "
                "If the prompt is ambiguous, set clarify: true with a relevant question. "
                f"Recent chat history (for context, not file existence):\n{history_context}\n"
                f"Current src/ structure:\n{file_structure}\n"
                f"Current file contents (use this to make precise updates):\n{file_contents}"
            )

            logging.debug(f"Sending prompt: {prompt}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"In project {project_dir.name}, {prompt}"}
                ]
            )
            content = response.choices[0].message.content
            logging.debug(f"Raw response: {content[:1000]}...")

            # Robust JSON parsing
            try:
                content = re.sub(r'^```(?:json)?\s*|\s*```$', '', content, flags=re.MULTILINE).strip()
                result = json.loads(content)
                if not isinstance(result, dict) or "message" not in result:
                    logging.error(f"Invalid response format: {content[:100]}")
                    return {"message": f"Invalid response format: {content[:100]}", "files": {}, "executable": False, "clarify": False}
                result.setdefault("files", {})
                result.setdefault("clarify", False)
                result.setdefault("question", "")
                result.setdefault("executable", any(k.endswith((".py", ".sh")) for k in result["files"]))
                result["files"] = {f"src/{k}" if not k.startswith("src/") else k: v for k, v in result["files"].items()}
                logging.debug(f"Parsed response: {result}")
                return result
            except json.JSONDecodeError as e:
                logging.error(f"JSON parse error: {str(e)} - Content: {content[:100]}")
                return {"message": f"Failed to parse response: {content[:100]}", "files": {}, "executable": False, "clarify": False}
        except Exception as e:
            logging.error(f"API error: {str(e)}")
            return {"message": f"Error processing prompt: {str(e)}", "files": {}, "executable": False, "clarify": False}
