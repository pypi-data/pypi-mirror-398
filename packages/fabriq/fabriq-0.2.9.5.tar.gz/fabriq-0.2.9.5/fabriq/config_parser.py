import yaml
from typing import Any
from dotenv import load_dotenv

class ConfigParser:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        if load_dotenv(self.config.get('env_file')):
            print("Environment variables loaded.")

    def get(self, section: str, default: Any = None) -> Any:
        """
        Get a section from the config. Returns default if not found.
        """
        return self.config.get(section, default)

    def get_nested(self, keys: list, default: Any = None) -> Any:
        """
        Get a nested value from the config using a list of keys.
        Returns default if not found.
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def as_dict(self) -> dict:
        """
        Return the entire config as a dictionary.
        """
        return self.config

# Usage example:
# parser = ConfigParser('evaluation/config.yaml')
# print(parser.get('evaluation'))
# print(parser.get('llm'))
# print(parser.get_nested(['llm', 'model_kwargs']))
# print(parser.as_dict())