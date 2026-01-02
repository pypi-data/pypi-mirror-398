import asyncio
import logging
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional

import httpx

from dhisana.schemas.common import (
    SendEmailContext,
    QueryEmailContext,
    ReplyEmailContext,
)
from dhisana.schemas.sales import MessageItem
from dhisana.utils.email_body_utils import body_variants


def get_microsoft365_access_token(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieve a Microsoft Graph OAuth2 access token from tool_config or env.

    Expected tool_config shape (similar to HubSpot):
        {
          "name": "microsoft365",
          "configuration": [
            {"name": "oauth_tokens", "value": {"access_token": "..."} }
            # or {"name": "access_token", "value": "..."}
          ]
        }

    This helper no longer reads environment variables; the token must be supplied
    via the microsoft365 integration's configuration.
    """
    access_token: Optional[str] = None

    if tool_config:
        ms_cfg = next((c for c in tool_config if c.get("name") == "microsoft365"), None)
        if ms_cfg:
            cfg_map = {f["name"]: f.get("value") for f in ms_cfg.get("configuration", []) if f}
            raw_oauth = cfg_map.get("oauth_tokens")
            # If oauth_tokens is a JSON string, parse; if dict, read directly
            if isinstance(raw_oauth, str):
                try:
                    raw_oauth = json.loads(raw_oauth)
                except Exception:
                    raw_oauth = None
            if isinstance(raw_oauth, dict):
                access_token = raw_oauth.get("access_token") or raw_oauth.get("token")
            if not access_token:
                access_token = cfg_map.get("access_token") or cfg_map.get("apiKey")

    if not access_token:
        raise ValueError(
            "Microsoft 365 integration is not configured. Please connect Microsoft 365 in Integrations and provide an OAuth access token."
        )
    return access_token


def _get_m365_auth_mode(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Determine auth mode: 'delegated' (default) or 'application'.
    Looks for configuration fields in the microsoft365 integration:
      - auth_mode: 'delegated' | 'application'
      - use_application_permissions: true/false (string or bool)
    """
    mode = "delegated"
    if tool_config:
        ms_cfg = next((c for c in tool_config if c.get("name") == "microsoft365"), None)
        if ms_cfg:
            cfg_map = {f["name"]: f.get("value") for f in ms_cfg.get("configuration", []) if f}
            raw_mode = (
                cfg_map.get("auth_mode")
                or cfg_map.get("authMode")
                or cfg_map.get("mode")
            )
            if isinstance(raw_mode, str) and raw_mode:
                val = raw_mode.strip().lower()
                if val in ("application", "app", "service", "service_account"):
                    return "application"
                if val in ("delegated", "user"):
                    return "delegated"
            uap = cfg_map.get("use_application_permissions") or cfg_map.get("applicationPermissions")
            if isinstance(uap, str):
                if uap.strip().lower() in ("true", "1", "yes", "y"):  # truthy
                    return "application"
            elif isinstance(uap, bool) and uap:
                return "application"
    return mode


def _base_resource(sender_email: Optional[str], tool_config: Optional[List[Dict]], auth_mode: Optional[str] = None) -> str:
    mode = (auth_mode or _get_m365_auth_mode(tool_config)).lower()
    if mode == "application":
        if not sender_email:
            raise ValueError("sender_email is required when using application permissions.")
        return f"/users/{sender_email}"
    # Delegated (per-user) uses /me
    return "/me"


def _token_has_mail_read_scope(token: str) -> bool:
    """
    Best-effort check if the OAuth token includes Mail.Read or Mail.ReadWrite.
    Works for both delegated ("scp") and app-only ("roles"). No signature verification.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return False
        import base64

        def _b64url_decode(segment: str) -> bytes:
            pad = "=" * (-len(segment) % 4)
            return base64.urlsafe_b64decode(segment + pad)

        payload_bytes = _b64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))

        scopes = set()
        scp = payload.get("scp")
        if isinstance(scp, str):
            scopes.update(s.strip() for s in scp.split(" ") if s.strip())

        roles = payload.get("roles")
        if isinstance(roles, list):
            scopes.update(r for r in roles if isinstance(r, str))

        return any(s in scopes for s in ("Mail.ReadWrite", "Mail.Read"))
    except Exception:
        return False


async def send_email_using_microsoft_graph_async(
    send_email_context: SendEmailContext,
    tool_config: Optional[List[Dict]] = None,
    auth_mode: Optional[str] = None,
) -> str:
    """
    Send an email via Microsoft Graph API using an OAuth2 access token.

    Uses the /sendMail endpoint which only requires Mail.Send permission.
    Returns a best-effort string identifier (not a Graph message ID) since
    /sendMail responds 202 with no body. If higher privileges are present
    (Mail.Read*), callers should locate the actual message ID from Sent Items
    separately if they need it.
    """
    token = get_microsoft365_access_token(tool_config)
    sender_email = send_email_context.sender_email

    base_url = "https://graph.microsoft.com/v1.0"
    base_res = _base_resource(sender_email, tool_config, auth_mode)

    plain_body, html_body, resolved_fmt = body_variants(
        send_email_context.body,
        getattr(send_email_context, "body_format", None),
    )
    content_type = "Text" if resolved_fmt == "text" else "HTML"
    content_body = plain_body if resolved_fmt == "text" else html_body

    message_payload: Dict[str, Any] = {
        "subject": send_email_context.subject,
        "body": {
            "contentType": content_type,
            "content": content_body,
        },
        "toRecipients": [
            {"emailAddress": {"address": send_email_context.recipient}}
        ],
    }

    extra_headers = getattr(send_email_context, "headers", None) or {}
    if extra_headers:
        message_payload["internetMessageHeaders"] = [
            {"name": header, "value": str(value)}
            for header, value in extra_headers.items()
            if header and value is not None
        ]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        send_url = f"{base_url}{base_res}/sendMail"
        send_body = {
            "message": message_payload,
            "saveToSentItems": True,
        }
        send_resp = await client.post(send_url, headers=headers, json=send_body)
        send_resp.raise_for_status()  # expect 202 Accepted

    # Attempt to fetch the just-sent message from Sent Items regardless of scopes.
    # If the token lacks read scopes, a 401/403 is expected; log and continue.
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
            # Normalize to Z suffix
            since = since.replace("+00:00", "Z")
            params = {
                "$select": "id,subject,toRecipients,ccRecipients,sentDateTime,createdDateTime",
                "$orderby": "sentDateTime desc",
                "$top": "25",
                "$filter": f"sentDateTime ge {since}",
            }
            list_url = f"{base_url}{base_res}/mailFolders/SentItems/messages"
            resp = await client.get(list_url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json() or {}
            target_subject = (send_email_context.subject or "").strip()
            target_to = (send_email_context.recipient or "").strip().lower()
            for m in data.get("value", []):
                subj = (m.get("subject") or "").strip()
                if subj != target_subject:
                    continue
                # Gather recipient addresses
                recips: List[str] = []
                for r in m.get("toRecipients", []) or []:
                    addr = ((r.get("emailAddress") or {}).get("address") or "").strip().lower()
                    if addr:
                        recips.append(addr)
                if target_to and target_to in recips:
                    msg_id = m.get("id")
                    if msg_id:
                        return msg_id
    except httpx.HTTPStatusError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (401, 403):
            logging.warning(
                "Microsoft Graph: insufficient read scope (status %s) while fetching sent message id; skipping.",
                status,
            )
        else:
            logging.exception(
                "Microsoft Graph: unable to retrieve sent message id; continuing without it"
            )
    except Exception:
        logging.exception(
            "Microsoft Graph: unable to retrieve sent message id; continuing without it"
        )

    # Fall back: we cannot reliably return the Graph message ID without a lookup
    # or if we didn't find it. Return a best‑effort opaque token for correlation.
    return f"sent:{send_email_context.sender_email}:{send_email_context.recipient}:{send_email_context.subject}"


def _join_people(emails: List[Dict[str, Any]]) -> tuple[str, str]:
    names: List[str] = []
    addrs: List[str] = []
    for entry in emails or []:
        addr = entry.get("emailAddress", {})
        names.append(addr.get("name") or "")
        addrs.append(addr.get("address") or "")
    return ", ".join([n for n in names if n]), ", ".join([a for a in addrs if a])


async def list_emails_in_time_range_m365_async(
    context: QueryEmailContext,
    tool_config: Optional[List[Dict]] = None,
    auth_mode: Optional[str] = None,
) -> List[MessageItem]:
    """
    List messages in a time range using Microsoft Graph.

    Interprets labels as Outlook categories when provided.
    """
    if context.labels is None:
        context.labels = []

    token = get_microsoft365_access_token(tool_config)
    base_url = "https://graph.microsoft.com/v1.0"
    base_res = _base_resource(context.sender_email, tool_config, auth_mode)
    headers = {"Authorization": f"Bearer {token}"}

    # Build $filter
    filters: List[str] = [
        f"receivedDateTime ge {context.start_time}",
        f"receivedDateTime le {context.end_time}",
    ]
    if context.unread_only:
        filters.append("isRead eq false")
    if context.labels:
        cats = [f"categories/any(c:c eq '{lbl}')" for lbl in context.labels]
        filters.append("( " + " or ".join(cats) + " )")
    filter_q = " and ".join(filters)

    # Select minimal fields and sort newest first
    select = (
        "id,conversationId,subject,from,toRecipients,ccRecipients,receivedDateTime,"
        "bodyPreview,internetMessageId,categories"
    )
    top = 50
    url = (
        f"{base_url}{base_res}/messages"
        f"?$select={select}&$orderby=receivedDateTime desc&$top={top}&$filter={httpx.QueryParams({'f': filter_q})['f']}"
    )

    items: List[MessageItem] = []
    async with httpx.AsyncClient(timeout=30) as client:
        next_url = url
        fetched = 0
        max_fetch = 200
        while next_url and fetched < max_fetch:
            resp = await client.get(next_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            for m in data.get("value", []):
                s_name = (m.get("from", {}).get("emailAddress", {}) or {}).get("name") or ""
                s_email = (m.get("from", {}).get("emailAddress", {}) or {}).get("address") or ""
                to_names, to_emails = _join_people(m.get("toRecipients", []))
                cc_names, cc_emails = _join_people(m.get("ccRecipients", []))
                receiver_name = ", ".join([v for v in [to_names, cc_names] if v])
                receiver_email = ", ".join([v for v in [to_emails, cc_emails] if v])

                items.append(
                    MessageItem(
                        message_id=m.get("id", ""),
                        thread_id=m.get("conversationId", ""),
                        sender_name=s_name,
                        sender_email=s_email,
                        receiver_name=receiver_name,
                        receiver_email=receiver_email,
                        iso_datetime=m.get("receivedDateTime", ""),
                        subject=m.get("subject", ""),
                        body=m.get("bodyPreview", ""),
                    )
                )
                fetched += 1
            next_url = data.get("@odata.nextLink")
            if next_url and fetched >= max_fetch:
                break

    return items


async def reply_to_email_m365_async(
    reply_email_context: ReplyEmailContext,
    tool_config: Optional[List[Dict]] = None,
    auth_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Reply-all to a message using Microsoft Graph. Returns basic metadata similar to GW helper.
    """
    if reply_email_context.add_labels is None:
        reply_email_context.add_labels = []

    token = get_microsoft365_access_token(tool_config)
    base_url = "https://graph.microsoft.com/v1.0"
    base_res = _base_resource(reply_email_context.sender_email, tool_config, auth_mode)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1) Fetch original message for context (subject, recipients, thread)
    async with httpx.AsyncClient(timeout=30) as client:
        get_url = f"{base_url}{base_res}/messages/{reply_email_context.message_id}"
        get_resp = await client.get(get_url, headers=headers)
        get_resp.raise_for_status()
        orig = get_resp.json()

        orig_subject = orig.get("subject", "")
        subject = orig_subject if orig_subject.startswith("Re:") else f"Re: {orig_subject}"
        thread_id = orig.get("conversationId", "")
        cc_list = orig.get("ccRecipients", [])
        to_list = orig.get("toRecipients", [])
        sender_email_lc = (reply_email_context.sender_email or "").lower()

        def _is_self(addr: str) -> bool:
            return bool(sender_email_lc) and sender_email_lc in addr.lower()

        def _addresses(recipients: List[Dict[str, Any]]) -> List[str]:
            return [
                (recipient.get("emailAddress", {}) or {}).get("address", "")
                for recipient in recipients
                if recipient
            ]

        to_addresses = ", ".join(
            [addr for addr in _addresses(to_list) if addr and not _is_self(addr)]
        )
        cc_addresses = ", ".join(
            [addr for addr in _addresses(cc_list) if addr and not _is_self(addr)]
        )

        all_recipients = [addr for addr in _addresses(to_list + cc_list) if addr]
        if not any(all_recipients):
            from_addr = orig.get("from", {}).get("emailAddress", {})
            from_address = from_addr.get("address", "")
            if from_address:
                all_recipients.append(from_address)

        non_self_recipients = [addr for addr in all_recipients if not _is_self(addr)]
        if not non_self_recipients and reply_email_context.fallback_recipient:
            fr = reply_email_context.fallback_recipient
            if fr and not _is_self(fr):
                non_self_recipients.append(fr)

        if not to_addresses and non_self_recipients:
            to_addresses = ", ".join(non_self_recipients)
            cc_addresses = ""

        if not non_self_recipients:
            raise httpx.HTTPStatusError(
                "No valid recipient found in the original message; refusing to reply to sender.",
                request=get_resp.request,
                response=get_resp,
            )

        # 2) Create reply-all draft with comment
        create_reply_url = (
            f"{base_url}{base_res}/messages/{reply_email_context.message_id}/createReplyAll"
        )
        create_payload = {"comment": reply_email_context.reply_body}
        create_resp = await client.post(create_reply_url, headers=headers, json=create_payload)
        create_resp.raise_for_status()
        reply_msg = create_resp.json()
        reply_id = reply_msg.get("id")

        # 3) Optionally add categories (labels) to the reply draft
        if reply_email_context.add_labels:
            patch_url = f"{base_url}{base_res}/messages/{reply_id}"
            categories = list(set((reply_msg.get("categories") or []) + reply_email_context.add_labels))
            await client.patch(patch_url, headers=headers, json={"categories": categories})

        # 4) Send the reply
        send_url = f"{base_url}{base_res}/messages/{reply_id}/send"
        send_resp = await client.post(send_url, headers=headers)
        send_resp.raise_for_status()

        # 5) Optionally mark original as read
        if str(reply_email_context.mark_as_read).lower() == "true":
            mark_url = f"{base_url}{base_res}/messages/{reply_email_context.message_id}"
            await client.patch(mark_url, headers=headers, json={"isRead": True})

    # Attempt to fetch the sent message to get final details (best effort)
    email_labels: List[str] = reply_email_context.add_labels or []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            fetch_url = f"{base_url}{base_res}/messages/{reply_id}?$select=id,categories"
            fetch_resp = await client.get(fetch_url, headers=headers)
            if fetch_resp.status_code == 200:
                sent_obj = fetch_resp.json()
                email_labels = sent_obj.get("categories", email_labels)
    except Exception:
        pass

    sent_message_details = {
        "mailbox_email_id": reply_id,
        "message_id": thread_id,
        "email_subject": subject,
        "email_sender": reply_email_context.sender_email,
        "email_recipients": [to_addresses] + ([cc_addresses] if cc_addresses else []),
        "read_email_status": "READ" if str(reply_email_context.mark_as_read).lower() == "true" else "UNREAD",
        "email_labels": email_labels,
    }

    return sent_message_details
