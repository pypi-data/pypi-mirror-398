import json
import os
from pathlib import Path
import sqlite3
import logging
from datetime import datetime

class ContextStore:
    def __init__(self):
        if os.name == 'nt':  # Windows
            log_dir = Path(os.getenv('TEMP', 'C:\\Temp'))
        else:  # Unix-like
            log_dir = Path('/tmp')
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, filename=log_dir / "illusion.log")

    def save_chat_history(self, project_dir, prompt, response):
        history_file = project_dir / ".illusion" / "chat_history.json"
        history = []
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []
        status = "succeeded" if "Created" in response or "Executed" in response else "failed"
        history.append({
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "clarify": False  # Default, overridden in ui.py for clarifications
        })
        # Keep only last 50 entries to prevent file from growing too large
        if len(history) > 50:
            history = history[-50:]
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
        logging.debug(f"Saved chat history to {history_file}")
        return "Saved chat history"

    def get_chat_history(self, project_dir):
        history_file = project_dir / ".illusion" / "chat_history.json"
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        logging.debug(f"No chat history found at {history_file}")
        return []

    def get_context_summary(self, project_dir, max_entries=10):
        """Get a summarized context of recent interactions."""
        history = self.get_chat_history(project_dir)
        if not history:
            return "No previous interactions."
        recent = history[-max_entries:]
        summary = []
        for h in recent:
            summary.append(f"User: {h['prompt'][:100]}... Assistant: {h['response'][:100]}...")
        return "\n".join(summary)

    def init_project_db(self, project_dir):
        db_path = project_dir / ".illusion" / "vector.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS embeddings (id INTEGER PRIMARY KEY, vector BLOB)")
        conn.close()
        logging.debug(f"Initialized vector DB at {db_path}")
        return "Initialized project vector DB"
