"""Utility functions for formatting messages."""

import traceback
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
import re

from django.http import HttpRequest


def is_request_object(obj: Any) -> bool:
    """
    Check if object is a request object (Django HttpRequest or DRF Request).
    
    Args:
        obj: Object to check
        
    Returns:
        True if object is a request object
    """
    if obj is None:
        return False
    
    if isinstance(obj, HttpRequest):
        return True
    
    if hasattr(obj, 'method') and hasattr(obj, 'path'):
        return True
    
    return False

MAX_STACK_TRACE_DEPTH = 10

BLUE_COLOR = 0x3498DB
GREEN_COLOR = 0x2ECC71
RED_COLOR = 0xFF0000


def format_exception_message(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Format exception information into Discord Embed format (multiple embeds).

    Args:
        exception: Exception object
        context: DRF exception handler context (request, view, etc.)

    Returns:
        List of dictionaries in Discord Embed format
    """
    embeds: List[Dict[str, Any]] = []
    
    # First Embed: Basic information
    main_embed: Dict[str, Any] = {
        "title": f"🚨 Exception: {type(exception).__name__}",
        "description": str(exception),
        "color": RED_COLOR,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [],
    }

    # Add request information
    if context:
        request = context.get("request")

        if is_request_object(request):
            # Extract detailed user information
            user_info = get_user_info(request)
            device_info = get_device_info(request)
            
            if hasattr(request, 'build_absolute_uri'):
                try:
                    full_url = request.build_absolute_uri()
                except Exception:
                    full_url = getattr(request, 'path', 'N/A')
            else:
                full_url = getattr(request, 'path', 'N/A')
            
            url_info = get_url_info(request)
            
            method_field = {
                "name": "Method",
                "value": request.method,
                "inline": True,
            }
            path_field = {
                "name": "Path",
                "value": request.path,
                "inline": True,
            }
            url_field = {
                "name": "🌐 Full URL",
                "value": full_url[:1024] if len(full_url) > 1024 else full_url,
                "inline": False,
            }
            
            main_embed["fields"].extend([method_field, path_field, url_field])
            
            url_value = ""
            if url_info:
                if url_info.get('url_name'):
                    url_value += f"URL Name: `{url_info['url_name']}`\n"
                if url_info.get('route'):
                    url_value += f"Route Pattern: `{url_info['route']}`\n"
                if url_info.get('view_name'):
                    url_value += f"View Name: `{url_info['view_name']}`\n"
                if url_info.get('app_name'):
                    url_value += f"App Name: `{url_info['app_name']}`\n"
                if url_info.get('namespace'):
                    url_value += f"Namespace: `{url_info['namespace']}`\n"
                if url_info.get('kwargs'):
                    url_value += f"URL Kwargs: `{url_info['kwargs']}`\n"
                if url_info.get('args'):
                    url_value += f"URL Args: `{url_info['args']}`"
            
            if not url_value:
                url_value = "Unable to get URL pattern information"
            
            main_embed["fields"].append({
                "name": "📍 URL Pattern",
                "value": url_value.strip(),
                "inline": False,
            })
            
            user_value = ""
            if user_info:
                if user_info.get("authenticated") is not False and "authenticated" not in user_info:
                    if user_info.get('id'):
                        user_value += f"ID: {user_info['id']}\n"
                    if user_info.get('username'):
                        user_value += f"Username: {user_info['username']}\n"
                    if user_info.get('email'):
                        user_value += f"Email: {user_info['email']}\n"
                    if user_info.get('is_staff'):
                        user_value += f"Staff: {user_info['is_staff']}\n"
                    if user_info.get('is_superuser'):
                        user_value += f"Superuser: {user_info['is_superuser']}"
                elif user_info.get("authenticated") is False:
                    suser_value = "Anonymous (Not authenticated)"
            else:
                if hasattr(request, "user"):
                    if hasattr(request.user, "is_authenticated") and request.user.is_authenticated:
                        user_value = f"User: {request.user}"
                    else:
                        user_value = "Anonymous (Not authenticated)"
                else:
                    user_value = "No user information available"
            
            main_embed["fields"].append({
                "name": "👤 User Info",
                "value": user_value.strip() if user_value else "Unknown",
                "inline": False,
            })
            
            if device_info:
                device_value = f"User-Agent: {device_info.get('user_agent', 'N/A')}\n"
                device_value += f"IP: {device_info.get('ip', 'N/A')}\n"
                if device_info.get('browser'):
                    device_value += f"Browser: {device_info['browser']}\n"
                if device_info.get('os'):
                    device_value += f"OS: {device_info['os']}"
                main_embed["fields"].append({
                    "name": "💻 Device Info",
                    "value": device_value[:1024],
                    "inline": False,
                })

        view = context.get("view")
        if view:
            view_value = f"`{view.__class__.__module__}.{view.__class__.__name__}`"
            if hasattr(view, 'get_view_name'):
                try:
                    view_name = view.get_view_name()
                    if view_name:
                        view_value += f"\nView Name: `{view_name}`"
                except:
                    pass
            
            insert_index = len(main_embed["fields"])
            for i, field in enumerate(main_embed["fields"]):
                if field.get("name") == "📍 URL Pattern":
                    insert_index = i + 1
                    break
            
            main_embed["fields"].insert(insert_index, {
                "name": "🔍 View",
                "value": view_value,
                "inline": False,
            })
        
        if not view and context and context.get("request"):
            request = context["request"]
            exception_location = get_exception_location(exception)
            if exception_location:
                main_embed["fields"].append({
                    "name": "📍 Exception Location",
                    "value": exception_location,
                    "inline": False,
                })
    
    
    embeds.append(main_embed)

    if context and context.get("request"):
        request = context["request"]
        request_embed: Dict[str, Any] = {
            "title": "📥 Request Details",
            "color": BLUE_COLOR,
            "fields": [],
        }
        
        query_params = None
        if "filtered_query_params" in context and context["filtered_query_params"] is not None:
            query_params = context["filtered_query_params"]
        elif hasattr(request, "query_params") and request.query_params:
            query_params = dict(request.query_params)
        elif request.GET:
            query_params = dict(request.GET)
        
        if query_params:
            request_embed["fields"].append({
                "name": "Query Parameters",
                "value": format_dict(query_params, max_length=1000),
                "inline": False,
            })
        
        request_data = None
        if "filtered_request_data" in context and context["filtered_request_data"] is not None:
            request_data = context["filtered_request_data"]
        elif hasattr(request, "data") and request.data:
            try:
                request_data = dict(request.data) if hasattr(request.data, "__iter__") else request.data
            except (TypeError, ValueError):
                request_data = str(request.data)[:200]
        
        if request_data:
            request_embed["fields"].append({
                "name": "Request Body",
                "value": format_dict(request_data if isinstance(request_data, dict) else {"data": request_data}, max_length=1000),
                "inline": False,
            })
        
        if hasattr(request, "headers"):
            headers_info = {}
            for key in ["User-Agent", "Content-Type", "Accept", "Referer", "Origin"]:
                value = request.headers.get(key)
                if value:
                    headers_info[key] = value[:100]
            
            auth_header = request.headers.get("Authorization")
            if auth_header:
                if auth_header.startswith("Bearer "):
                    headers_info["Authorization"] = "Bearer ***FILTERED***"
                elif auth_header.startswith("Basic "):
                    headers_info["Authorization"] = "Basic ***FILTERED***"
                else:
                    headers_info["Authorization"] = "***FILTERED***"
            
            if headers_info:
                request_embed["fields"].append({
                    "name": "Headers",
                    "value": format_dict(headers_info, max_length=1000),
                    "inline": False,
                })
        
        if request_embed["fields"]:
            embeds.append(request_embed)
        
        response = context.get("response")
        if response:
            response_embed: Dict[str, Any] = {
                "title": "📤 Response Details",
                "color": GREEN_COLOR,
                "fields": [
                    {
                        "name": "Status Code",
                        "value": str(getattr(response, 'status_code', 'N/A')),
                        "inline": True,
                    },
                ],
            }
            
            if hasattr(response, 'data'):
                try:
                    response_data = response.data
                    if isinstance(response_data, dict):
                        response_embed["fields"].append({
                            "name": "Response Data",
                            "value": format_dict(response_data, max_length=1000),
                            "inline": False,
                        })
                    else:
                        response_embed["fields"].append({
                            "name": "Response Data",
                            "value": str(response_data)[:1000],
                            "inline": False,
                        })
                except (AttributeError, TypeError):
                    pass
            
            embeds.append(response_embed)
    
    tb_lines = traceback.format_exception(
        type(exception),
        exception,
        exception.__traceback__,
    )
    stack_trace = "".join(tb_lines)
    
    if len(stack_trace) > 800:
        stack_trace_summary = stack_trace[:800] + "\n... (The full stack trace is available in the separate message/thread below)"
    else:
        stack_trace_summary = stack_trace
    
    trace_embed: Dict[str, Any] = {
        "title": "🔍 Stack Trace (Summary)",
        "description": "The full stack trace is sent in a separate message.",
        "color": 0xE74C3C,  # Red color
        "fields": [
            {
                "name": "Stack Trace Preview",
                "value": f"```\n{stack_trace_summary}\n```",
                "inline": False,
            },
        ],
    }
    
    embeds.append(trace_embed)
    
    return embeds


def format_stack_trace_messages(
    exception: Exception,
    max_length: int = 1900,
) -> List[str]:
    """
    Split stack trace into multiple messages (Discord message limit: 2000 characters).

    Args:
        exception: Exception object
        max_length: Maximum length of each message (consider code block markers)

    Returns:
        List of message strings
    """
    try:
        tb_lines = traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__,
            capture_locals=True,
        )
    except TypeError:
        tb_lines = traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__,
        )
    
    stack_trace = "".join(tb_lines)
    
    messages = []
    chunk_size = max_length
    
    total_chunks = (len(stack_trace) + chunk_size - 1) // chunk_size
    
    for i in range(0, len(stack_trace), chunk_size):
        chunk = stack_trace[i:i+chunk_size]
        part_num = i // chunk_size + 1
        
        if total_chunks > 1:
            message = f"**🔍 Full Stack Trace - Part {part_num}/{total_chunks}**\n```\n{chunk}\n```"
        else:
            message = f"**🔍 Full Stack Trace**\n```\n{chunk}\n```"
        
        messages.append(message)
    
    return messages


def format_dict(data: Dict[str, Any], max_length: int = 1000) -> str:
    """
    Format dictionary into string (include length limit).

    Args:
        data: Dictionary to format
        max_length: Maximum length

    Returns:
        Formatted string
    """
    formatted = str(data)
    if len(formatted) > max_length:
        formatted = formatted[:max_length] + "... (truncated)"
    return formatted


def get_user_info(request: Any) -> Dict[str, Any]:
    """
    Extract user information from request.

    Args:
        request: Django HttpRequest object

    Returns:
        User information dictionary
    """
    user_info = {}
    
    if hasattr(request, "user") and request.user and hasattr(request.user, "is_authenticated"):
        if request.user.is_authenticated:
            user_info["id"] = getattr(request.user, "id", None) or getattr(request.user, "pk", None)
            user_info["username"] = getattr(request.user, "username", None) or str(request.user)
            user_info["email"] = getattr(request.user, "email", None)
            user_info["is_staff"] = getattr(request.user, "is_staff", False)
            user_info["is_superuser"] = getattr(request.user, "is_superuser", False)
        else:
            user_info["authenticated"] = False
    
    return user_info


def get_url_info(request: Any) -> Dict[str, Any]:
    """
    Extract URL pattern information from request.

    Args:
        request: Django HttpRequest object

    Returns:
        URL information dictionary
    """
    url_info = {}
    
    # Extract URL pattern information via resolver_match
    if hasattr(request, 'resolver_match') and request.resolver_match:
        resolver_match = request.resolver_match
        
        if hasattr(resolver_match, 'url_name') and resolver_match.url_name:
            url_info['url_name'] = resolver_match.url_name
        
        if hasattr(resolver_match, 'route') and resolver_match.route:
            url_info['route'] = resolver_match.route
        elif hasattr(resolver_match, 'pattern') and resolver_match.pattern:
            try:
                if hasattr(resolver_match.pattern, 'route'):
                    url_info['route'] = resolver_match.pattern.route
            except:
                pass
        
        if hasattr(resolver_match, 'view_name') and resolver_match.view_name:
            url_info['view_name'] = resolver_match.view_name
        
        if hasattr(resolver_match, 'app_name') and resolver_match.app_name:
            url_info['app_name'] = resolver_match.app_name
        
        if hasattr(resolver_match, 'namespace') and resolver_match.namespace:
            url_info['namespace'] = resolver_match.namespace
        
        if hasattr(resolver_match, 'kwargs') and resolver_match.kwargs:
            url_info['kwargs'] = resolver_match.kwargs
        
        if hasattr(resolver_match, 'args') and resolver_match.args:
            url_info['args'] = resolver_match.args
    
    return url_info


def get_exception_location(exception: Exception) -> Optional[str]:
    """
    Extract exception location information.

    Args:
        exception: Exception object

    Returns:
        Exception location string (None if not available)
    """
    if not hasattr(exception, '__traceback__') or not exception.__traceback__:
        return None
    
    try:
        tb = exception.__traceback__
        frame = tb
        
        location_parts = []
        
        depth = 0
        while frame and depth < MAX_STACK_TRACE_DEPTH:
            filename = frame.tb_frame.f_code.co_filename
            lineno = frame.tb_lineno
            func_name = frame.tb_frame.f_code.co_name
            
            if 'site-packages' not in filename and '__pycache__' not in filename:
                # Show file path simply
                if '/' in filename:
                    file_path = filename.split('/')[-1]
                else:
                    file_path = filename
                
                location_parts.append(f"`{file_path}:{lineno}` in `{func_name}()`")
                break  # Show only first project file
            
            frame = frame.tb_next
            depth += 1
        
        if location_parts:
            return "\n".join(location_parts)
    except Exception:
        pass
    
    return None


def get_device_info(request: Any) -> Dict[str, Any]:
    """
    Extract Device information from request.

    Args:
        request: Django HttpRequest object

    Returns:
        Device information dictionary
    """
    device_info = {}
    
    user_agent = None
    if hasattr(request, "headers"):
        user_agent = request.headers.get("User-Agent", "")
    elif hasattr(request, "META"):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
    
    if user_agent:
        device_info["user_agent"] = user_agent
        
        browser_match = re.search(r'(Chrome|Firefox|Safari|Edge|Opera|MSIE|Trident)[/\s]?(\d+\.\d+)?', user_agent, re.IGNORECASE)
        if browser_match:
            device_info["browser"] = browser_match.group(0)
        
        os_match = re.search(r'(Windows|Mac|Linux|Android|iOS|iPhone|iPad)[/\s]?([\d.]+)?', user_agent, re.IGNORECASE)
        if os_match:
            device_info["os"] = os_match.group(0)
    
    ip = None
    if hasattr(request, "META"):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
    
    if ip:
        device_info["ip"] = ip
    
    return device_info
