# DRF Discord Handler

A Django REST Framework package that automatically sends detailed exception notifications to Discord channels when errors occur in your API.

![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)
![Django Version](https://img.shields.io/badge/django-6.0+-green.svg)
![DRF Version](https://img.shields.io/badge/drf-3.16.1+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Links

- **PyPI**: https://pypi.org/project/drf-discord-handler/
- **GitHub**: https://github.com/shinkeonkim/drf_discord_handler


## Features

- 🚨 **Automatic Exception Notifications**: Automatically sends detailed exception information to Discord when errors occur in your DRF API
- 📊 **Rich Error Details**: Includes request method, path, full URL, user information, device info, stack traces, and more
- 🔒 **Sensitive Data Filtering**: Automatically filters sensitive information (passwords, tokens, etc.) before sending to Discord
- 🧵 **Discord Thread Support**: Creates threads in Discord forum channels for better organization of error messages
- ⚙️ **Configurable**: Easy configuration through Django settings
- 🎯 **Multiple Channels**: Support for different Discord channels for different types of notifications

## Screenshots

<img height="800" alt="Image" src="https://github.com/user-attachments/assets/2ea93180-96ee-42fe-9619-a7b983d1ef76" />

## Installation

Install the package using pip:

```bash
pip install drf-discord-handler
```

Or using uv:

```bash
uv add drf-discord-handler
```

## Requirements

- Python 3.14+
- Django 6.0+
- Django REST Framework 3.16.1+

## Quick Start

### 1. Configure Discord Webhook

Add the following configuration to your Django `settings.py`:

```python
DRF_DISCORD_HANDLER = {
    'ENABLED': True,
    'EXCEPTION_WEBHOOK_URL': 'https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN',
    'FILTER_SENSITIVE_DATA': True,
    'EXCLUDE_EXCEPTIONS': [
        # django.http.Http404,  # Example: exclude 404 errors
    ],
}
```

### 2. Configure DRF Exception Handler

Add the exception handler to your DRF settings:

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'drf_discord_handler.discord_exception_handler',
}
```

### 3. That's it!

Now whenever an exception occurs in your DRF API, you'll receive detailed notifications in your Discord channel.

## Configuration Options

### `ENABLED` (bool, default: `True`)
Enable or disable Discord notifications. Set to `False` to disable notifications (useful for development).

### `EXCEPTION_WEBHOOK_URL` (str, required)
Discord webhook URL for exception notifications. You can create a webhook in your Discord server settings.

### `FILTER_SENSITIVE_DATA` (bool, default: `True`)
Automatically filter sensitive information (passwords, tokens, etc.) from request data before sending to Discord.

### `SENSITIVE_KEYS` (list, optional)
Custom list of keys to filter. Default includes common sensitive keys like `password`, `token`, `secret`, etc.

### `EXCLUDE_EXCEPTIONS` (list, optional)
List of exception classes to exclude from Discord notifications. For example, to exclude 404 errors:

```python
'EXCLUDE_EXCEPTIONS': [
    django.http.Http404,
]
```

## What Information is Sent?

When an exception occurs, the following information is automatically sent to Discord:

- **Exception Details**: Exception type and message
- **Request Information**: HTTP method, path, full URL, URL pattern
- **User Information**: User ID, username, email (if authenticated), or "Anonymous" if not
- **Device Information**: User-Agent, IP address, browser, OS
- **View Information**: View class and view name
- **Request Details**: Query parameters, request body, headers
- **Response Details**: Status code and response data
- **Stack Trace**: Full stack trace with local variables (sent in separate messages/threads)

## Discord Thread Support

If your Discord webhook is configured for a forum channel, the package automatically creates threads for each exception. The full stack trace is sent in the thread, keeping the main channel clean.

## Using DiscordClient Directly

You can also use the `DiscordClient` class directly to send custom messages:

```python
from drf_discord_handler import DiscordClient

client = DiscordClient(webhook_url='https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN')

# Send a simple message
client.send_message(content="Hello from Django!")

# Send an embed
client.send_embed(
    title="Custom Notification",
    description="This is a custom notification",
    color=0x00FF00,  # Green color
)
```

## Security Considerations

- **Sensitive Data Filtering**: By default, the package filters sensitive information from request data. Make sure `FILTER_SENSITIVE_DATA` is set to `True` in production.
- **Webhook URLs**: Keep your Discord webhook URLs secure. Never commit them to version control. Use environment variables instead:

```python
import os

DRF_DISCORD_HANDLER = {
    'EXCEPTION_WEBHOOK_URL': os.environ.get('DISCORD_EXCEPTION_WEBHOOK_URL'),
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
