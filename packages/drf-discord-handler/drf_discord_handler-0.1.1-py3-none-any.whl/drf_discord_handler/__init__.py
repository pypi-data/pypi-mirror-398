"""DRF Discord Handler 패키지."""

__version__ = "0.1.1"

def _lazy_import_client():
    from drf_discord_handler.clients import DiscordClient
    return DiscordClient

def _lazy_import_handler():
    from drf_discord_handler.handlers.exception_handler import discord_exception_handler
    return discord_exception_handler

def _lazy_import_config():
    from drf_discord_handler.settings import DiscordHandlerConfig
    return DiscordHandlerConfig

def __getattr__(name: str):
    if name == "DiscordClient":
        return _lazy_import_client()
    elif name == "discord_exception_handler":
        return _lazy_import_handler()
    elif name == "DiscordHandlerConfig":
        return _lazy_import_config()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "__version__",
    "DiscordClient",
    "discord_exception_handler",
    "DiscordHandlerConfig",
]
