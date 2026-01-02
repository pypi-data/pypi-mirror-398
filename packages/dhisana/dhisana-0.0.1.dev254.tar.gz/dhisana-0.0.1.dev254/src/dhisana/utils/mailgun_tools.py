import asyncio
import logging
import os
from typing import Optional, List, Dict

import aiohttp

from dhisana.utils.assistant_tool_tag import assistant_tool
from dhisana.schemas.common import SendEmailContext
from dhisana.utils.email_body_utils import body_variants


def get_mailgun_notify_key(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieve the Mailgun API key from tool_config or environment.

    Looks for an integration named "mailgun" and reads configuration item
    with name "apiKey". Falls back to env var MAILGUN_NOTIFY_KEY.
    """
    key = None
    if tool_config:
        cfg = next((item for item in tool_config if item.get("name") == "mailgun"), None)
        if cfg:
            cfg_map = {i["name"]: i["value"] for i in cfg.get("configuration", []) if i}
            key = cfg_map.get("apiKey")
    key = key or os.getenv("MAILGUN_NOTIFY_KEY")
    if not key:
        raise ValueError(
            "Mailgun integration is not configured. Please configure the connection to Mailgun in Integrations."
        )
    return key


def get_mailgun_notify_domain(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieve the Mailgun domain from tool_config or environment.

    Looks for an integration named "mailgun" and reads configuration item
    with name "domain" (preferred) or legacy "notifyDomain".
    Falls back to env var MAILGUN_DOMAIN, then MAILGUN_NOTIFY_DOMAIN.
    """
    domain = None
    if tool_config:
        cfg = next((item for item in tool_config if item.get("name") == "mailgun"), None)
        if cfg:
            cfg_map = {i["name"]: i["value"] for i in cfg.get("configuration", []) if i}
            domain = cfg_map.get("domain") or cfg_map.get("notifyDomain")
    domain = domain or os.getenv("MAILGUN_DOMAIN") or os.getenv("MAILGUN_NOTIFY_DOMAIN")
    if not domain:
        raise ValueError(
            "Mailgun integration is not configured. Please configure the connection to Mailgun in Integrations."
        )
    return domain


@assistant_tool
async def send_email_with_mailgun(
    sender: str,
    recipients: List[str],
    subject: str,
    message: str,
    tool_config: Optional[List[Dict]] = None,
    body_format: Optional[str] = None,
):
    """
    Send an email using the Mailgun API.

    Parameters:
    - sender: Email address string, e.g. "Alice <alice@example.com>" or just address.
    - recipients: List of recipient email addresses.
    - subject: Subject string.
    - message: HTML content body.
    - tool_config: Optional integrations config list.
    """
    try:
        api_key = get_mailgun_notify_key(tool_config)
        domain = get_mailgun_notify_domain(tool_config)

        body = message or ""
        data = {
            "from": sender,
            "to": recipients,
            "subject": subject,
        }

        plain_body, html_body, _ = body_variants(body, body_format)
        data["text"] = plain_body
        data["html"] = html_body

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                auth=aiohttp.BasicAuth("api", api_key),
                data=data,
            ) as response:
                # Try to return JSON payload if available
                try:
                    return await response.json()
                except Exception:
                    return await response.text()
    except Exception as ex:
        logging.warning(f"Error sending email via Mailgun: {ex}")
        return {"error": str(ex)}


async def send_email_using_mailgun_async(
    send_email_context: SendEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> str:
    """
    Provider-style wrapper for Mailgun that accepts SendEmailContext and returns an id string.
    """
    api_key = get_mailgun_notify_key(tool_config)
    domain = get_mailgun_notify_domain(tool_config)

    plain_body, html_body, _ = body_variants(
        send_email_context.body,
        getattr(send_email_context, "body_format", None),
    )

    data = {
        "from": f"{send_email_context.sender_name} <{send_email_context.sender_email}>",
        "to": [send_email_context.recipient],
        "subject": send_email_context.subject,
        "text": plain_body,
        "html": html_body,
    }

    extra_headers = getattr(send_email_context, "headers", None) or {}
    for header, value in extra_headers.items():
        if not header or value is None:
            continue
        data[f"h:{header}"] = str(value)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=aiohttp.BasicAuth("api", api_key),
            data=data,
        ) as response:
            # Raise if not 2xx to match other providers' behavior
            if response.status < 200 or response.status >= 300:
                try:
                    detail = await response.text()
                except Exception:
                    detail = f"status={response.status}"
                raise RuntimeError(f"Mailgun send failed: {detail}")
            try:
                payload = await response.json()
            except Exception:
                payload = {"message": await response.text()}

    # Normalise return value akin to other providers
    msg_id = payload.get("id") if isinstance(payload, dict) else None
    await asyncio.sleep(20)
    return msg_id or str(payload)
