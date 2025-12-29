import json
import os
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """
        Loads configuration from defaults, files, and environment variables.
        Priority: Env Vars > Config File > Defaults
        """
        # 1. Defaults
        self._config = {
            "app_name": "DocumentConverter",
            "version": "1.0.0",
            "environment": "development",
            "logging": {
                "level": "INFO",
                "file": "logs/app.log"
            },
            "upload_dir": "uploads",
            "output_dir": "converted",
            "profiles": {}
        }

        # 2. Load from file (YAML or JSON)
        config_path = os.getenv("CONFIG_PATH", "config/settings.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                try:
                    if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                        file_config = yaml.safe_load(f)
                    elif config_path.endswith(".json"):
                        file_config = json.load(f)
                    else:
                        print(f"Unsupported config file format: {config_path}")
                        file_config = {}
                    
                    if file_config:
                        self._deep_update(self._config, file_config)
                except Exception as e:
                    print(f"Error loading config file: {e}")

        # Load profiles
        self._load_profiles()

        # 3. Environment Variables Overrides
        # Convention: APP_SECTION_KEY (e.g., APP_LOGGING_LEVEL)
        self._override_from_env()

        # 4. Validation
        self._validate()

    def _load_profiles(self):
        """Loads conversion profiles from JSON."""
        profiles_path = os.getenv("PROFILES_PATH", "config/conversion_profiles.json")
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, "r") as f:
                    self._config["profiles"] = json.load(f)
            except Exception as e:
                print(f"Error loading profiles: {e}")

    def get_profile(self, profile_name: str = "default") -> Dict[str, Any]:
        """
        Retrieves a conversion profile.
        Falls back to 'default' if the requested profile doesn't exist.
        """
        profiles = self._config.get("profiles", {})
        if profile_name in profiles:
            return profiles[profile_name]
        
        if "default" in profiles:
            print(f"Profile '{profile_name}' not found. Using 'default'.")
            return profiles["default"]
            
        return {}


    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Recursively updates a dictionary."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _override_from_env(self):
        """Overrides configuration with environment variables."""
        # Simple mapping for demonstration. 
        # A more robust solution would iterate over all keys or use a prefix.
        
        if os.getenv("APP_ENVIRONMENT"):
            self._config["environment"] = os.getenv("APP_ENVIRONMENT")
            
        if os.getenv("APP_LOGGING_LEVEL"):
            self._config["logging"]["level"] = os.getenv("APP_LOGGING_LEVEL")

    def _validate(self):
        """Validates the configuration."""
        required_keys = ["app_name", "version", "environment"]
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        if self._config["environment"] not in ["development", "production", "testing"]:
            raise ValueError(f"Invalid environment: {self._config['environment']}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

# Global instance
settings = Settings()
