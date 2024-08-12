import json
import threading
import os

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    cls._instance.module_config = {}
        return cls._instance

    def init_app(self, app):
        self.app = app
        self.load_config()

    def load_config(self):
        with self.app.app_context():
            mod_config_path = self.app.config['MOD_CONFIG_PATH']
            if os.path.exists(mod_config_path):
                with open(mod_config_path, 'r') as f:
                    self.module_config = json.load(f)
            else:
                self.module_config = {"MODULE_LIST": []}

    def get_module_config(self):
        return self.module_config

    def reload_config(self):
        self.load_config()