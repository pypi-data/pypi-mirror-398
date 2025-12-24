"""Discord Webhook 클라이언트 구현.

Python 표준 라이브러리만 사용하여 Discord Webhook API를 직접 구현합니다.
Python 3.14 호환성을 보장합니다.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


class DiscordClient:
    """Class to send messages to Discord via Webhook."""

    def __init__(self, webhook_url: str, timeout: int = 10):
        """
        Args:
            webhook_url: Discord Webhook URL
            timeout: Request timeout (seconds)
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send_message(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        thread_id: Optional[str] = None,
        thread_name: Optional[str] = None,
    ) -> (bool, str):
        """
        Send message to Discord via Webhook.

        Args:
            content: Message text content
            embeds: Discord Embed objects list
            username: Webhook username (optional)
            avatar_url: Webhook avatar URL (optional)
            thread_id: Existing thread ID (optional, send message to the thread)
            thread_name: Thread name for new thread in Forum channel (optional)

        Returns:
            (success, thread ID)
        """
        if not content and not embeds:
            logger.warning("[DRF Discord Handler] Failed to send message: content and embeds are empty")
            return (False, None)
        
        payload = {
            "content": content if content else None,
            "username": username if username else None,
            "avatar_url": avatar_url if avatar_url else None,
            "thread_id": thread_id if thread_id else None,
            "thread_name": thread_name if thread_name else None,
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        if embeds:
            normalized_embeds = []
            for embed_dict in embeds:
                normalized_embed = {}
                
                for key in ["title", "description", "color", "timestamp", "fields", "footer"]:
                    if key in embed_dict:
                        normalized_embed[key] = embed_dict[key]
                
                if "timestamp" in normalized_embed and not isinstance(normalized_embed["timestamp"], str):
                    if isinstance(normalized_embed["timestamp"], datetime):
                        normalized_embed["timestamp"] = normalized_embed["timestamp"].isoformat()
                
                normalized_embeds.append(normalized_embed)
            
            payload["embeds"] = normalized_embeds
        
        try:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            request_url = self.webhook_url
            
            if thread_name:
                encoded_thread_name = quote(thread_name, safe=':')
                separator = '&' if '?' in self.webhook_url else '?'
                request_url = f"{self.webhook_url}{separator}thread_name={encoded_thread_name}&wait=true"                
            elif thread_id:
                separator = '&' if '?' in self.webhook_url else '?'
                request_url = f"{self.webhook_url}{separator}thread_id={thread_id}&wait=true"            
            
            req = urllib_request.Request(
                request_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': f'drf-discord-handler',
                },
                method='POST'
            )
            
            with urllib_request.urlopen(req, timeout=self.timeout) as response:
                status_code = response.getcode()
                response_data = response.read()
                
                if 200 <= status_code < 300:
                    if thread_name or thread_id:
                        try:
                            response_json = json.loads(response_data.decode('utf-8'))

                            if 'thread' in response_json and isinstance(response_json['thread'], dict):
                                thread_id_from_response = response_json['thread'].get('id')
                                if thread_id_from_response:
                                    return (True, thread_id_from_response)
                            elif 'id' in response_json and thread_name:
                                return (True, response_json['id'])
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            logger.error(f"[DRF Discord Handler] Failed to get thread ID: {e}")
                    return (True, None)
                else:
                    logger.error(
                        f"[DRF Discord Handler] Failed to send message: HTTP {status_code}. "
                        f"Response: {response_data.decode('utf-8', errors='ignore')[:200]}"
                    )
                    return (False, None)
                    
        except HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode('utf-8', errors='ignore')[:500]
            except:
                pass
            logger.error(
                f"[DRF Discord Handler] Failed to send message: HTTP {e.code} - {e.reason}. "
                f"Error: {error_body}. "
                f"thread_name={thread_name}, thread_id={thread_id}, "
                f"URL: {request_url[:150]}..."
            )
            return (False, None)
        except URLError as e:
            logger.error(f"[DRF Discord Handler] Failed to send message: URL error - {e.reason}")
            return (False, None)
        except Exception as e:
            logger.error(f"[DRF Discord Handler] Failed to send message: {e}", exc_info=True)
            return (False, None)

    def send_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[Dict[str, str]] = None,
        timestamp: Optional[str] = None,
    ) -> (bool, str):
        """
        Send message to Discord in Embed format.

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (decimal integer, e.g. 0xFF0000 = red)
            fields: Embed fields list (each field has name, value, inline keys)
            footer: Embed footer (text key)
            timestamp: ISO 8601 format timestamp

        Returns:
            (success, thread ID)
        """
        embed: Dict[str, Any] = {"title": title}

        if description:
            embed["description"] = description
        if color is not None:
            embed["color"] = color
        if fields:
            embed["fields"] = fields
        if footer:
            embed["footer"] = footer
        if timestamp:
            embed["timestamp"] = timestamp

        return self.send_message(embeds=[embed])
