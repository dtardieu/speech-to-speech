import os
import json

class ConfigManager:
    """Handles loading and managing configurations."""

    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.available_configs = self.list_config_files()
        if not self.available_configs:
            raise FileNotFoundError("No configuration files found in the configs directory.")
        self.config = self.load_config(self.available_configs[0])

    def list_config_files(self):
        """Lists all JSON configuration files in the config directory."""
        return [f for f in os.listdir(self.config_dir) if f.endswith(".json")]

    def load_config(self, config_file):
        """Loads configuration from a selected JSON file."""
        config_path = os.path.join(self.config_dir, config_file)
        with open(config_path, "r") as file:
            return json.load(file)

    def get_config(self):
        """Returns the loaded configuration."""
        return self.config
