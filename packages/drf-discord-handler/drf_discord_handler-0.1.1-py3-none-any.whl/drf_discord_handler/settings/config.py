"""Class to manage package settings."""

from typing import Dict, Any, Optional
from django.conf import settings as django_settings

DEFAULT_FILTERING_SENSITIVE_KEYS = [
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "credential",
    "private_key",
    "privatekey",
    "session",
    "cookie",
    "csrf",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "cvv",
    "pin",
]

DEFAULT_FILTERED_VALUE = "***FILTERED***"


class DiscordHandlerConfig:
    """Class to manage DRF Discord Handler settings."""

    _config: Dict[str, Any] = {}

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        Load DRF_DISCORD_HANDLER settings from Django settings.

        Returns:
            Configuration dictionary
        """
        if cls._config:
            return cls._config

        config = getattr(django_settings, "DRF_DISCORD_HANDLER", {})
        cls._config = {
            "enabled": config.get("ENABLED", not django_settings.DEBUG),
            "exception_webhook_url": config.get("EXCEPTION_WEBHOOK_URL"),
            "should_filter_sensitive_data": config.get("SHOULD_FILTER_SENSITIVE_DATA", True),
            "filtering_sensitive_keys": config.get("FILTERING_SENSITIVE_KEYS", DEFAULT_FILTERING_SENSITIVE_KEYS),
            "filtered_value": config.get("FILTERED_VALUE", DEFAULT_FILTERED_VALUE),
            "exclude_exceptions": config.get("EXCLUDE_EXCEPTIONS", []),
        }
        return cls._config

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if the package is enabled."""
        config = cls.load_config()
        return config.get("enabled", False)

    @classmethod
    def get_exception_webhook_url(cls) -> Optional[str]:
        """Return Discord Webhook URL for exception handler."""
        config = cls.load_config()
        return config.get("exception_webhook_url")

    @classmethod
    def should_filter_sensitive_data(cls) -> bool:
        """Return whether sensitive data should be filtered."""
        config = cls.load_config()
        return config.get("should_filter_sensitive_data", True)

    @classmethod
    def get_sensitive_keys(cls) -> list:
        config = cls.load_config()
        return config.get("filtering_sensitive_keys", DEFAULT_FILTERING_SENSITIVE_KEYS)
    
    @classmethod
    def get_filtered_value(cls) -> str:
        """Return filtered value."""
        config = cls.load_config()
        return config.get("filtered_value", DEFAULT_FILTERED_VALUE)

    @classmethod
    def get_exclude_exceptions(cls) -> list:
        """Return list of exceptions to exclude."""
        config = cls.load_config()
        return config.get("exclude_exceptions", [])
