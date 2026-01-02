import json
import logging
import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, List, Any, Optional
import requests

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - optional dependency
    AsyncOpenAI = None  # type: ignore

import aiohttp
from google.oauth2 import service_account
from googleapiclient.discovery import build
import imaplib
import aiosmtplib
from simple_salesforce import Salesforce
from urllib.parse import urljoin, urlparse

from dhisana.utils.clay_tools import push_to_clay_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If FindyMail uses a base URL in your environment, define it here:
FINDYMAIL_BASE_URL = "https://app.findymail.com/api"

###############################################################################
#                             HELPER FUNCTIONS
###############################################################################

async def safe_json(response: aiohttp.ClientResponse) -> Any:
    """
    Safely parse JSON from an aiohttp response.
    Returns None if parsing fails.
    """
    try:
        return await response.json()
    except Exception:
        return None

###############################################################################
#                         TOOL TEST FUNCTIONS
###############################################################################

async def test_zerobounce(api_key: str) -> Dict[str, Any]:
    url = f"https://api.zerobounce.net/v2/validate?api_key={api_key}&email=contact@dhisana.ai"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"Non-200 from ZeroBounce: {status}"
                    }
                # If the API key is invalid, ZeroBounce might return status=200 but "api_key_invalid"
                if data and data.get("status") == "invalid" and data.get("sub_status") == "api_key_invalid":
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": "ZeroBounce indicates invalid API key"
                    }
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"ZeroBounce test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_openai(api_key: str, model_name: str, reasoning_effort: str) -> Dict[str, Any]:
    """
    Tests OpenAI API key by making a simple chat completion request.
    - If the model name starts with 'o', includes 'reasoning_effort' in the request.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}

    # Base request body
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "max_completion_tokens": 5
    }

    # Only apply the reasoning parameter if it's an 'o' series model
    if model_name.startswith("o"):
        data["reasoning_effort"] = reasoning_effort

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=data) as response:
                status = response.status
                resp_data = await safe_json(response)

                if status != 200:
                    err_message = (
                        resp_data.get("error", {}).get("message")
                        if resp_data and isinstance(resp_data, dict)
                        else f"Non-200 from OpenAI: {status}"
                    )
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": err_message
                    }

                # Check if "error" is present in the response
                if resp_data and "error" in resp_data:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": resp_data["error"].get("message", "OpenAI error returned")
                    }

                return {"success": True, "status_code": status, "error_message": None}

    except Exception as e:
        logger.error(f"OpenAI test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_google_workspace(api_key: str, subject: str) -> Dict[str, Any]:
    """
    Tests Google Workspace by listing Gmail messages using domain-wide delegation.
    Requires subject (email) to impersonate. 'me' then refers to that user mailbox.
    """
    try:
        creds_info = json.loads(api_key)
        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://mail.google.com/"]
        )

        # Domain-wide delegation requires specifying the email to impersonate
        delegated_creds = creds.with_subject(subject)

        service = build("gmail", "v1", credentials=delegated_creds)

        # Execute synchronous call in a background thread to avoid blocking
        def _list_messages():
            return service.users().messages().list(userId="me").execute()

        response = await asyncio.to_thread(_list_messages)

        if "messages" in response:
            return {"success": True, "status_code": 200, "error_message": None}
        return {
            "success": False,
            "status_code": 200,
            "error_message": "API responded but no 'messages' key found"
        }
    except Exception as e:
        logger.error(f"Google Workspace test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_google_drive(api_key: str, subject: str) -> Dict[str, Any]:
    """Tests Google Drive API access using domain-wide delegation.

    Lists files in the impersonated user's Drive to verify the credentials.
    """
    try:
        creds_info = json.loads(api_key)
        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"],
        )

        delegated_creds = creds.with_subject(subject)

        service = build("drive", "v3", credentials=delegated_creds)

        def _list_files():
            return service.files().list(pageSize=1).execute()

        response = await asyncio.to_thread(_list_files)

        if "files" in response:
            return {"success": True, "status_code": 200, "error_message": None}
        return {
            "success": False,
            "status_code": 200,
            "error_message": "API responded but no 'files' key found",
        }
    except Exception as e:
        logger.error(f"Google Drive test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_serpapi(api_key: str) -> Dict[str, Any]:
    url = f"https://serpapi.com/search?engine=google&q=hello+world&api_key={api_key}"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    err_message = data.get("error") if data else f"Non-200 from SERPAPI: {status}"
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": err_message
                    }
                # Some SERP API errors might still be 200 but contain an 'error' field
                if data and "error" in data:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": data["error"]
                    }
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"SERP API test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


###############################################################################
#          UPDATED test_serperdev TO MATCH THE search_google_serper USAGE
###############################################################################
async def test_serperdev(api_key: str) -> Dict[str, Any]:
    """
    Tests Serper.dev by sending a POST request to https://google.serper.dev/search
    using similar headers/payload as `search_google_serper`.
    """
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": "Hello world from SerperDev",
        "gl": "us",
        "hl": "en",
        "autocorrect": True,
        "page": 1,
        "type": "search"
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"Non-200 from Serper.dev: {status}"
                    }
                # Check if "organic" in the JSON to confirm we got typical search results
                if data and "organic" in data and isinstance(data["organic"], list):
                    return {
                        "success": True,
                        "status_code": status,
                        "error_message": None
                    }
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": "No 'organic' field found in Serper.dev response"
                }
    except Exception as e:
        logger.error(f"SerperDev test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_proxycurl(api_key: str) -> Dict[str, Any]:
    url = "https://enrichlayer.com/api/v2/profile"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"linkedin_profile_url": "https://www.linkedin.com/in/satyanadella"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers, params=params) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    err_message = None
                    if data and isinstance(data, dict):
                        err_message = data.get("message") or data.get("detail")
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": err_message or f"Non-200 from Enrich Layer: {status}"
                    }
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"Enrich Layer test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_exa(api_key: str) -> Dict[str, Any]:
    """Verify Exa connectivity by issuing a minimal search request."""

    url = "https://api.exa.ai/search"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "query": "Dhisana connectivity check",
        "numResults": 1,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    err_message = None
                    if isinstance(data, dict):
                        err_message = (
                            data.get("message")
                            or data.get("error")
                            or data.get("detail")
                        )
                        if isinstance(err_message, dict):
                            err_message = err_message.get("message") or str(err_message)
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": err_message or f"Non-200 from Exa: {status}",
                    }

                if isinstance(data, dict):
                    if "error" in data:
                        error_value = data["error"]
                        if isinstance(error_value, dict):
                            error_value = error_value.get("message") or str(error_value)
                        return {
                            "success": False,
                            "status_code": status,
                            "error_message": str(error_value),
                        }

                    results = data.get("results")
                    if isinstance(results, list):
                        return {"success": True, "status_code": status, "error_message": None}

                return {
                    "success": False,
                    "status_code": status,
                    "error_message": "Unexpected response from Exa API.",
                }
    except Exception as exc:
        logger.error(f"Exa test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_apollo(api_key: str) -> Dict[str, Any]:
    organization_domain = 'microsoft.com'
    url = f'https://api.apollo.io/api/v1/organizations/enrich?domain={organization_domain}'
    logger.debug(f"Making GET request to Apollo for domain: {organization_domain}")
    headers = {"X-Api-Key": api_key}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                if status == 200:
                    await response.json()
                    logger.info("Successfully retrieved organization info from Apollo.")
                    return {"success": True, "status_code": status}

                elif status == 429:
                    msg = "Rate limit exceeded"
                    logger.warning(msg)
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": msg
                    }
                else:
                    err_message = None
                    if response.content_type == "application/json":
                        data = await safe_json(response)
                        err_message = data.get("message") if data else None
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": err_message or f"Non-200 from Apollo: {status}"
                    }
    except Exception as e:
        logger.error(f"Apollo test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_hubspot(api_key: str) -> Dict[str, Any]:
    url = "https://api.hubapi.com/account-info/v3/details"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    err_message = None
                    if data and isinstance(data, dict):
                        err_message = data.get("message") or data.get("error")
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": err_message or f"Non-200 from HubSpot: {status}"
                    }
                if data and "portalId" in data:
                    return {"success": True, "status_code": status, "error_message": None}

                return {
                    "success": False,
                    "status_code": status,
                    "error_message": "Did not find 'portalId' in the response."
                }
    except Exception as e:
        logger.error(f"HubSpot test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_mailgun(api_key: str, domain: str) -> Dict[str, Any]:
    """
    Basic Mailgun connectivity check against the domain-specific stats endpoint.

    Uses BasicAuth("api", api_key) as required by Mailgun. Does not send mail.
    """
    url = f"https://api.mailgun.net/v3/{domain}/stats/total"
    params = {"event": "accepted", "duration": "1d", "limit": 1}
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        auth = aiohttp.BasicAuth("api", api_key)
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with session.get(url, params=params) as response:
                status = response.status
                data = await safe_json(response)
                if status != 200:
                    msg = None
                    if data and isinstance(data, dict):
                        msg = data.get("message") or data.get("error")
                    return {"success": False, "status_code": status, "error_message": msg or f"Mailgun non-200: {status}"}
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"Mailgun test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_sendgrid(api_key: str) -> Dict[str, Any]:
    """
    Basic SendGrid connectivity check via the user account endpoint.

    SendGrid returns 200 with account details when the API key is valid
    and has sufficient scopes.
    """
    url = "https://api.sendgrid.com/v3/user/account"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)
                if status != 200:
                    msg = None
                    if data and isinstance(data, dict):
                        # Typical SendGrid error shape: {"errors":[{"message": ...}]}
                        errs = data.get("errors")
                        if isinstance(errs, list) and errs:
                            first = errs[0]
                            if isinstance(first, dict):
                                msg = first.get("message")
                    return {"success": False, "status_code": status, "error_message": msg or f"SendGrid non-200: {status}"}
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"SendGrid test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_mailreach(api_key: str) -> Dict[str, Any]:
    """
    Basic MailReach connectivity check using the Ping endpoint.
    
    Uses the /v1/ping endpoint to verify API key validity and service availability.
    Reference: https://docs.mailreach.co/reference/getv1ping
    """
    url = "https://api.mailreach.co/api/v1/ping"
    headers = {"x-api-key": api_key}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)
                if status != 200:
                    msg = None
                    if data and isinstance(data, dict):
                        msg = data.get("message") or data.get("error")
                    return {"success": False, "status_code": status, "error_message": msg or f"MailReach non-200: {status}"}
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"MailReach test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_samgov(api_key: str) -> Dict[str, Any]:
    """Test SAM.gov connectivity by fetching a single opportunity."""

    url = "https://api.sam.gov/opportunities/v2/search"
    now = datetime.now(timezone.utc)
    posted_to = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    posted_from = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "limit": 1,
        "offset": 0,
        "keyword": "software",
        "status": "active",
        "includeCount": "true",
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "api_key": api_key,
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:

            async def perform(request_params: Dict[str, Any]):
                async with session.get(url, params=request_params) as response:
                    status = response.status
                    body_text = await response.text()
                    data: Optional[Dict[str, Any]] = None

                    try:
                        parsed = json.loads(body_text)
                        if isinstance(parsed, dict):
                            data = parsed
                    except json.JSONDecodeError:
                        data = None

                    return status, data, body_text

            status, data, body_text = await perform(params)

            def extract_error_message(payload: Optional[Dict[str, Any]], fallback_text: str) -> Optional[str]:
                if not payload:
                    return fallback_text[:200] if fallback_text else None

                errors = payload.get("errors") or payload.get("error")
                if isinstance(errors, list):
                    parts = [
                        err.get("message") if isinstance(err, dict) else str(err)
                        for err in errors
                        if err
                    ]
                    return "; ".join(parts) if parts else fallback_text[:200]
                if isinstance(errors, dict):
                    return errors.get("message") or str(errors)
                if errors:
                    return str(errors)

                for key in ("message", "errorMessage", "detail", "description"):
                    if key in payload and payload[key]:
                        return str(payload[key])

                return fallback_text[:200] if fallback_text else None

            error_message = extract_error_message(data, body_text)

            if status == 400 and error_message and "Invalid Date Entered" in error_message:
                fallback_params = dict(params)
                fallback_params["postedFrom"] = (now - timedelta(days=7)).strftime("%m/%d/%Y")
                fallback_params["postedTo"] = now.strftime("%m/%d/%Y")
                status, data, body_text = await perform(fallback_params)
                error_message = extract_error_message(data, body_text)

            if status != 200:
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": error_message or f"SAM.gov non-200: {status}",
                }

            if not data:
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": "SAM.gov returned invalid JSON response.",
                }

            if data.get("errors"):
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": extract_error_message(data, body_text) or "SAM.gov reported errors.",
                }

            if data.get("opportunitiesData") or data.get("totalRecords") is not None:
                return {"success": True, "status_code": status, "error_message": None}

            return {
                "success": False,
                "status_code": status,
                "error_message": "Unexpected SAM.gov response payload.",
            }

    except Exception as e:
        logger.error(f"SAM.gov test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_salesforce(
    username: str,
    password: str,
    security_token: str,
    domain: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """Test Salesforce connectivity using provided credentials.

    If client_id and client_secret are supplied, perform an OAuth2 password
    grant to obtain an access token and execute a simple REST API call. This is
    suitable for production environments. Otherwise, fall back to the
    simple_salesforce login used for testing.
    """

    try:
        def _connect():
            # OAuth2 password grant flow when client credentials are provided
            if client_id and client_secret:
                token_url = f"https://{domain}.salesforce.com/services/oauth2/token"
                resp = requests.post(
                    token_url,
                    data={
                        "grant_type": "password",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "username": username,
                        "password": f"{password}{security_token}",
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                access_token = data.get("access_token")
                instance_url = data.get("instance_url")
                if not access_token or not instance_url:
                    raise ValueError("Invalid response from Salesforce OAuth2 token endpoint")
                headers = {"Authorization": f"Bearer {access_token}"}
                url = f"{instance_url}/services/data/v59.0/sobjects/Account/"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                return res.json()

            # Default simple_salesforce client for testing/sandbox
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain,
            )
            return sf.query("SELECT Id FROM Account LIMIT 1")

        data = await asyncio.to_thread(_connect)
        if isinstance(data, dict):
            return {"success": True, "status_code": 200, "error_message": None}
        return {
            "success": False,
            "status_code": 200,
            "error_message": "Did not receive records from Salesforce.",
        }
    except Exception as e:
        status = getattr(e, "status", 0)
        logger.error(f"Salesforce test failed: {e}")
        return {"success": False, "status_code": status, "error_message": str(e)}


async def test_github(api_key: str) -> Dict[str, Any]:
    """
    Tests GitHub API connectivity using a Personal Access Token (PAT).
    Performs a GET /user call to verify token validity.
    """
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {api_key}",
        "Accept": "application/vnd.github+json",
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    error_message = data.get("message", f"Non-200 from GitHub: {status}") if data else None
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": error_message
                    }

                if data and "login" in data:
                    return {
                        "success": True,
                        "status_code": status,
                        "error_message": None
                    }
                else:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": "GitHub API responded but 'login' not found."
                    }
    except Exception as e:
        logger.error(f"GitHub connectivity test failed: {e}")
        return {
            "success": False,
            "status_code": 0,
            "error_message": str(e)
        }

###############################################################################
#                UPDATED test_findyemail TO REFLECT ACTUAL USAGE
###############################################################################

async def test_findyemail(api_key: str) -> Dict[str, Any]:
    """
    Tests FindyMail by sending a POST request to /search/name
    with a dummy name+domain, matching the usage in guess_email_with_findymail.
    """
    url = f"{FINDYMAIL_BASE_URL}/search/name"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": "Satya Nadella",
        "domain": "microsoft.com"
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"[FindyMail] Non-200: {status}"
                    }

                # On success, we usually get { "contact": { ... } }
                contact = data.get("contact")
                if not contact:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": "No 'contact' field in response. Possibly invalid API key or insufficient data."
                    }
                # If we got here, assume success
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        logger.error(f"FindyEmail test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}

###############################################################################
#                UPDATED test_hunter TO REFLECT ACTUAL USAGE
###############################################################################

async def test_hunter(api_key: str) -> Dict[str, Any]:
    """
    Tests Hunter by calling their /v2/email-finder endpoint with dummy parameters,
    mirroring guess_email_with_hunter usage.
    """
    # Example dummy usage with domain=example.com, first_name=John, last_name=Doe
    base_url = "https://api.hunter.io/v2/email-finder"
    url = f"{base_url}?domain=microsoft.com&first_name=Satya&last_name=Nadella&api_key={api_key}"

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                status = response.status
                data = await safe_json(response)
                if status != 200:
                    logger.warning("[Hunter] email-finder non‑200: %s", status)
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"Hunter responded with {status}"
                    }

                # On success, check if we got an email in data->"data"->"email"
                email = data.get("data", {}).get("email")
                if not email:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": "No email found in Hunter response. Possibly invalid API key or no data."
                    }
                return {"success": True, "status_code": status, "error_message": None}
    except Exception as ex:
        logger.exception("[Hunter] test exception: %s", ex)
        return {"success": False, "status_code": 0, "error_message": str(ex)}

###############################################################################
#                             CLAY CONNECTIVITY TEST
###############################################################################

async def test_clay(api_key: str, webhook: str) -> Dict[str, Any]:
    """Send a simple payload to the Clay webhook to verify credentials."""
    dummy_lead = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
    }

    try:
        result = await push_to_clay_table(dummy_lead, webhook=webhook, api_key=api_key)
        if isinstance(result, dict) and "error" in result:
            return {
                "success": False,
                "status_code": 0,
                "error_message": result["error"],
            }
        return {"success": True, "status_code": 200, "error_message": None}
    except Exception as exc:  # network or other
        logger.error(f"Clay test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}

###############################################################################
#                            POSTHOG CONNECTIVITY TEST
###############################################################################

async def test_posthog(
    api_host: str,
    project_id: str,
    personal_api_key: str,
) -> Dict[str, Any]:
    """
    Validate PostHog connectivity by issuing a lightweight HogQL query.

    Requires:
      • api_host            (e.g. https://app.posthog.com or self-hosted URL)
      • project_id          (numeric or string project identifier)
      • personal_api_key    (token with query access)
    """
    base_url = (api_host or "").rstrip("/")
    if not base_url:
        return {
            "success": False,
            "status_code": 0,
            "error_message": "Missing api_host for PostHog connectivity test.",
        }
    if not project_id:
        return {
            "success": False,
            "status_code": 0,
            "error_message": "Missing project_id for PostHog connectivity test.",
        }
    if not personal_api_key:
        return {
            "success": False,
            "status_code": 0,
            "error_message": "Missing personal_api_key for PostHog connectivity test.",
        }

    url = f"{base_url}/api/projects/{project_id}/query/"
    headers = {
        "Authorization": f"Bearer {personal_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"query": {"kind": "HogQLQuery", "query": "SELECT 1"}}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    return {"success": True, "status_code": status, "error_message": None}

                detail = None
                if isinstance(data, dict):
                    detail = (
                        data.get("message")
                        or data.get("detail")
                        or data.get("error")
                        or data.get("code")
                    )
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": detail or f"PostHog responded with {status}",
                }
    except Exception as exc:
        logger.error(f"PostHog connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}

###############################################################################
#                          MCP SERVER CONNECTIVITY TEST
###############################################################################

async def test_mcp_server(
    base_url: str,
    server_label: str = "",
    header_name: str = "",
    header_value: str = ""
) -> Dict[str, Any]:
    """Simple connectivity check for an MCP server using the OpenAI client."""

    if AsyncOpenAI is None:
        return {
            "success": False,
            "status_code": 0,
            "error_message": "openai package not installed",
        }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "status_code": 0,
            "error_message": "OPENAI_API_KEY environment variable not set",
        }

    headers: Dict[str, str] = (
        {header_name: header_value} if header_name and header_value else {}
    )

    tools = [
        {
            "type": "mcp",
            "server_label": server_label,
            "server_url": base_url,
            "require_approval": "never",
            "headers": headers,
        }
    ]

    try:
        client = AsyncOpenAI(api_key=api_key)
        
        kwargs: Dict[str, Any] = {
            "input": [
                {"role": "user", "content": "list tools available"},
            ],
            "model": "gpt-4",
            "store": False,
            "tools": tools,
            "tool_choice": "required",
        }
        
        response = await client.responses.create(**kwargs)
        
        # Convert response to dict-like structure for compatibility
        status = 200  # Successful response creation
        data = response.model_dump() if hasattr(response, 'model_dump') else None

        if data and data.get("error"):
            detail = data["error"].get("message") if isinstance(data["error"], dict) else str(data["error"])
            return {"success": False, "status_code": status, "error_message": detail}

        return {"success": True, "status_code": status, "error_message": None}
    except Exception as e:
        return {"success": False, "status_code": 0, "error_message": str(e)}
    
    
###############################################################################
#                   SMTP / IMAP CONNECTIVITY TEST FUNCTION
###############################################################################

async def test_smtp_accounts(
    usernames: str,
    passwords: str,
    smtp_host: str,
    smtp_port: int,
    imap_host: str,
    imap_port: int,
) -> Dict[str, Any]:
    """
    Quick “smoke test” for an SMTP + IMAP mailbox configuration.

    Parameters
    ----------
    usernames : str
        Comma-separated list of mailbox usernames.
    passwords : str
        Comma-separated list of passwords or app-passwords, **same order** as *usernames*.
    smtp_host : str
        SMTP server hostname (e.g. ``smtp.gmail.com``).
    smtp_port : int
        SMTP port (587 for STARTTLS, 465 for implicit SSL, etc.).
    imap_host : str
        IMAP server hostname (e.g. ``imap.gmail.com``).
    imap_port : int
        IMAP SSL port (usually 993).

    Returns
    -------
    dict
        {
          "success": bool,
          "status_code": int,          # 250 for SMTP OK, or last IMAP status-code on error
          "error_message": Optional[str]
        }
    """
    users: List[str] = [u.strip() for u in usernames.split(",") if u.strip()]
    pwds:  List[str] = [p.strip() for p in passwords.split(",") if p.strip()]

    if not users or len(users) != len(pwds):
        return {
            "success": False,
            "status_code": 0,
            "error_message": "Username / password list mismatch or empty."
        }

    # --- use the first account for the connectivity check ---
    user, pwd = users[0], pwds[0]

    # 1)  SMTP LOGIN ----------------------------------------------------------
    try:
        smtp_kwargs = dict(hostname=smtp_host, port=smtp_port, timeout=10)
        if smtp_port == 587:
            smtp_kwargs["start_tls"] = True  # STARTTLS upgrade
        else:
            smtp_kwargs["tls"] = (smtp_port == 465)  # implicit SSL on 465

        smtp = aiosmtplib.SMTP(**smtp_kwargs)
        await smtp.connect()

        code, _msg = await smtp.login(user, pwd)
        await smtp.quit()

        if code not in (235, 250):  # 235 = Auth OK, 250 = generic OK
            return {
                "success": False,
                "status_code": code,
                "error_message": f"SMTP login failed with code {code}"
            }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "error_message": f"SMTP error: {e}"
        }

    # 2)  IMAP LOGIN ----------------------------------------------------------
    try:
        conn = imaplib.IMAP4_SSL(imap_host, imap_port)  # SSL always for 993
        status, _ = conn.login(user, pwd)
        conn.logout()

        if status != "OK":
            return {
                "success": False,
                "status_code": 0,
                "error_message": f"IMAP login failed: {status}"
            }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "error_message": f"IMAP error: {e}"
        }

    # ------------------------------------------------------------------------
    return {
        "success": True,
        "status_code": 250,  # canonical “OK” code for SMTP success
        "error_message": None
    }

async def test_slack(webhook_url: str) -> Dict[str, Any]:
    """
    Sends a test JSON payload to the provided Slack Webhook URL.
    Slack typically returns a 200 status with 'ok' in the body if successful.
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            payload = {"text": "Hello from Dhisana connectivity test!"}
            async with session.post(webhook_url, json=payload) as response:
                status = response.status
                text_response = await response.text()

                if status != 200:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"Slack webhook returned non-200 status: {status}"
                    }

                # Slack returns "ok" if the message was posted successfully
                if text_response.strip().lower() != "ok":
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"Unexpected Slack response: {text_response}"
                    }

                return {"success": True, "status_code": status, "error_message": None}

    except Exception as e:
        logger.error(f"Slack connectivity test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


async def test_jinaai(api_key: str) -> Dict[str, Any]:
    """Simple connectivity test for the Jina AI API."""
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jina-embeddings-v2-base-en",
        "input": ["ping"]
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    message = data.get("message") if isinstance(data, dict) else None
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": message or f"Non-200 from Jina AI: {status}",
                    }

                if data and "error" in data:
                    err = data["error"]
                    if isinstance(err, dict):
                        err = err.get("message", str(err))
                    return {"success": False, "status_code": status, "error_message": err}

                return {"success": True, "status_code": status, "error_message": None}
    except Exception as exc:
        logger.error(f"Jina AI connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_firefliesai(api_key: str) -> Dict[str, Any]:
    """Validate Fireflies.ai API key by querying user metadata via GraphQL."""
    url = "https://api.fireflies.ai/graphql"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Try a couple of documented/observed query shapes — Fireflies occasionally
    # aliases the viewer field, so we fall back if the first choice is rejected.
    queries = [
        ("users", {"query": "{ users { name user_id } }"}, ("data", "users")),
        ("viewer", {"query": "query { viewer { id email } }"}, ("data", "viewer")),
        ("me", {"query": "query { me { id email } }"}, ("data", "me")),
        ("currentUser", {"query": "query { currentUser { id email } }"}, ("data", "currentUser")),
    ]

    def extract_error(payload: Optional[Dict[str, Any]]) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        errors = payload.get("errors")
        if isinstance(errors, list):
            messages = [
                err.get("message") for err in errors
                if isinstance(err, dict) and err.get("message")
            ]
            if messages:
                return "; ".join(messages)
        elif errors:
            return str(errors)
        return (
            payload.get("message")
            or payload.get("error_description")
            or payload.get("error")
        )

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            last_error: Optional[str] = None

            for query_name, payload, data_path in queries:
                async with session.post(url, headers=headers, json=payload) as response:
                    status = response.status
                    data = await safe_json(response)

                    if status != 200:
                        error_message = extract_error(data)
                        if (
                            error_message
                            and "Cannot query field" in error_message
                            and query_name != queries[-1][0]
                        ):
                            last_error = error_message
                            continue
                        return {
                            "success": False,
                            "status_code": status,
                            "error_message": error_message or f"Non-200 from Fireflies.ai ({query_name})",
                        }

                    if not isinstance(data, dict):
                        return {
                            "success": False,
                            "status_code": status,
                            "error_message": "Fireflies.ai returned non-JSON response.",
                        }

                    error_message = extract_error(data)
                    if error_message:
                        last_error = error_message
                        # If the error indicates the field is unknown, try the next query option.
                        if "Cannot query field" in error_message and query_name != queries[-1][0]:
                            continue
                        return {
                            "success": False,
                            "status_code": status,
                            "error_message": error_message,
                        }

                    # Walk the data path to ensure the expected field exists.
                    cursor: Any = data
                    for key in data_path:
                        if not isinstance(cursor, dict):
                            cursor = None
                            break
                        cursor = cursor.get(key)

                    if cursor is not None:
                        return {"success": True, "status_code": status, "error_message": None}

                    last_error = f"Fireflies.ai {query_name} response missing expected fields."

            return {
                "success": False,
                "status_code": 200,
                "error_message": last_error or "Fireflies.ai queries did not return user data.",
            }
    except Exception as exc:
        logger.error(f"Fireflies.ai connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_firecrawl(api_key: str) -> Dict[str, Any]:
    """Quick check for Firecrawl API key validity (official v1 endpoint)."""
    url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {api_key}",  # per Firecrawl v1 docs
        "Content-Type": "application/json",
    }
    payload = {"url": "https://example.com"}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    message = data.get("message") if isinstance(data, dict) else None
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": message or f"Non-200 from Firecrawl: {status}",
                    }

                if data and "error" in data:
                    err = data["error"]
                    if isinstance(err, dict):
                        err = err.get("message", str(err))
                    return {"success": False, "status_code": status, "error_message": err}

                return {"success": True, "status_code": status, "error_message": None}
    except Exception as exc:
        logger.error(f"Firecrawl connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_scraperapi(api_key: str) -> Dict[str, Any]:
    """Connectivity check for ScraperAPI using a simple NYTimes scrape."""
    url = "https://api.scraperapi.com/"
    params = {
        "api_key": api_key,
        "url": "https://example.com/",  # lightweight public page to minimize credit usage
        "output_format": "markdown",
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, params=params) as response:
                status = response.status
                body_text = await response.text()

                if status != 200:
                    snippet = body_text[:200] if body_text else None
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": snippet or f"Non-200 from ScraperAPI: {status}",
                    }

                if not body_text:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": "ScraperAPI returned an empty response.",
                    }

                return {"success": True, "status_code": status, "error_message": None}
    except Exception as exc:
        logger.error(f"ScraperAPI connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_youtube(api_key: str) -> Dict[str, Any]:
    """
    Tests YouTube Data API v3 by making a simple search request.
    Uses a basic search query that works with API key authentication only.
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "test",
        "type": "video",
        "maxResults": 1,
        "key": api_key
    }
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, params=params) as response:
                status = response.status
                
                # Get response text first for debugging
                response_text = await response.text()
                logger.debug(f"YouTube API response status: {status}, text: {response_text[:500]}")
                
                # Try to parse as JSON
                data = None
                try:
                    data = json.loads(response_text) if response_text else None
                except json.JSONDecodeError:
                    logger.warning(f"YouTube API returned non-JSON response: {response_text[:200]}")

                if status != 200:
                    error_message = None
                    if data and isinstance(data, dict):
                        error = data.get("error", {})
                        if isinstance(error, dict):
                            error_message = error.get("message")
                        else:
                            error_message = str(error)
                    
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": error_message or f"Non-200 from YouTube API: {status}. Response: {response_text[:200]}"
                    }

                # Handle case where we got 200 but no valid JSON data
                if not data:
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"YouTube API returned empty or invalid JSON response: {response_text[:200]}"
                    }

                # Check for API errors in 200 response
                if "error" in data:
                    error = data["error"]
                    error_message = error.get("message") if isinstance(error, dict) else str(error)
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": f"YouTube API error: {error_message}"
                    }

                # Check if we got valid response structure
                if "kind" in data and data["kind"] == "youtube#searchListResponse":
                    return {"success": True, "status_code": status, "error_message": None}
                
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": f"Invalid response format from YouTube API. Expected 'youtube#searchListResponse', got: {data.get('kind', 'unknown')}"
                }

    except Exception as exc:
        logger.error(f"YouTube API connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_orum(api_key: str) -> Dict[str, Any]:
    """
    Validate an Orum API key by calling a lightweight authenticated endpoint.

    The base URL can be overridden with ORUM_API_BASE_URL if needed.
    """
    base_url = os.getenv("ORUM_API_BASE_URL", "https://api.orum.com")
    url = f"{base_url.rstrip('/')}/api/v1/users/me"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    return {"success": True, "status_code": status, "error_message": None}

                message = None
                if isinstance(data, dict):
                    message = data.get("message") or data.get("error") or data.get("detail")
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"Orum responded with {status}",
                }
    except Exception as exc:
        logger.error(f"Orum connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_aircall(app_id: str, api_token: str) -> Dict[str, Any]:
    """
    Validate Aircall credentials via a lightweight authenticated call.
    Uses HTTP Basic Auth (app_id:api_token).
    """
    url = "https://api.aircall.io/v1/users"
    params = {"per_page": 1}

    try:
        auth = aiohttp.BasicAuth(app_id, api_token)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), auth=auth) as session:
            async with session.get(url, params=params) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200 and isinstance(data, dict) and "users" in data:
                    return {"success": True, "status_code": status, "error_message": None}

                message = None
                if isinstance(data, dict):
                    message = data.get("message") or data.get("error")
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"Aircall responded with {status}",
                }
    except Exception as exc:
        logger.error(f"Aircall connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_ringover(api_key: str) -> Dict[str, Any]:
    """
    Validate Ringover API key using a minimal authenticated request.
    """
    base_url = os.getenv("RINGOVER_API_BASE_URL", "https://public-api.ringover.com")
    url = f"{base_url.rstrip('/')}/v2/users"
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }
    params = {"limit": 1}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers, params=params) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    return {"success": True, "status_code": status, "error_message": None}

                message = None
                if isinstance(data, dict):
                    message = data.get("message") or data.get("error") or data.get("detail")
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"Ringover responded with {status}",
                }
    except Exception as exc:
        logger.error(f"Ringover connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_dialpad(client_id: str, client_secret: str) -> Dict[str, Any]:
    """
    Validate Dialpad client credentials via client_credentials token exchange, then whoami.
    """
    base_url = os.getenv("DIALPAD_API_BASE_URL", "https://dialpad.com")
    token_url = f"{base_url.rstrip('/')}/oauth/token"
    whoami_url = f"{base_url.rstrip('/')}/api/v2/whoami"

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            token_resp = await session.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Accept": "application/json"},
            )
            token_status = token_resp.status
            token_data = await safe_json(token_resp)

            access_token = None
            if isinstance(token_data, dict):
                access_token = token_data.get("access_token")

            if token_status != 200 or not access_token:
                message = None
                if isinstance(token_data, dict):
                    message = token_data.get("error_description") or token_data.get("error")
                return {
                    "success": False,
                    "status_code": token_status,
                    "error_message": message or "Failed to obtain Dialpad access token.",
                }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
            async with session.get(whoami_url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    return {"success": True, "status_code": status, "error_message": None}

                message = None
                if isinstance(data, dict):
                    message = data.get("message") or data.get("error") or data.get("detail")
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"Dialpad responded with {status}",
                }
    except Exception as exc:
        logger.error(f"Dialpad connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_nooks(api_key: str) -> Dict[str, Any]:
    """
    Validate Nooks.ai API key via a simple authenticated call.
    """
    base_url = os.getenv("NOOKS_API_BASE_URL", "https://api.nooks.ai")
    url = f"{base_url.rstrip('/')}/v1/users/me"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    return {"success": True, "status_code": status, "error_message": None}

                message = None
                if isinstance(data, dict):
                    message = data.get("message") or data.get("error") or data.get("detail")
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"Nooks.ai responded with {status}",
                }
    except Exception as exc:
        logger.error(f"Nooks.ai connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_commonroom(api_key: str) -> Dict[str, Any]:
    """Validate a Common Room API token via the token status endpoint."""
    url = "https://api.commonroom.io/community/v1/api-token-status"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    return {"success": True, "status_code": status, "error_message": None}

                message = None
                if isinstance(data, dict):
                    message = (
                        data.get("message")
                        or data.get("reason")
                        or data.get("error")
                        or data.get("docs")
                    )
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"Common Room responded with {status}",
                }
    except Exception as exc:
        logger.error(f"Common Room connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_scarf(api_key: str) -> Dict[str, Any]:
    """
    Validate a Scarf API token via the lightweight /v2/search endpoint.

    The endpoint requires only the bearer token and a simple query string.
    """
    url = "https://api.scarf.sh/v2/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"query": "dhisana connectivity test"}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                data = await safe_json(response)

                if status != 200:
                    message = None
                    if isinstance(data, dict):
                        message = data.get("message") or data.get("error") or data.get("detail")
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": message or f"Scarf responded with {status}",
                    }

                if isinstance(data, dict) and "results" in data:
                    return {"success": True, "status_code": status, "error_message": None}

                return {
                    "success": False,
                    "status_code": status,
                    "error_message": "Unexpected Scarf response payload.",
                }
    except Exception as exc:
        logger.error(f"Scarf connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


async def test_theorg(api_key: str) -> Dict[str, Any]:
    """Validate The Org API key by calling the Usage endpoint."""
    url = "https://api.theorg.com/v1.1/usage"
    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await safe_json(response)

                if status == 200:
                    payload = data if isinstance(data, dict) else None
                    usage = payload.get("data") if payload else None
                    if isinstance(usage, dict):
                        return {"success": True, "status_code": status, "error_message": None}
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": "The Org usage endpoint returned an unexpected payload.",
                    }

                message = None
                if isinstance(data, dict):
                    message = (
                        data.get("message")
                        or data.get("error")
                        or data.get("detail")
                    )
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": message or f"The Org responded with {status}",
                }
    except Exception as exc:
        logger.error(f"The Org connectivity test failed: {exc}")
        return {"success": False, "status_code": 0, "error_message": str(exc)}


###############################################################################
#                            CORESIGNAL CONNECTIVITY
###############################################################################

async def test_coresignal(api_key: str) -> Dict[str, Any]:
    """
    Connectivity test for Coresignal using the Multi-source Jobs API search preview.

    Uses a lightweight search query to verify API key validity.
    Reference: https://docs.coresignal.com/jobs-api/multi-source-jobs-api/search-preview
    """
    url = "https://api.coresignal.com/cdapi/v2/job_multi_source/search/es_dsl/preview"
    headers = {
        "apikey": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    # Minimal query to check connectivity
    payload = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "title": "software engineer"
                        }
                    }
                ]
            }
        }
    }

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                status = resp.status
                data = await safe_json(resp)

                if status == 200:
                    # Check if we got a valid response (list of job results or empty list)
                    if isinstance(data, list):
                        return {"success": True, "status_code": status, "error_message": None}
                    # Some endpoints may return a dict with results
                    if isinstance(data, dict):
                        if "error" in data or "errors" in data:
                            err = data.get("error") or data.get("errors")
                            if isinstance(err, dict):
                                err = err.get("message") or str(err)
                            return {"success": False, "status_code": status, "error_message": str(err)}
                        return {"success": True, "status_code": status, "error_message": None}
                    return {"success": True, "status_code": status, "error_message": None}

                if status in (401, 403):
                    msg = None
                    if isinstance(data, dict):
                        msg = data.get("message") or data.get("error") or data.get("detail")
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": msg or "Unauthorized – check Coresignal API key",
                    }

                msg = None
                if isinstance(data, dict):
                    msg = data.get("message") or data.get("error") or data.get("detail")
                return {
                    "success": False,
                    "status_code": status,
                    "error_message": msg or f"Coresignal responded with {status}",
                }
    except Exception as e:
        logger.error(f"Coresignal connectivity test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


###############################################################################
#                              DATAGMA CONNECTIVITY
###############################################################################

async def test_datagma(api_key: str) -> Dict[str, Any]:
    """
    Connectivity test for Datagma using the documented Get Credit endpoint
    with query param authentication.

    Endpoint: GET https://gateway.datagma.net/api/ingress/v1/mine?apiId=<KEY>
    """
    base_url = "https://gateway.datagma.net/api/ingress/v1/mine"
    url = f"{base_url}?apiId={api_key}"

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                status = resp.status
                data = await safe_json(resp)

                if status == 200:
                    if isinstance(data, dict) and ("error" in data or "errors" in data):
                        err = data.get("error") or data.get("errors")
                        if isinstance(err, dict):
                            err = err.get("message") or str(err)
                        return {"success": False, "status_code": status, "error_message": str(err)}
                    return {"success": True, "status_code": status, "error_message": None}

                if status in (401, 403):
                    msg = None
                    if isinstance(data, dict):
                        msg = data.get("message") or data.get("error")
                    return {
                        "success": False,
                        "status_code": status,
                        "error_message": msg or "Unauthorized – check Datagma API key",
                    }

                return {
                    "success": False,
                    "status_code": status,
                    "error_message": f"Datagma responded with {status}",
                }
    except Exception as e:
        logger.error(f"Datagma connectivity test failed: {e}")
        return {"success": False, "status_code": 0, "error_message": str(e)}


###############################################################################
#                         MAIN CONNECTIVITY FUNCTION
###############################################################################

async def test_connectivity(tool_config: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Checks connectivity for multiple tools and returns a dictionary
    with the result for each.

    Special-cases:
      • 'openai'           – needs modelName & reasoningEffort
      • 'googleworkspace'  – needs subjectEmail
      • 'googledrive'      – needs subjectEmail
      • 'smtpEmail'        – has *no* apiKey; instead requires usernames,
                             passwords, smtp/imap hosts & ports
    """
    # Updated test_mapping with the revised test_* functions
    test_mapping: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {
        "zerobounce":       test_zerobounce,
        "openai":           test_openai,
        "googleworkspace":  test_google_workspace,
        "googledrive":      test_google_drive,
        "serpapi":          test_serpapi,
        "serperdev":        test_serperdev,
        "proxycurl":        test_proxycurl,
        "exa":             test_exa,
        "apollo":           test_apollo,
        "hubspot":          test_hubspot,
        "github":           test_github,
        "smtpEmail":        test_smtp_accounts,
        "hunter":           test_hunter,
        "findymail":        test_findyemail,
        "datagma":          test_datagma,
        "jinaai":           test_jinaai,
        "firefliesai":      test_firefliesai,
        "firecrawl":        test_firecrawl,
        "youtube":          test_youtube,
        "orum":             test_orum,
        "aircall":          test_aircall,   # handled specially to pass appId + apiToken
        "ringover":         test_ringover,
        "dialpad":          test_dialpad,   # handled specially to pass client credentials
        "nooks":            test_nooks,
        "commonRoom":       test_commonroom,
        "scarf":            test_scarf,
        "theorg":           test_theorg,
        "coresignal":       test_coresignal,
        "salesforce":       test_salesforce,
        "clay":             test_clay,
        "posthog":          test_posthog,
        "mcpServer":        test_mcp_server,
        "slack":            test_slack,
        "mailgun":          test_mailgun,
        "mailreach":        test_mailreach,
        "sendgrid":         test_sendgrid,
        "samgov":          test_samgov,
        "scraperapi":       test_scraperapi,
    }

    results: Dict[str, Dict[str, Any]] = {}

    for tool in tool_config:
        tool_name: str = tool.get("name", "")
        config_entries: List[Dict[str, Any]] = tool.get("configuration", [])

        if not tool_name:
            logger.warning("Tool entry missing 'name' field.")
            results.setdefault("unknown_tool", {
                "success": False,
                "status_code": 0,
                "error_message": "Tool entry missing 'name'."
            })
            continue

        if tool_name not in test_mapping:
            logger.warning(f"No test function found for tool: {tool_name}")
            results[tool_name] = {
                "success": False,
                "status_code": 0,
                "error_message": f"No test function for tool '{tool_name}'."
            }
            continue

        # ------------------------------------------------------------------ #
        # Special-case: SMTP / IMAP connectivity (no apiKey)
        # ------------------------------------------------------------------ #
        if tool_name == "smtpEmail":
            def _get(name: str, default: Any = None):
                return next((c["value"] for c in config_entries if c["name"] == name), default)

            usernames   = _get("usernames", "")
            passwords   = _get("passwords", "")
            smtp_host   = _get("smtpEndpoint", "smtp.gmail.com")
            smtp_port   = int(_get("smtpPort", 587))
            imap_host   = _get("imapEndpoint", "imap.gmail.com")
            imap_port   = int(_get("imapPort", 993))

            if not usernames or not passwords:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing usernames or passwords."
                }
            else:
                logger.info("Testing connectivity for smtpEmail…")
                results[tool_name] = await test_smtp_accounts(
                    usernames,
                    passwords,
                    smtp_host,
                    smtp_port,
                    imap_host,
                    imap_port,
                )
            continue  # handled – move to next tool

        # ------------------------------------------------------------------ #
        # Special-case: MCP server (headers instead of apiKey)
        # ------------------------------------------------------------------ #
        if tool_name == "mcpServer":
            server_url = next((c["value"] for c in config_entries if c["name"] == "serverUrl"), "")
            server_label = next((c["value"] for c in config_entries if c["name"] == "serverLabel"), "")
            header_name = next((c["value"] for c in config_entries if c["name"] == "apiKeyHeaderName"), "")
            header_value = next((c["value"] for c in config_entries if c["name"] == "apiKeyHeaderValue"), "")
            if not server_url or not header_name or not header_value:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing serverUrl or API key header info.",
                }
            else:
                logger.info("Testing connectivity for mcpServer…")
                results[tool_name] = await test_mcp_server(server_url, server_label, header_name, header_value)
            continue

        # ------------------------------------------------------------------ #
        # Special-case: Slack (webhookUrl instead of an apiKey)
        # ------------------------------------------------------------------ #
        if tool_name == "slack":
            webhook_url = next(
                (c["value"] for c in config_entries if c["name"] == "webhookUrl"),
                None
            )
            if not webhook_url:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing 'webhookUrl' for Slack."
                }
            else:
                logger.info("Testing connectivity for Slack…")
                results[tool_name] = await test_slack(webhook_url)
            continue

        # ------------------------------------------------------------------ #
        # Special-case: Mailgun (needs notifyDomain in addition to apiKey)
        # ------------------------------------------------------------------ #
        if tool_name == "mailgun":
            api_key = next((c["value"] for c in config_entries if c["name"] == "apiKey"), None)
            # Prefer new field name 'domain', fall back to legacy 'notifyDomain'
            domain  = next((c["value"] for c in config_entries if c["name"] == "domain"), None)
            if not domain:
                domain = next((c["value"] for c in config_entries if c["name"] == "notifyDomain"), None)
            if not api_key or not domain:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing apiKey or domain for Mailgun.",
                }
            else:
                logger.info("Testing connectivity for Mailgun…")
                results[tool_name] = await test_mailgun(api_key, domain)
            continue

        # ------------------------------------------------------------------ #
        # Special-case: PostHog (needs host + project id + personal API key)
        # ------------------------------------------------------------------ #
        if tool_name == "posthog":
            api_host = next((c["value"] for c in config_entries if c["name"] == "api_host"), None)
            project_id = next((c["value"] for c in config_entries if c["name"] == "project_id"), None)
            personal_api_key = next(
                (c["value"] for c in config_entries if c["name"] in ("personal_api_key", "personalApiKey")),
                None,
            )

            if not api_host or not project_id or not personal_api_key:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing api_host, project_id, or personal_api_key for PostHog.",
                }
            else:
                logger.info("Testing connectivity for PostHog…")
                results[tool_name] = await test_posthog(api_host, project_id, personal_api_key)
            continue

        # ------------------------------------------------------------------ #
        # Special-case: Salesforce (requires credentials)
        # ------------------------------------------------------------------ #
        if tool_name == "salesforce":
            cfg_map = {c.get("name"): c.get("value") for c in config_entries if c}
            username = cfg_map.get("username")
            password = cfg_map.get("password")
            security_token = cfg_map.get("security_token")
            domain = cfg_map.get("domain", "login")
            client_id = cfg_map.get("client_id")
            client_secret = cfg_map.get("client_secret")

            if not all([username, password, security_token]):
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing Salesforce credentials.",
                }
            else:
                logger.info("Testing connectivity for salesforce…")
                results[tool_name] = await test_salesforce(
                    username,
                    password,
                    security_token,
                    domain,
                    client_id,
                    client_secret,
                )
            continue

        # ------------------------------------------------------------------ #
        # Special-case: Aircall (app_id + api_token)
        # ------------------------------------------------------------------ #
        if tool_name == "aircall":
            app_id = next((c["value"] for c in config_entries if c["name"] == "apiId"), None)
            api_token = next((c["value"] for c in config_entries if c["name"] == "apiToken"), None)
            if not app_id or not api_token:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing apiId or apiToken for Aircall.",
                }
            else:
                logger.info("Testing connectivity for Aircall…")
                results[tool_name] = await test_aircall(app_id, api_token)
            continue

        # ------------------------------------------------------------------ #
        # Special-case: Dialpad (client credentials)
        # ------------------------------------------------------------------ #
        if tool_name == "dialpad":
            client_id = next((c["value"] for c in config_entries if c["name"] == "clientId"), None)
            client_secret = next((c["value"] for c in config_entries if c["name"] == "clientSecret"), None)
            if not client_id or not client_secret:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing clientId or clientSecret for Dialpad.",
                }
            else:
                logger.info("Testing connectivity for Dialpad…")
                results[tool_name] = await test_dialpad(client_id, client_secret)
            continue

        # ------------------------------------------------------------------ #
        # All other tools – expect an apiKey by default
        # ------------------------------------------------------------------ #
        api_key = next((c["value"] for c in config_entries if c["name"] == "apiKey"), None)
        if not api_key:
            logger.warning(f"Tool '{tool_name}' missing 'apiKey' in configuration.")
            results[tool_name] = {
                "success": False,
                "status_code": 0,
                "error_message": "Missing apiKey."
            }
            continue

        logger.info(f"Testing connectivity for {tool_name}…")

        # OpenAI needs extra args
        if tool_name == "openai":
            model_name = next((c["value"] for c in config_entries if c["name"] == "modelName"), "gpt-5.1-chat")
            reasoning_effort = next((c["value"] for c in config_entries if c["name"] == "reasoningEffort"), "medium")
            results[tool_name] = await test_openai(api_key, model_name, reasoning_effort)

        # Google Workspace needs subjectEmail
        elif tool_name == "googleworkspace":
            subject_email = next((c["value"] for c in config_entries if c["name"] == "subjectEmail"), "")
            if not subject_email:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing subjectEmail for Google Workspace."
                }
            else:
                results[tool_name] = await test_google_workspace(api_key, subject_email)

        # Google Drive also needs subjectEmail
        elif tool_name == "googledrive":
            subject_email = next((c["value"] for c in config_entries if c["name"] == "subjectEmail"), "")
            if not subject_email:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing subjectEmail for Google Drive.",
                }
            else:
                results[tool_name] = await test_google_drive(api_key, subject_email)

        # Clay needs webhook URL in addition to apiKey
        elif tool_name == "clay":
            webhook = next(
                (c["value"] for c in config_entries if c["name"] in ("webhook", "webhookUrl", "webhook_url")),
                None,
            )
            if not webhook:
                results[tool_name] = {
                    "success": False,
                    "status_code": 0,
                    "error_message": "Missing webhook URL for Clay.",
                }
            else:
                results[tool_name] = await test_clay(api_key, webhook)

        # Everything else calls the mapped test function with just api_key
        else:
            results[tool_name] = await test_mapping[tool_name](api_key)

    return results
