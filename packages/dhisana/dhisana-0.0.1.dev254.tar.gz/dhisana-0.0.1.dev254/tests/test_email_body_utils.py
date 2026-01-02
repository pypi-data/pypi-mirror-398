import pytest

from dhisana.schemas.common import BodyFormat
from dhisana.utils.email_body_utils import body_variants


@pytest.mark.parametrize(
    "body,format_hint,expected_resolved",
    [
        ("<p>Hello</p>", BodyFormat.HTML, "html"),
        ("Hello", BodyFormat.TEXT, "text"),
    ],
)
def test_body_variants_honors_body_format_enum(body, format_hint, expected_resolved):
    plain, html, resolved = body_variants(body, format_hint)

    if expected_resolved == "html":
        assert html == body
        assert plain == "Hello"
    else:
        assert plain == body
        assert html.startswith("<div")
    assert resolved == expected_resolved
