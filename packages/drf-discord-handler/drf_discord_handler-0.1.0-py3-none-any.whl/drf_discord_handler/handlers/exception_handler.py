"""DRF Exception Handler"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from rest_framework.views import exception_handler as drf_exception_handler

from drf_discord_handler.clients import DiscordClient
from drf_discord_handler.settings.config import DiscordHandlerConfig
from drf_discord_handler.utils.formatters import format_exception_message, format_stack_trace_messages
from drf_discord_handler.utils.filters import (
    filter_sensitive_data,
    should_exclude_exception,
)
from functools import wraps

logger = logging.getLogger(__name__)

class PackageExeptionHandler:
    """
    Exception handler for the package.

    Args:
        f: Function to handle the exception

    Returns:
        Function result
    """
    def __init__(self, f):
        self.func = f

    def __call__(self, exc: Exception, context: Dict[str, Any]) -> Optional[Any]:
        try:
            return self.func(exc, context)
        except Exception as e:
            logger.error(f"[DRF Discord Handler] Error handling exception: {e}", exc_info=True)
            return drf_exception_handler(exc, context)


@PackageExeptionHandler
def discord_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Any]:
    """
    DRF Exception Handler with Discord notification.

    Args:
        exc: Exception object
        context: DRF context dictionary (request, view, etc.)

    Returns:
        DRF Response object or None
    """
    response = drf_exception_handler(exc, context)

    if not DiscordHandlerConfig.is_enabled():
        return response

    exclude_exceptions = DiscordHandlerConfig.get_exclude_exceptions()
    if exclude_exceptions and should_exclude_exception(exc, exclude_exceptions):
        return response

    webhook_url = DiscordHandlerConfig.get_exception_webhook_url()
    if not webhook_url:
        logger.error("[DRF Discord Handler] Webhook URL is not set")
        return response
    
    context_data = context.copy()

    if response:
        context_data["response"] = response

    context_data = filter_context_data(context_data)

    embeds = format_exception_message(exc, context_data)

    client = DiscordClient(webhook_url)
    
    thread_name = f"Exception: {type(exc).__name__} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    is_success, thread_id = client.send_message(
        embeds=embeds,
        thread_name=thread_name,
    )

    if not is_success:
        logger.warning(f"[DRF Discord Handler] Failed to send exception notification to Discord")
        return response

    stack_trace_messages = format_stack_trace_messages(exc)
    
    for trace_message in stack_trace_messages:
        client.send_message(
            content=trace_message,
            thread_id=thread_id,
        )
    return response


def filter_context_data(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter the context data to remove sensitive information.

    Args:
        context: DRF context dictionary (request, view, etc.)

    Returns:
        Filtered context dictionary
    """

    shoud_filter_sensitive_data = DiscordHandlerConfig.should_filter_sensitive_data()
    sensitive_keys = DiscordHandlerConfig.get_sensitive_keys()

    try:
        if shoud_filter_sensitive_data and "request" in context_data:        
            request = context_data["request"]

            filtered_data = None
            filtered_query_params = None

            if hasattr(request, "data") and request.data:
                filtered_data = filter_sensitive_data(dict(request.data), sensitive_keys)
                
            if hasattr(request, "query_params") and request.query_params:
                filtered_query_params = filter_sensitive_data(dict(request.query_params), sensitive_keys)
            
            context_data["filtered_request_data"] = filtered_data
            context_data["filtered_query_params"] = filtered_query_params
    except Exception as e:
        logger.error(f"[DRF Discord Handler] Error formatting exception information: {e}", exc_info=True)

    return context_data
