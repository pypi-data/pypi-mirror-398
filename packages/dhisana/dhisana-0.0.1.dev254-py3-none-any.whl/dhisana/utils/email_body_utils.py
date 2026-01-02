"""Small helpers for handling e-mail bodies across providers."""

from typing import Optional, Tuple
import html as html_lib
import re


def looks_like_html(text: str) -> bool:
    """Heuristically determine whether the body contains HTML markup."""
    return bool(text and re.search(r"<[a-zA-Z][^>]*>", text))


def _normalize_format_hint(format_hint: Optional[str]) -> str:
    """
    Normalize a user-supplied format hint into html/text/auto.

    Accepts variations like "plain" or "plaintext" as text.
    """
    if not format_hint:
        return "auto"
    fmt_raw = getattr(format_hint, "value", format_hint)
    fmt = str(fmt_raw).strip().lower()
    if fmt in ("html",):
        return "html"
    if fmt in ("text", "plain", "plain_text", "plaintext"):
        return "text"
    return "auto"


def html_to_plain_text(html: str) -> str:
    """
    Produce a very lightweight plain-text version of an HTML fragment.
    This keeps newlines on block boundaries and strips tags.
    """
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|h[1-6])\s*>", "\n", text)
    text = re.sub(r"(?is)<.*?>", "", text)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def plain_text_to_html(text: str) -> str:
    """Wrap plain text in a minimal HTML container that preserves newlines."""
    if text is None:
        return ""
    escaped = html_lib.escape(text)
    return f'<div style="white-space: pre-wrap">{escaped}</div>'


def body_variants(body: Optional[str], format_hint: Optional[str]) -> Tuple[str, str, str]:
    """
    Return (plain, html, resolved_format) honoring an optional format hint.

    resolved_format is "html" or "text" after applying auto-detection.
    """
    content = body or ""
    fmt = _normalize_format_hint(format_hint)

    if fmt == "html":
        return html_to_plain_text(content), content, "html"
    if fmt == "text":
        return content, plain_text_to_html(content), "text"

    if looks_like_html(content):
        return html_to_plain_text(content), content, "html"

    return content, plain_text_to_html(content), "text"
