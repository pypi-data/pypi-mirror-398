"""Utility functions for xnotify."""

import os
import socket
from typing import Any, Dict, Optional
from pathlib import Path


def get_hostname() -> str:
    """Get current hostname."""
    return socket.gethostname()


def get_username() -> str:
    """Get current username."""
    return os.getenv('USER') or os.getenv('USERNAME') or 'unknown'


def ensure_dir(path: str) -> Path:
    """
    Ensure directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def truncate_message(message: str, max_length: int = 1000) -> str:
    """
    Truncate message to maximum length.
    
    Args:
        message: Message to truncate
        max_length: Maximum length
        
    Returns:
        Truncated message
    """
    if len(message) <= max_length:
        return message
    return message[:max_length - 3] + '...'


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def format_size(bytes_size: int) -> str:
    """
    Format bytes size to human readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Dictionary to merge
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def is_valid_url(url: str) -> bool:
    """
    Check if string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL
    """
    return url.startswith(('http://', 'https://'))


def parse_bool(value: Any) -> bool:
    """
    Parse boolean value from various types.
    
    Args:
        value: Value to parse
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'on', 'enabled')
    
    if isinstance(value, int):
        return value != 0
    
    return bool(value)


def get_config_paths() -> list[Path]:
    """
    Get list of possible configuration file paths.
    
    Returns:
        List of Path objects
    """
    home = Path.home()
    
    return [
        Path.cwd() / 'xnotify.yaml',
        Path.cwd() / 'xnotify.json',
        home / '.xnotify' / 'config.yaml',
        home / '.xnotify' / 'config.json',
        home / '.config' / 'xnotify' / 'config.yaml',
        home / '.config' / 'xnotify' / 'config.json',
        Path('/etc/xnotify/config.yaml'),
        Path('/etc/xnotify/config.json'),
    ]


def find_config_file() -> Optional[Path]:
    """
    Find configuration file in default locations.
    
    Returns:
        Path to config file or None
    """
    for path in get_config_paths():
        if path.exists() and path.is_file():
            return path
    return None