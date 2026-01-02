import os
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from dhisana.utils.assistant_tool_tag import assistant_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_url = 'https://api.mailreach.co/api/v1'


def get_mailreach_api_key(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieves the MailReach API key from the provided tool configuration or environment variables.

    Args:
        tool_config (list): A list of dictionaries containing the tool configuration. 
                            Each dictionary should have a "name" key and a "configuration" key,
                            where "configuration" is a list of dictionaries containing "name" and "value" keys.

    Returns:
        str: The MailReach API key.

    Raises:
        ValueError: If the MailReach integration has not been configured.
    """
    api_key = None
    
    if tool_config:
        mailreach_config = next(
            (item for item in tool_config if item.get("name") == "mailreach"), None
        )
        if mailreach_config:
            config_map = {
                item["name"]: item["value"]
                for item in mailreach_config.get("configuration", [])
                if item
            }
            api_key = config_map.get("apiKey")
    
    api_key = api_key or os.getenv("MAILREACH_API_KEY")
    
    if not api_key:
        raise ValueError(
            "MailReach integration is not configured. Please configure the connection to MailReach in Integrations."
        )
    
    return api_key


def get_mailreach_headers(tool_config: Optional[List[Dict]] = None) -> Dict[str, str]:
    """
    Get the headers required for MailReach API requests.

    Args:
        tool_config (list): Optional tool configuration containing API credentials.

    Returns:
        Dict[str, str]: Headers dictionary with x-api-key and Content-Type.
    """
    api_key = get_mailreach_api_key(tool_config)
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    return headers


async def _handle_mailreach_response(response: aiohttp.ClientResponse) -> Any:
    """
    Handle MailReach API responses consistently.

    Args:
        response: The aiohttp ClientResponse object.

    Returns:
        The JSON response data.

    Raises:
        aiohttp.ClientResponseError: For rate limits or other errors.
    """
    if response.status == 200:
        return await response.json()
    elif response.status == 429:
        raise aiohttp.ClientResponseError(
            request_info=response.request_info,
            history=response.history,
            status=response.status,
            message="Rate limit exceeded",
            headers=response.headers
        )
    else:
        error_message = await response.text()
        logger.error(f"MailReach API Error {response.status}: {error_message}")
        response.raise_for_status()


@assistant_tool
async def ping_mailreach(
    tool_config: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Ping the MailReach API to verify connectivity and authentication.
    
    This is a simple endpoint to test if your API key is valid and the service is accessible.

    Args:
        tool_config (list): Optional tool configuration containing API credentials.

    Returns:
        Dict[str, Any]: Response from the ping endpoint, typically containing a success message.
    """
    url = f"{base_url}/ping"
    headers = get_mailreach_headers(tool_config)
    
    logger.info("Pinging MailReach API...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            result = await _handle_mailreach_response(response)
            logger.info("MailReach ping successful")
            return result
