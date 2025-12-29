import os

import pytest
from dotenv import load_dotenv

from aps_viewer_sdk.helper import get_2lo_token
from aps_viewer_sdk import APSViewer
from aps_viewer_sdk.plugins import Draw2DCircles


@pytest.mark.requires_secrets
def test_draw_2d_circles_plugin_is_injected_into_html() -> None:
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    test_urn = os.getenv("TEST_URN")
    if not client_id or not client_secret or not test_urn:
        pytest.skip("Missing CLIENT_ID/CLIENT_SECRET/TEST_URN for circle plugin test")

    token = get_2lo_token(client_id, client_secret)
    viewer = APSViewer(
        urn=test_urn,
        token=token,
        views_selector=True,
    )

    viewer.add_plugin(Draw2DCircles(initial_radius=0.5, color="#00ff00").spec())

    html = viewer.write()
    viewer.show()

    assert "PLUGINS_PLACEHOLDER" not in html
    assert "PLUGINS_JS_PLACEHOLDER" not in html

    assert '"extensionId": "My.CircleMarkers"' in html
    assert '"only2d": true' in html
    assert '"initialRadius": 0.5' in html
    assert '"color": "#00ff00"' in html

    assert 'const EXT_ID = "My.CircleMarkers";' in html


if __name__ == "__main__":
    test_draw_2d_circles_plugin_is_injected_into_html()
