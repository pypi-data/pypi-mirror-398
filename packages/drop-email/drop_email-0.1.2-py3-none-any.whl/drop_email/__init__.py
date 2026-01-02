"""
drop_email - Send data as beautiful HTML emails
"""

from .email_sender import send
from .config import get_config, load_config, init_config, get_config_path

__version__ = "0.1.2"
__all__ = ["send", "get_config", "load_config", "init_config", "get_config_path"]

