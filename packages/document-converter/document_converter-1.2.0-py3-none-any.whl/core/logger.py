import logging
import logging.config
import os
import yaml
from typing import Optional

def setup_logger(
    name: str = "document_converter",
    env: str = "development",
    config_path: str = "config/logging_config.yaml"
) -> logging.Logger:
    """
    Sets up a logger using YAML configuration.

    Args:
        name: Name of the logger.
        env: Environment profile ('development' or 'production').
        config_path: Path to the YAML configuration file.

    Returns:
        Configured logger instance.
    """
    # Create logs directory if it doesn't exist (default location in yaml)
    if not os.path.exists("logs"):
        os.makedirs("logs")

    if os.path.exists(config_path):
        with open(config_path, "rt") as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                print(f"Error loading logging config: {e}")
                # Fallback to basic config
                logging.basicConfig(level=logging.INFO)
    else:
        print(f"Logging config file not found at {config_path}. Using default.")
        logging.basicConfig(level=logging.INFO)
        # Ensure the returned logger has the correct level if basicConfig didn't set it for this specific logger
        logging.getLogger(name).setLevel(logging.INFO)

    # Get the specific logger for the environment if defined, otherwise root
    # In this design, we might want to configure the root logger based on the env
    # or return a specific named logger. 
    # For simplicity, we'll return the requested named logger, 
    # but we can apply specific env settings if needed.
    
    logger = logging.getLogger(name)
    
    # If the config defines specific loggers for 'development' or 'production',
    # we could copy their settings to our named logger, or just rely on the 
    # root logger configuration + specific overrides in the YAML.
    # A simpler approach for this specific request (profiles):
    
    if env in logging.root.manager.loggerDict:
        # If we have a logger defined for this env in YAML, use its level/handlers
        env_logger = logging.getLogger(env)
        logger.setLevel(env_logger.level)
        # Note: Handlers are usually attached to root or specific loggers.
        # If we want to inherit handlers from the 'env' logger, we'd need to add them.
        # However, a cleaner way is usually to just configure the root logger differently 
        # based on env, OR have the YAML define the 'document_converter' logger directly.
        
        # Let's stick to the plan: "Diferentes perfiles".
        # We will assume the YAML configures loggers appropriately.
        # But to make 'env' effective, we might need to select the config part.
        pass

    return logger
