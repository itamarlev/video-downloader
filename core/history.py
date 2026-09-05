"""Download history persistence, independent of any UI."""

import json
from pathlib import Path

DEFAULT_HISTORY_FILE = Path(__file__).parent.parent / "download_history.json"


class DownloadHistory:
    """Manages download history persistence."""

    def __init__(self, history_file: Path = DEFAULT_HISTORY_FILE):
        self.history_file = history_file
        self.history = []
        self.load()

    def load(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []

    def save(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def add(self, entry):
        self.history.insert(0, entry)
        self.save()

    def clear(self):
        self.history = []
        self.save()

    def get_all(self):
        return self.history
