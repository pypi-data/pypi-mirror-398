import base64
import json
import logging
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import httpx

from dhisana.schemas.common import (
    SendEmailContext,
    QueryEmailContext,
    ReplyEmailContext,
)
from dhisana.schemas.sales import MessageItem
from dhisana.utils.email_parse_helpers import (
    find_header,
    parse_single_address,
    find_all_recipients_in_headers,
    convert_date_to_iso,
    extract_email_body_in_plain_text,
)
from dhisana.utils.assistant_tool_tag import assistant_tool
from dhisana.utils.cache_output_tools import retrieve_output, cache_output
from dhisana.utils.email_body_utils import body_variants
from typing import Optional as _Optional  # avoid name clash in wrappers

def _status_phrase(code: int) -> str:
    mapping = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        412: "Precondition Failed",
        415: "Unsupported Media Type",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return mapping.get(code, "HTTP Error")


def _extract_google_api_message(response: Optional[httpx.Response]) -> str:
    """Extract a concise message from Google-style error JSON responses."""
    if not response:
        return ""
    try:
        data = response.json()
    except Exception:
        text = getattr(response, "text", None)
        return text or ""

    msg = None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            msg = err.get("message") or err.get("status")
        elif isinstance(err, str):
            # Some endpoints return string error + error_description
            msg = data.get("error_description") or err
        if not msg:
            msg = data.get("message") or data.get("text")
    return msg or ""


def _rethrow_with_google_message(exc: httpx.HTTPStatusError, context: str) -> None:
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None) or 0
    phrase = _status_phrase(int(code))
    api_msg = _extract_google_api_message(resp) or "Google API request failed."
    raise httpx.HTTPStatusError(
        f"{code} {phrase} ({context}). {api_msg}", request=exc.request, response=resp
    )


def get_google_access_token(tool_config: Optional[List[Dict]] = None) -> str:
    """
    Retrieve a Google OAuth2 access token from the 'google' integration config.

    Expected tool_config shape:
        {
          "name": "google",
          "configuration": [
            {"name": "oauth_tokens", "value": {"access_token": "..."} }
            # or {"name": "access_token", "value": "..."}
          ]
        }

    If provided as a JSON string under oauth_tokens, it is parsed.
    """
    access_token: Optional[str] = None

    if tool_config:
        g_cfg = next((c for c in tool_config if c.get("name") == "google"), None)
        if g_cfg:
            cfg_map = {f["name"]: f.get("value") for f in g_cfg.get("configuration", []) if f}
            raw_oauth = cfg_map.get("oauth_tokens")
            # oauth_tokens might be a JSON string or a dict
            if isinstance(raw_oauth, str):
                try:
                    raw_oauth = json.loads(raw_oauth)
                except Exception:
                    raw_oauth = None
            if isinstance(raw_oauth, dict):
                access_token = raw_oauth.get("access_token") or raw_oauth.get("token")
            if not access_token:
                access_token = cfg_map.get("access_token")

    if not access_token:
        raise ValueError(
            "Google integration is not configured. Please connect Google and supply an OAuth access token."
        )
    return access_token


async def send_email_using_google_oauth_async(
    send_email_context: SendEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> str:
    """
    Send an email using Gmail API with a per-user OAuth2 token.

    Returns the Gmail message id of the sent message when available.
    """
    token = get_google_access_token(tool_config)

    plain_body, html_body, resolved_fmt = body_variants(
        send_email_context.body,
        getattr(send_email_context, "body_format", None),
    )
    # Use multipart/alternative when we have both; fall back to single part for pure text.
    if resolved_fmt == "text":
        message = MIMEText(plain_body, "plain", _charset="utf-8")
    else:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(plain_body, "plain", _charset="utf-8"))
        message.attach(MIMEText(html_body, "html", _charset="utf-8"))

    message["to"] = send_email_context.recipient
    message["from"] = f"{send_email_context.sender_name} <{send_email_context.sender_email}>"
    message["subject"] = send_email_context.subject

    extra_headers = getattr(send_email_context, "headers", None) or {}
    for header, value in extra_headers.items():
        if not header or value is None:
            continue
        message[header] = str(value)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload: Dict[str, Any] = {"raw": raw_message}
    if send_email_context.labels:
        payload["labelIds"] = send_email_context.labels

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json() or {}
            return data.get("id", "")
        except httpx.HTTPStatusError as exc:
            _rethrow_with_google_message(exc, "Gmail Send OAuth")


async def list_emails_in_time_range_google_oauth_async(
    context: QueryEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> List[MessageItem]:
    """
    List Gmail messages for the connected user in a time range using OAuth2.
    Returns a list of MessageItem.
    """
    if context.labels is None:
        context.labels = []

    token = get_google_access_token(tool_config)
    base_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    headers = {"Authorization": f"Bearer {token}"}

    # Convert RFC3339 times to unix timestamps for Gmail search query
    # Expecting context.start_time and context.end_time as ISO 8601; Gmail q uses epoch seconds
    from datetime import datetime
    start_dt = datetime.fromisoformat(context.start_time.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(context.end_time.replace("Z", "+00:00"))
    after_ts = int(start_dt.timestamp())
    before_ts = int(end_dt.timestamp())

    q_parts: List[str] = [f"after:{after_ts}", f"before:{before_ts}"]
    if context.unread_only:
        q_parts.append("is:unread")
    if context.labels:
        q_parts.extend([f"label:{lbl}" for lbl in context.labels])
    query = " ".join(q_parts)

    params = {"q": query, "maxResults": 100}

    items: List[MessageItem] = []
    max_fetch = 500  # defensive cap to avoid excessive paging
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            next_page_token = None
            while True:
                page_params = dict(params)
                if next_page_token:
                    page_params["pageToken"] = next_page_token

                list_resp = await client.get(base_url, headers=headers, params=page_params)
                list_resp.raise_for_status()
                list_data = list_resp.json() or {}
                for m in list_data.get("messages", []) or []:
                    if len(items) >= max_fetch:
                        break
                    mid = m.get("id")
                    tid = m.get("threadId")
                    if not mid:
                        continue
                    get_url = f"{base_url}/{mid}"
                    get_resp = await client.get(get_url, headers=headers)
                    get_resp.raise_for_status()
                    mdata = get_resp.json() or {}

                    headers_list = (mdata.get("payload") or {}).get("headers", [])
                    from_header = find_header(headers_list, "From") or ""
                    subject_header = find_header(headers_list, "Subject") or ""
                    date_header = find_header(headers_list, "Date") or ""

                    iso_dt = convert_date_to_iso(date_header)
                    s_name, s_email = parse_single_address(from_header)
                    r_name, r_email = find_all_recipients_in_headers(headers_list)

                    items.append(
                        MessageItem(
                            message_id=mdata.get("id", ""),
                            thread_id=tid or "",
                            sender_name=s_name,
                            sender_email=s_email,
                            receiver_name=r_name,
                            receiver_email=r_email,
                            iso_datetime=iso_dt,
                            subject=subject_header,
                            body=extract_email_body_in_plain_text(mdata),
                        )
                    )

                if len(items) >= max_fetch:
                    break

                next_page_token = list_data.get("nextPageToken")
                if not next_page_token:
                    break
        except httpx.HTTPStatusError as exc:
            _rethrow_with_google_message(exc, "Gmail List OAuth")

    return items


async def reply_to_email_google_oauth_async(
    reply_email_context: ReplyEmailContext,
    tool_config: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Reply-all to a Gmail message for the connected user using OAuth2.
    Returns a metadata dictionary similar to other providers.
    """
    if reply_email_context.add_labels is None:
        reply_email_context.add_labels = []

    token = get_google_access_token(tool_config)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base = "https://gmail.googleapis.com/gmail/v1/users/me"

    # 1) Fetch original message
    get_url = f"{base}/messages/{reply_email_context.message_id}"
    params = {"format": "full"}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            get_resp = await client.get(get_url, headers=headers, params=params)
            get_resp.raise_for_status()
            original = get_resp.json() or {}
        except httpx.HTTPStatusError as exc:
            _rethrow_with_google_message(exc, "Gmail Fetch Message OAuth")

    headers_list = (original.get("payload") or {}).get("headers", [])
    # Use case-insensitive lookups via find_header to avoid missing values on header casing differences.
    subject = find_header(headers_list, "Subject") or ""
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"
    reply_to_header = find_header(headers_list, "Reply-To") or ""
    from_header = find_header(headers_list, "From") or ""
    to_header = find_header(headers_list, "To") or ""
    cc_header = find_header(headers_list, "Cc") or ""
    message_id_header = find_header(headers_list, "Message-ID") or ""
    thread_id = original.get("threadId")

    sender_email_lc = (reply_email_context.sender_email or "").lower()

    def _is_self(addr: str) -> bool:
        return bool(sender_email_lc) and sender_email_lc in addr.lower()

    cc_addresses = cc_header or ""
    # Prefer Reply-To unless it points back to the sender. If the original was SENT mail,
    # From will equal the sender, so we should reply to the original To/CC instead.
    if reply_to_header and not _is_self(reply_to_header):
        to_addresses = reply_to_header
    elif from_header and not _is_self(from_header):
        to_addresses = from_header
    elif to_header and not _is_self(to_header):
        to_addresses = to_header
    else:
        combined = ", ".join([v for v in (to_header, cc_header, from_header) if v])
        to_addresses = combined
        cc_addresses = ""

    if (not to_addresses or _is_self(to_addresses)) and reply_email_context.fallback_recipient:
        if not _is_self(reply_email_context.fallback_recipient):
            to_addresses = reply_email_context.fallback_recipient
            cc_addresses = ""

    if not to_addresses or _is_self(to_addresses):
        raise ValueError(
            "No valid recipient found in the original message; refusing to reply to sender."
        )

    # 2) Build reply MIME
    plain_reply, html_reply, resolved_reply_fmt = body_variants(
        reply_email_context.reply_body,
        getattr(reply_email_context, "reply_body_format", None),
    )
    if resolved_reply_fmt == "text":
        msg = MIMEText(plain_reply, "plain", _charset="utf-8")
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(plain_reply, "plain", _charset="utf-8"))
        msg.attach(MIMEText(html_reply, "html", _charset="utf-8"))

    msg["To"] = to_addresses
    if cc_addresses:
        msg["Cc"] = cc_addresses
    msg["From"] = f"{reply_email_context.sender_name} <{reply_email_context.sender_email}>"
    msg["Subject"] = subject
    if message_id_header:
        msg["In-Reply-To"] = message_id_header
        msg["References"] = message_id_header

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = {"raw": raw_message}
    if thread_id:
        payload["threadId"] = thread_id

    # 3) Send the reply
    send_url = f"{base}/messages/send"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            send_resp = await client.post(send_url, headers=headers, json=payload)
            send_resp.raise_for_status()
            sent = send_resp.json() or {}
        except httpx.HTTPStatusError as exc:
            _rethrow_with_google_message(exc, "Gmail Send Reply OAuth")

    # 4) Optional: mark as read
    if str(reply_email_context.mark_as_read).lower() == "true" and thread_id:
        modify_url = f"{base}/threads/{thread_id}/modify"
        modify_payload = {"removeLabelIds": ["UNREAD"]}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(modify_url, headers=headers, json=modify_payload)
        except Exception:
            logging.exception("Gmail: failed to mark thread as read (best-effort)")

    # 5) Optional: add labels
    if reply_email_context.add_labels and thread_id:
        modify_url = f"{base}/threads/{thread_id}/modify"
        modify_payload = {"addLabelIds": reply_email_context.add_labels}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(modify_url, headers=headers, json=modify_payload)
        except Exception:
            logging.exception("Gmail: failed to add labels to thread (best-effort)")

    return {
        "mailbox_email_id": sent.get("id"),
        "message_id": (sent.get("threadId") or thread_id or ""),
        "email_subject": subject,
        "email_sender": reply_email_context.sender_email,
        "email_recipients": [to_addresses] + ([cc_addresses] if cc_addresses else []),
        "read_email_status": "READ" if str(reply_email_context.mark_as_read).lower() == "true" else "UNREAD",
        "email_labels": sent.get("labelIds", []),
    }


# ---------------------------------------------------------------------------
# Google Calendar (OAuth per-user)
# ---------------------------------------------------------------------------

@assistant_tool
async def get_calendar_events_using_google_oauth_async(
    start_date: str,
    end_date: str,
    tool_config: Optional[List[Dict]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve events from the user's primary Google Calendar using a per-user OAuth token.

    start_date, end_date: 'YYYY-MM-DD' strings (inclusive start, inclusive end day as 23:59:59Z).
    Returns a list of event dicts from the Calendar API.
    """
    token = get_google_access_token(tool_config)
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    time_min = f"{start_date}T00:00:00Z"
    time_max = f"{end_date}T23:59:59Z"
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "maxResults": 10,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json() or {}
            events = data.get("items", [])
            if not events:
                logging.info("No upcoming events found within the specified range (OAuth).")
            return events
        except httpx.HTTPStatusError as exc:
            _rethrow_with_google_message(exc, "Calendar OAuth")


# ---------------------------------------------------------------------------
# Google Sheets and Docs (OAuth per-user)
# ---------------------------------------------------------------------------

def _get_sheet_id_from_url(sheet_url: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9-_]+)/", sheet_url)
    if not match:
        raise ValueError("Could not extract spreadsheet ID from the provided URL.")
    return match.group(1)


def _get_document_id_from_url(doc_url: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9-_]+)/", doc_url)
    if not match:
        raise ValueError("Could not extract document ID from the provided URL.")
    return match.group(1)


@assistant_tool
async def read_google_sheet_using_google_oauth(
    sheet_url: str,
    range_name: str,
    tool_config: Optional[List[Dict]] = None,
) -> List[List[str]]:
    """
    Read data from a Google Sheet using the connected user's OAuth token.

    If range_name is empty, reads the first sheet tab by fetching spreadsheet metadata.
    """
    token = get_google_access_token(tool_config)
    headers = {"Authorization": f"Bearer {token}"}

    # If the GCP project requires a quota/billing project with OAuth, allow an optional header
    def _quota_project(cfg: _Optional[List[Dict]]) -> _Optional[str]:
        try:
            g_cfg = next((c for c in (cfg or []) if c.get("name") == "google"), None)
            if not g_cfg:
                return None
            cmap = {f["name"]: f.get("value") for f in g_cfg.get("configuration", []) if f}
            return (
                cmap.get("quota_project")
                or cmap.get("quotaProjectId")
                or cmap.get("project_id")
                or cmap.get("x_goog_user_project")
                or cmap.get("google_cloud_project")
            )
        except Exception:
            return None

    qp = _quota_project(tool_config)
    if qp:
        headers["X-Goog-User-Project"] = qp

    spreadsheet_id = _get_sheet_id_from_url(sheet_url)

    async def _oauth_fetch() -> List[List[str]]:
        nonlocal range_name
        # Default range to first sheet title if not supplied
        if not range_name:
            meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            params = {"fields": "sheets(properties(title))"}
            async with httpx.AsyncClient(timeout=30) as client:
                meta_resp = await client.get(meta_url, headers=headers, params=params)
                meta_resp.raise_for_status()
                meta = meta_resp.json() or {}
                sheets = meta.get("sheets", [])
                if not sheets:
                    return []
                range_name = (sheets[0].get("properties") or {}).get("title") or "Sheet1"

        values_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
        async with httpx.AsyncClient(timeout=30) as client:
            val_resp = await client.get(values_url, headers=headers)
            val_resp.raise_for_status()
            data = val_resp.json() or {}
            return data.get("values", [])

    try:
        return await _oauth_fetch()
    except httpx.HTTPStatusError as exc:
        # If OAuth fails with 403 (likely insufficient scope or access), fail with clear guidance
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status == 403:
            api_msg = _extract_google_api_message(exc.response) or "Access forbidden by Google API (403)."
            guidance = (
                "Google Sheets access denied with OAuth. Ensure the connected Google account can access the spreadsheet "
                "(share with the account if private) and that the OAuth token includes the Sheets scope "
                "('https://www.googleapis.com/auth/spreadsheets.readonly' or 'https://www.googleapis.com/auth/spreadsheets')."
            )
            raise httpx.HTTPStatusError(
                f"403 Forbidden (Sheets OAuth). {api_msg} {guidance}", request=exc.request, response=exc.response
            )
        # For other statuses, rethrow with Google's message
        _rethrow_with_google_message(exc, "Sheets OAuth")


@assistant_tool
async def read_google_document_using_google_oauth(
    doc_url: str,
    tool_config: Optional[List[Dict]] = None,
) -> str:
    """
    Read text content from a Google Doc using the connected user's OAuth token.
    Concatenates all text runs in the document body.
    """
    token = get_google_access_token(tool_config)
    headers = {"Authorization": f"Bearer {token}"}

    document_id = _get_document_id_from_url(doc_url)
    url = f"https://docs.googleapis.com/v1/documents/{document_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            doc = resp.json() or {}
        except httpx.HTTPStatusError as exc:
            _rethrow_with_google_message(exc, "Docs OAuth")

    content = (doc.get("body") or {}).get("content", [])
    parts: List[str] = []
    for element in content:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for elem in paragraph.get("elements", []) or []:
            text_run = elem.get("textRun")
            if text_run:
                parts.append(text_run.get("content", ""))

    return "".join(parts)


@assistant_tool
async def search_google_custom_search(
    query: str,
    number_of_results: int = 10,
    offset: int = 0,
    tool_config: _Optional[List[Dict]] = None,
    as_oq: _Optional[str] = None,
) -> List[str]:
    """
    Search Google using the Custom Search JSON API with a per-user OAuth token.

    Requires a Programmable Search Engine ID (cx) from the 'google_custom_search' integration
    or env var 'GOOGLE_SEARCH_CX'. Returns a list of JSON strings with
    { position, title, link, snippet } items.
    """
    # Final query composition
    full_query = query if not as_oq else f"{query} {as_oq}"

    # Acquire OAuth token and CX id
    token = get_google_access_token(tool_config)

    cx: Optional[str] = None
    if tool_config:
        gcs_cfg = next((c for c in tool_config if c.get("name") == "google_custom_search"), None)
        if gcs_cfg:
            cfg_map = {f["name"]: f.get("value") for f in gcs_cfg.get("configuration", []) if f}
            cx = cfg_map.get("cx")
    if not cx:
        import os as _os
        cx = _os.environ.get("GOOGLE_SEARCH_CX")
    if not cx:
        err = (
            "Google Custom Search CX is not configured. Please add 'google_custom_search' integration with 'cx',"
            " or set GOOGLE_SEARCH_CX."
        )
        logging.error(err)
        return [json.dumps({"error": err})]

    # Pagination: start=1-based index
    start_index = max(1, int(offset) + 1)

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": full_query,
        "num": number_of_results,
        "start": start_index,
        "cx": cx,
    }
    headers = {"Authorization": f"Bearer {token}"}

    cache_key = f"oauth_cse:{full_query}:{number_of_results}:{offset}:{cx}"
    cached = retrieve_output("search_google_custom_search_oauth", cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 429:
                return [json.dumps({"error": "Rate limit exceeded (429)"})]
            resp.raise_for_status()
            data = resp.json() or {}

            items = data.get("items", []) or []
            norm: List[Dict[str, Any]] = []
            for i, item in enumerate(items):
                norm.append({
                    "position": i + 1,
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            out = [json.dumps(o) for o in norm]
            cache_output("search_google_custom_search_oauth", cache_key, out)
            return out
        except httpx.HTTPStatusError as exc:
            try:
                err_json = exc.response.json()
            except Exception:
                err_json = {"status": exc.response.status_code, "text": exc.response.text}
            logging.warning(f"CSE OAuth request failed: {err_json}")
            return [json.dumps({"error": err_json})]
        except Exception as e:
            logging.exception("CSE OAuth request failed")
            return [json.dumps({"error": str(e)})]

@assistant_tool
async def search_google_places(
    query: str,
    location_bias: dict = None,
    number_of_results: int = 3,
    tool_config: _Optional[List[Dict]] = None,
) -> List[str]:
    """
    Search Google Places (New) with a per-user OAuth token.

    - Requires that the OAuth token has Maps/Places access enabled for the project.
    - Returns a list of JSON strings, each being a place object.
    """
    

    token = get_google_access_token(tool_config)
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        # Field mask is required to limit returned fields
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,places.location,"
            "places.websiteUri,places.rating,places.reviews"
        ),
    }

    body: Dict[str, Any] = {"textQuery": query}
    if location_bias:
        body["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": location_bias.get("latitude"),
                    "longitude": location_bias.get("longitude"),
                },
                "radius": location_bias.get("radius", 5000),
            }
        }

    # Cache key based on query, count and bias
    bias_str = json.dumps(location_bias, sort_keys=True) if location_bias else "None"
    cache_key = f"oauth_places:{query}:{number_of_results}:{bias_str}"
    cached = retrieve_output("search_google_places_oauth", cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code == 429:
                return [json.dumps({"error": "Rate limit exceeded (429)"})]
            resp.raise_for_status()
            data = resp.json() or {}
            places = (data.get("places") or [])[: max(0, int(number_of_results))]
            out = [json.dumps(p) for p in places]
            cache_output("search_google_places_oauth", cache_key, out)
            return out
        except httpx.HTTPStatusError as exc:
            try:
                err_json = exc.response.json()
            except Exception:
                err_json = {"status": exc.response.status_code, "text": exc.response.text}
            logging.warning(f"Places OAuth request failed: {err_json}")
            return [json.dumps({"error": err_json})]
        except Exception as e:
            logging.exception("Places OAuth request failed")
            return [json.dumps({"error": str(e)})]
