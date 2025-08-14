
import json, os
from typing import Any, Dict, List

DB_PATH = os.getenv("USER_STORE_PATH", "./data/user_history.json")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

class UserHistoryStore:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f)

    def _read(self) -> Dict[str, Any]:
        with open(self.path, "r") as f:
            return json.load(f)

    def get_user_history(self, user_id: str) -> List[dict]:
        return self._read().get(user_id, [])

    def append_brief(self, user_id: str, brief: dict):
        data = self._read()
        data.setdefault(user_id, []).append(brief)
        with open(self.path, "w") as f:
            json.dump(data, f, default=str)
