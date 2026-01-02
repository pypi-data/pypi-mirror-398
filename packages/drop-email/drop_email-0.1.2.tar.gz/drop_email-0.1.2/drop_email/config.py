"""
Configuration management for drop_email
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_FILE_NAME = "config.yaml"
CONFIG_PATH_ENV = "DROP_EMAIL_CONFIG"


def _get_default_config_path() -> Path:
    """
    Get default configuration file path using XDG standard.
    
    Priority:
    1. XDG_CONFIG_HOME/drop_email/config.yaml (if XDG_CONFIG_HOME is set)
    2. ~/.config/drop_email/config.yaml (fallback to standard XDG location)
    
    This is more stable than ~/.drop_email because XDG_CONFIG_HOME
    can be set to a fixed location that doesn't depend on home directory changes.
    """
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "drop_email" / CONFIG_FILE_NAME
    else:
        # Use standard XDG location: ~/.config/drop_email/config.yaml
        return Path.home() / ".config" / "drop_email" / CONFIG_FILE_NAME


def get_config_path() -> Path:
    """
    Get the configuration file path.
    
    Priority order:
    1. Environment variable DROP_EMAIL_CONFIG (absolute path recommended for stability)
    2. XDG_CONFIG_HOME/drop_email/config.yaml or ~/.config/drop_email/config.yaml
    
    For best stability when home directory may change, set DROP_EMAIL_CONFIG
    to an absolute path, e.g.:
        export DROP_EMAIL_CONFIG="/path/to/your/config.yaml"
    
    Returns:
        Path to configuration file
    """
    # Check environment variable first (highest priority)
    env_config = os.getenv(CONFIG_PATH_ENV)
    if env_config:
        env_path = Path(env_config).expanduser().resolve()
        # If env var is set, use it (will be created if doesn't exist)
        return env_path
    
    # Default: use XDG standard location
    return _get_default_config_path()


def create_default_config(config_path: Optional[Path] = None) -> Path:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path to create config file (uses get_config_path() if None)
    
    Returns:
        Path to the created configuration file
    """
    if config_path is None:
        config_path = get_config_path()
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "email": {
            "sender": {
                "address": "your_email@example.com",
                "password": "your_app_password",  # For Gmail, use App Password
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
            },
            "receivers": [
                "receiver1@example.com",
                "receiver2@example.com",
            ]
        }
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    return config_path


def init_config(force: bool = False, config_path: Optional[Path] = None) -> Path:
    """
    Initialize configuration file.
    
    Creates the configuration file at the location determined by get_config_path()
    (defaults to XDG_CONFIG_HOME/drop_email/config.yaml or ~/.config/drop_email/config.yaml).
    
    For a fixed location that doesn't depend on home directory, set the
    DROP_EMAIL_CONFIG environment variable to an absolute path.
    
    Args:
        force: If True, overwrite existing config file
        config_path: Optional path to create config (uses get_config_path() if None)
    
    Returns:
        Path to the configuration file
    """
    if config_path is None:
        config_path = get_config_path()
    
    if config_path.exists() and not force:
        print(f"Configuration file already exists at: {config_path}")
        print("Use force=True to overwrite it.")
        return config_path
    
    created_path = create_default_config(config_path)
    print(f"Configuration file created at: {created_path}")
    print("Please edit the file with your email settings:")
    print(f"  - Sender email and password")
    print(f"  - SMTP server settings")
    print(f"  - Receiver email addresses")
    
    return created_path


def load_config(config_path: Optional[Path] = None) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file (uses default if None)
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file doesn't exist (will not auto-create)
    """
    if config_path is None:
        config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at: {config_path}\n"
            f"Please run 'drop_email init' or 'drop_email.config.init_config()' "
            f"to create the configuration file."
        )
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config


def get_config() -> Dict:
    """Get the current configuration."""
    return load_config()


def get_sender_config() -> Dict:
    """Get sender email configuration."""
    config = get_config()
    return config.get("email", {}).get("sender", {})


def get_receivers() -> List[str]:
    """Get list of receiver email addresses."""
    config = get_config()
    return config.get("email", {}).get("receivers", [])

