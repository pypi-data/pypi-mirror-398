"""Mail delivery helpers for SendGrid and compatibility exports for Mailgun.

This module now contains:
- SendGrid: helpers to send e-mail via SendGrid's REST API.
- Mailgun: re-exports for helpers that were moved to `mailgun_tools.py`.
"""

import logging
import os
from typing import Optional, List, Dict
from email.utils import parseaddr

import aiohttp

from dhisana.utils.assistant_tool_tag import assistant_tool
from dhisana.schemas.common import SendEmailContext
from dhisana.utils.email_body_utils import body_variants

# --------------------------------------------------------------------------- #
# Mailgun (re-exported from dedicated module for backward compatibility)
# --------------------------------------------------------------------------- #
from .mailgun_tools import (
    get_mailgun_notify_key,
    get_mailgun_notify_domain,
    send_email_with_mailgun,
)


# --------------------------------------------------------------------------- #
# SendGrid helpers
# --------------------------------------------------------------------------- #

def get_sendgrid_api_key(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieve the SendGrid API key from tool_config or environment.

    Looks for an integration named "sendgrid" and reads configuration item
    with name "apiKey". Falls back to env var SENDGRID_API_KEY.
    """
    key: Optional[str] = None
    if tool_config:
        cfg = next((c for c in tool_config if c.get("name") == "sendgrid"), None)
        if cfg:
            cfg_map = {i.get("name"): i.get("value") for i in cfg.get("configuration", []) if i}
            key = cfg_map.get("apiKey")
    key = key or os.getenv("SENDGRID_API_KEY")
    if not key:
        raise ValueError(
            "SendGrid integration is not configured. Please configure the connection to SendGrid in Integrations."
        )
    return key


@assistant_tool
async def send_email_with_sendgrid(
    sender: str,
    recipients: List[str],
    subject: str,
    message: str,
    tool_config: Optional[List[Dict]] = None,
    body_format: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
):
    """
    Send an email using SendGrid's v3 Mail Send API.

    Parameters:
    - sender: Either "Name <email@example.com>" or a plain e-mail address.
    - recipients: List of recipient e-mail addresses.
    - subject: Subject string.
    - message: HTML body content.
    - tool_config: Optional integration configuration list.
    - custom_headers: Optional mapping of header names to values.
    """
    api_key = get_sendgrid_api_key(tool_config)

    name, email_addr = parseaddr(sender)
    from_obj: Dict[str, str] = {"email": email_addr or sender}
    if name:
        from_obj["name"] = name

    to_list = [{"email": r} for r in recipients if r]
    if not to_list:
        return {"error": "No recipients provided"}

    plain_body, html_body, _ = body_variants(message, body_format)
    content = [
        {"type": "text/plain", "value": plain_body},
        {"type": "text/html", "value": html_body},
    ]

    payload = {
        "personalizations": [
            {
                "to": to_list,
                "subject": subject,
            }
        ],
        "from": from_obj,
        "content": content,
    }

    if custom_headers:
        payload["headers"] = {
            header: str(value)
            for header, value in custom_headers.items()
            if header and value is not None
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=payload,
            ) as response:
                # SendGrid returns 202 Accepted on success with empty body
                if response.status == 202:
                    return {"status": 202, "message": "accepted"}
                # On error, try to parse JSON for helpful message
                try:
                    err = await response.json()
                except Exception:
                    err = {"text": await response.text()}
                return {"error": err, "status": response.status}
    except Exception as ex:
        logging.warning(f"Error sending email via SendGrid: {ex}")
        return {"error": str(ex)}


async def send_email_using_sendgrid_async(
    ctx: SendEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> str:
    """
    Provider-style wrapper for SendGrid using SendEmailContext.
    Returns an opaque token since SendGrid does not return a message id.
    """
    plain_body, html_body, _ = body_variants(
        ctx.body,
        getattr(ctx, "body_format", None),
    )
    result = await send_email_with_sendgrid(
        sender=f"{ctx.sender_name} <{ctx.sender_email}>",
        recipients=[ctx.recipient],
        subject=ctx.subject,
        message=ctx.body or "",
        body_format=getattr(ctx, "body_format", None),
        tool_config=tool_config,
        custom_headers=getattr(ctx, "headers", None),
    )
    # Normalise output to a string id-like value
    if isinstance(result, dict) and result.get("status") == 202:
        return f"sent:{ctx.sender_email}:{ctx.recipient}:{ctx.subject}"
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"SendGrid send failed: {result['error']}")
    return str(result)
