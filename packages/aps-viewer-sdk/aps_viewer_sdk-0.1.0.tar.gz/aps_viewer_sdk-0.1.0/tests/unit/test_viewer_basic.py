"""Unit tests for APSViewer that don't require API credentials."""

import webbrowser
from pathlib import Path

from aps_viewer_sdk import APSViewer
from aps_viewer_sdk.helper import to_md_urn


def test_viewer_initialization() -> None:
    """Test that APSViewer can be initialized with basic parameters."""
    viewer = APSViewer(
        urn="test-urn-12345",
        token="test-token",
        views_selector=False,
    )

    assert viewer.urn == "test-urn-12345"
    assert viewer.token == "test-token"
    assert viewer.views_selector is False


def test_viewer_write_returns_html() -> None:
    """Test that viewer.write() generates HTML content."""
    viewer = APSViewer(
        urn="test-urn-12345",
        token="test-token",
        views_selector=False,
    )

    html = viewer.write()

    assert isinstance(html, str)
    assert len(html) > 0
    assert "test-token" in html
    assert to_md_urn("test-urn-12345") in html


def test_viewer_show_creates_html_file(monkeypatch) -> None:
    """Test that viewer.show() creates an HTML file and attempts to open it."""
    viewer = APSViewer(
        urn="test-urn-12345",
        token="test-token",
        views_selector=False,
    )

    opened: dict[str, str] = {}

    def fake_open(url: str) -> bool:
        opened["url"] = url
        return True

    monkeypatch.setattr(webbrowser, "open", fake_open)

    viewer.show()

    assert "url" in opened
    assert opened["url"].startswith("file://")

    html_path = Path(opened["url"][7:])
    assert html_path.exists()

    html = html_path.read_text(encoding="utf-8")
    assert "test-token" in html
    assert f"urn:{to_md_urn(viewer.urn)}" in html


def test_to_md_urn_conversion() -> None:
    """Test URN to base64 conversion."""
    test_urn = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6bXlidWNrZXQvbXlmaWxlLnJ2dA"
    result = to_md_urn(test_urn)

    assert isinstance(result, str)
    assert len(result) > 0
