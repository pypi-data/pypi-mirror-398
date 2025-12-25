"""
Load and validate bot configuration from YAML.

Supports environment variable substitution via ${VAR_NAME}.
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    YAML configuration loader with environment variable substitution.
    
    Supports ${VAR_NAME} syntax for env vars. Validates required sections.
    """
    
    # Required environment variables (must be set)
    REQUIRED_ENV_VARS = [
        "TELEGRAM_TOKEN",
        "GIGACHAT_KEY",
        "YANDEX_API_KEY",
        "YANDEX_FOLDER_ID"
    ]
    
    @staticmethod
    def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
        """
        Load YAML configuration with environment variable substitution.
        
        Args:
            config_path: Path to config YAML file (default: "config.yaml")
        
        Returns:
            Dictionary with parsed configuration
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If required env var is missing or required section is missing
        
        Example:
            >>> config = ConfigLoader.load_config("config.yaml")
            >>> config["telegram"]["token"]
            "123456:ABC-DEF..."
        """
        # Check if config file exists
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        logger.info(f"Loading config from: {config_path}")
        
        # Load YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            raise ValueError("Config file is empty or invalid YAML")
        
        # Substitute environment variables
        config = ConfigLoader._substitute_env_vars(config)
        
        # Validate required sections
        ConfigLoader._validate_config(config)
        
        return config
    
    @staticmethod
    def _substitute_env_vars(obj: Any) -> Any:
        """
        Recursively substitute environment variables in config.
        
        Syntax: ${VAR_NAME} → os.getenv("VAR_NAME")
        
        Args:
            obj: Config object (dict, list, str, or primitive)
        
        Returns:
            Object with substituted values
        
        Raises:
            ValueError: If required env var is missing
        """
        if isinstance(obj, dict):
            # Recursively process dict values
            return {k: ConfigLoader._substitute_env_vars(v) for k, v in obj.items()}
        
        elif isinstance(obj, list):
            # Recursively process list items
            return [ConfigLoader._substitute_env_vars(item) for item in obj]
        
        elif isinstance(obj, str):
            # Find all ${VAR_NAME} patterns
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                
                # Check if required var is missing
                if var_name in ConfigLoader.REQUIRED_ENV_VARS:
                    if var_name not in os.environ:
                        raise ValueError(f"Missing required environment variable: {var_name}")
                    return os.environ[var_name]
                
                # Optional var (e.g., REDIS_URL)
                value = os.getenv(var_name)
                if value is not None:
                    return value
                else:
                    # Optional var not set → return empty string
                    # This handles both cases: entire string is placeholder or part of larger string
                    return ""
            
            # Replace all occurrences
            result = re.sub(pattern, replace_var, obj)
            return result
        
        else:
            # Primitive type (int, bool, etc.) → return as is
            return obj
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """
        Validate that required config sections exist.
        
        Args:
            config: Parsed configuration dictionary
        
        Raises:
            ValueError: If required section is missing
        """
        required_sections = ["telegram", "orchestrator", "modes"]
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required config section: {section}")
        
        logger.info("✅ Config validation passed")

