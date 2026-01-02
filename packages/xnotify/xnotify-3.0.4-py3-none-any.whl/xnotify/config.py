"""Configuration management for xnotify."""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager."""
    
    DEFAULT_CONFIG = {
        'plugins': {
            'growl': {
                'enabled': True,
            },
            'ntfy': {
                'enabled': True,
                'servers': ['https://ntfy.sh'],
                'topic': 'xnotify',
                'timeout': 10,
            },
            'pushbullet': {
                'enabled': False,
                'api_key': '',
                'timeout': 10,
            },
            'pushover': {
                'enabled': False,
                'user_key': '',
                'api_token': '',
                'timeout': 10,
            },
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_id': '',
                'timeout': 10,
            },
            'discord': {
                'enabled': False,
                'webhook_url': '',
                'username': 'xnotify',
                'timeout': 10,
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': '',
                'username': 'xnotify',
                'timeout': 10,
            },
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': None,
        },
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self._config = self.DEFAULT_CONFIG.copy()
        logger.debug(f"self._config [0]: {self._config}")
        
        if config_file:
            self.load_from_file(config_file)
        else:
            # Try to load from default locations
            self._load_default_config()
        
        # Load from environment variables
        self._load_from_env()

        logger.debug(f"self._config [1]: {self._config}")
    
    def _load_default_config(self):
        """Try to load configuration from default locations."""
        default_paths = [
            Path.home() / '.xnotify' / 'config.yaml',
            Path.home() / '.xnotify' / 'config.json',
            Path.home() / '.config' / 'xnotify' / 'config.yaml',
            Path.home() / '.config' / 'xnotify' / 'config.json',
            Path('/etc/xnotify/config.yaml'),
            Path('/etc/xnotify/config.json'),
        ]
        
        for path in default_paths:
            if path.exists():
                try:
                    self.load_from_file(str(path))
                    logger.info(f"Loaded configuration from: {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")
    
    def load_from_file(self, config_file: str):
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        path = Path(config_file)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        if path.suffix in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
            with open(path, 'r') as f:
                config = yaml.safe_load(f)  # type: ignore
        elif path.suffix == '.json':
            with open(path, 'r') as f:
                config = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")
        
        self._merge_config(config)
    
    def _merge_config(self, config: Dict[str, Any]):
        """Merge configuration with defaults."""
        self._deep_update(self._config, config)
    
    @staticmethod
    def _deep_update(base: Dict, update: Dict):
        """Deep update dictionary."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                Config._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Pushbullet
        if api_key := os.getenv('XNOTIFY_PUSHBULLET_API_KEY'):
            self._config['plugins']['pushbullet']['api_key'] = api_key
            self._config['plugins']['pushbullet']['enabled'] = True
        
        # Pushover
        if user_key := os.getenv('XNOTIFY_PUSHOVER_USER_KEY'):
            self._config['plugins']['pushover']['user_key'] = user_key
        if api_token := os.getenv('XNOTIFY_PUSHOVER_API_TOKEN'):
            self._config['plugins']['pushover']['api_token'] = api_token
            self._config['plugins']['pushover']['enabled'] = True
        
        # Telegram
        if bot_token := os.getenv('XNOTIFY_TELEGRAM_BOT_TOKEN'):
            self._config['plugins']['telegram']['bot_token'] = bot_token
        if chat_id := os.getenv('XNOTIFY_TELEGRAM_CHAT_ID'):
            self._config['plugins']['telegram']['chat_id'] = chat_id
            self._config['plugins']['telegram']['enabled'] = True
        
        # Discord
        if webhook_url := os.getenv('XNOTIFY_DISCORD_WEBHOOK_URL'):
            self._config['plugins']['discord']['webhook_url'] = webhook_url
            self._config['plugins']['discord']['enabled'] = True

        # Slack
        if webhook_url := os.getenv('XNOTIFY_SLACK_WEBHOOK_URL'):
            self._config['plugins']['slack']['webhook_url'] = webhook_url
            self._config['plugins']['slack']['enabled'] = True
        
        # Ntfy
        if servers := os.getenv('XNOTIFY_NTFY_SERVERS'):
            self._config['plugins']['ntfy']['servers'] = [s.strip() for s in servers.split(',')]
        if topic := os.getenv('XNOTIFY_NTFY_TOPIC'):
            self._config['plugins']['ntfy']['topic'] = topic

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value

    def save_to_file(self, config_file: str):
        """
        Save configuration to file.
        
        Args:
            config_file: Path to save configuration
        """
        path = Path(config_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
            with open(path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)  # type: ignore
        elif path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(self._config, f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")
        
        logger.info(f"Configuration saved to: {path}")
