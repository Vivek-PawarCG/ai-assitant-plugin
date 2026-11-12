import os
import json
import sys

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "gemini-3.8-flash-lite",
    "auto_copy_responses": True,
    "temperature": 0.7,
}

class ConfigManager:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or self._default_data_dir()
        self.config_path = os.path.join(self.data_dir, "config.json")
        self.config = self.load()

    def _default_data_dir(self):
        appdata = os.environ.get("APPDATA")
        if appdata:
            path = os.path.join(appdata, "Fenn", "plugins", "gemini-assistant")
        else:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(path, exist_ok=True)
        return path

    def set_data_dir(self, path):
        if path and os.path.isdir(path):
            self.data_dir = path
            self.config_path = os.path.join(self.data_dir, "config.json")
            self.config = self.load()

    def load(self):
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(data)
                    return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def has_api_key(self):
        key = self.get("api_key", "").strip()
        return len(key) > 10
