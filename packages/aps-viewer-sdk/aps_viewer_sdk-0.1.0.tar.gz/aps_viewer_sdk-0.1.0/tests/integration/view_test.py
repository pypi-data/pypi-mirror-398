import pytest
import os
import random
import webbrowser

from typing import cast
from pathlib import Path
from dotenv import load_dotenv
from aps_viewer_sdk import APSViewer, ElementsInScene
from aps_viewer_sdk.helper import (
    to_md_urn,
    get_2lo_token,
    get_metadata_viewables,
    get_all_model_properties,
)


@pytest.mark.requires_secrets
def test_show_opens_html_in_browser(monkeypatch) -> None:
    load_dotenv()
    test_urn = os.getenv("TEST_URN")
    if not test_urn:
        pytest.skip("Missing TEST_URN for browser launch test")

    viewer = APSViewer(
        urn=test_urn,
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
    html = html_path.read_text(encoding="utf-8")

    assert "test-token" in html
    assert f"urn:{to_md_urn(viewer.urn)}" in html


@pytest.mark.requires_secrets
def test_view_names_are_injected_into_html() -> None:
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    test_urn = os.getenv("TEST_URN")
    if not client_id or not client_secret or not test_urn:
        pytest.skip("Missing CLIENT_ID/CLIENT_SECRET/TEST_URN for live viewables test")

    token = get_2lo_token(client_id, client_secret)
    viewer = APSViewer(
        urn=test_urn,
        token=token,
        views_selector=True,
    )

    html = viewer.write()

    assert len(viewer.viewables) > 0
    assert any(v["name"] in html for v in viewer.viewables)


@pytest.mark.requires_secrets
def test_select_first_view_and_highlight_elements() -> None:
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    test_urn = os.getenv("TEST_URN")
    if not client_id or not client_secret or not test_urn:
        pytest.skip("Missing CLIENT_ID/CLIENT_SECRET/TEST_URN for live highlight test")

    token = get_2lo_token(client_id, client_secret)
    urn_bs64 = to_md_urn(test_urn)

    viewer = APSViewer(
        urn=test_urn,
        token=token,
        views_selector=True,
    )
    viewables = viewer.get_viewables(urn_bs64)
    if not viewables:
        pytest.skip("No viewables returned for TEST_URN")

    first_view = next((v for v in viewables if v.get("role") == "3d"), None)
    if not first_view:
        pytest.skip("No 3d viewables returned for TEST_URN")
    viewer.set_view_guid(first_view["guid"], first_view["name"], first_view["role"])

    metadata_views = get_metadata_viewables(token, urn_bs64)
    if not metadata_views:
        pytest.skip("No metadata viewables returned for TEST_URN")

    model_guid = next(
        (v["guid"] for v in metadata_views if v.get("role") == "3d"),
        metadata_views[0].get("guid"),
    )
    if not model_guid:
        pytest.skip("No valid model GUID available for metadata properties")

    payload: dict[str, object] = get_all_model_properties(token, urn_bs64, model_guid)
    data_raw = payload.get("data")
    data: dict[str, object] = cast(
        dict[str, object], data_raw if isinstance(data_raw, dict) else payload
    )
    collection = data.get("collection", [])

    seen: set[str] = set()
    external_ids: list[str] = []
    for item in collection:
        ext = item.get("externalId")
        if isinstance(ext, str) and ext and ext not in seen:
            seen.add(ext)
            external_ids.append(ext)
    if not external_ids:
        pytest.skip("No external IDs returned for selected view")

    print("external_ids sample:", external_ids[:10])

    rng = random.Random(0)
    highlight: list[ElementsInScene] = []
    for ext_id in external_ids[:3]:
        color = (
            f"#{rng.randrange(256):02x}{rng.randrange(256):02x}{rng.randrange(256):02x}"
        )
        highlight.append({"externalElementId": ext_id, "color": color})

    viewer.highlight_elements(highlight)
    html = viewer.write()

    assert first_view["guid"] in html
    for item in highlight:
        assert item["externalElementId"] in html
        assert item["color"] in html
