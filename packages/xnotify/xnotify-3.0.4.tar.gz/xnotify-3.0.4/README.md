# xnotify

[![PyPI version](https://badge.fury.io/py/xnotify.svg)](https://badge.fury.io/py/xnotify)
[![Python Support](https://img.shields.io/pypi/pyversions/xnotify.svg)](https://pypi.org/project/xnotify/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Universal notification library with plugin support for Python. Send notifications through multiple services with a single, unified API.

## Features

- 🔌 **Plugin-based architecture** - Easy to extend and customize
- 🚀 **Multiple services supported** - Pushbullet, Ntfy, Pushover, Telegram, Discord, Slack
- ⚙️ **Flexible configuration** - JSON, YAML, or environment variables
- 🐍 **Python 3.7+** - Modern Python with type hints
- 📦 **Production ready** - Robust error handling and logging
- 🔒 **Secure** - No credentials stored in code

## Installation

### Basic installation
```bash
pip install xnotify
```

### With all optional dependencies
```bash
pip install xnotify[full]
```
    
### Individual extras
```bash
pip install xnotify[yaml]        # YAML config support
pip install xnotify[ntfy]        # YAML config support
pip install xnotify[growl]        # YAML config support
pip install xnotify[pushbullet]  # Pushbullet support
pip install xnotify[dev]  # Pushbullet support
```

## Quick Start

### Basic Usage

```python
from xnotify import XNotify

# Initialize with default config
notifier = XNotify()

# Send notification through all enabled plugins
notifier.send(
    title="Hello World",
    message="This is a test notification"
)

# Send through specific plugins
notifier.send(
    title="Hello World",
    message="This is a test notification",
    plugins=['ntfy', 'telegram']
)
```

### Configuration

Create a configuration file (`~/.xnotify/config.yaml` or `~/.config/xnotify/config.yaml`):

```yaml
plugins:
  ntfy:
    enabled: true
    servers:
      - https://ntfy.sh
    topic: my-notifications
    
  pushbullet:
    enabled: true
    api_key: your_api_key_here
    
  pushover:
    enabled: true
    user_key: your_user_key
    api_token: your_api_token
    
  telegram:
    enabled: true
    bot_token: your_bot_token
    chat_id: your_chat_id
    
  discord:
    enabled: true
    webhook_url: your_webhook_url
    
  slack:
    enabled: true
    webhook_url: your_webhook_url
    channel: "#notifications"
```

### Environment Variables

You can also configure plugins using environment variables:

```bash
# Pushbullet
export XNOTIFY_PUSHBULLET_API_KEY="your_api_key"

# Pushover
export XNOTIFY_PUSHOVER_USER_KEY="your_user_key"
export XNOTIFY_PUSHOVER_API_TOKEN="your_api_token"

# Telegram
export XNOTIFY_TELEGRAM_BOT_TOKEN="your_bot_token"
export XNOTIFY_TELEGRAM_CHAT_ID="your_chat_id"

# Discord
export XNOTIFY_DISCORD_WEBHOOK_URL="your_webhook_url"

# Slack
export XNOTIFY_SLACK_WEBHOOK_URL="your_webhook_url"

# Ntfy
export XNOTIFY_NTFY_SERVERS="https://ntfy.sh,https://ntfy.example.com"
export XNOTIFY_NTFY_TOPIC="my-topic"
```

## Supported Services

### Ntfy (Free)
- Public server: https://ntfy.sh
- Self-hosted option available
- No registration required

### Pushbullet (Freemium)
- Free tier: 500 pushes/month
- Requires API key

### Pushover (Paid)
- 30-day free trial
- One-time purchase per platform

### Telegram (Free)
- Requires bot token
- Unlimited messages

### Discord (Free)
- Webhook-based
- Unlimited messages

### Slack (Freemium)
- Webhook-based
- Free tier available

## Advanced Usage

### Plugin-specific Parameters

```python
# Ntfy with advanced features
notifier.send(
    title="Alert",
    message="Server is down",
    plugins=['ntfy'],
    priority=5,  # High priority
    tags=['warning', 'server'],
    click="https://status.example.com",
    icon="https://example.com/icon.png"
)

# Telegram with custom formatting
notifier.send(
    title="Update",
    message="Deployment completed",
    plugins=['telegram'],
    parse_mode='Markdown',
    disable_notification=False
)

# Discord with color
notifier.send(
    title="Success",
    message="Build completed",
    plugins=['discord'],
    color=0x00FF00  # Green
)
```

### Enable/Disable Plugins

```python
# Disable a plugin
notifier.disable_plugin('pushbullet')

# Enable a plugin
notifier.enable_plugin('pushbullet')

# Check plugin status
status = notifier.get_plugin_status()
print(status)  # {'ntfy': True, 'pushbullet': False, ...}
```

### Error Handling

```python
from xnotify.plugins.base import SendError, ConfigurationError

try:
    results = notifier.send(
        title="Test",
        message="Testing error handling"
    )
    
    # Check which plugins succeeded
    for plugin, success in results.items():
        if not success:
            print(f"Failed to send via {plugin}")
            
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except SendError as e:
    print(f"Send error: {e}")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/cumulus13/xnotify.git
cd xnotify

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black xnotify tests
flake8 xnotify tests
mypy xnotify
```

### Creating a Plugin

```python
from xnotify.plugins.base import NotificationPlugin, SendError

class MyPlugin(NotificationPlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
    
    def validate_config(self):
        if not self.api_key:
            raise ConfigurationError("API key required")
        return True
    
    def send(self, title, message, **kwargs):
        if not self.is_enabled():
            return False
        
        try:
            self.validate_config()
            # Your sending logic here
            return True
        except Exception as e:
            raise SendError(f"Failed to send: {e}")
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

**[Hadi Cahyadi](mailto:cumulus13@gmail.com)**
- Email: cumulus13@gmail.com
- GitHub: [@cumulus13](https://github.com/cumulus13)
    
[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 
[Support me on Patreon](https://www.patreon.com/cumulus13)

## Credits

Original code inspiration from various notification libraries. Completely rewritten for production use.