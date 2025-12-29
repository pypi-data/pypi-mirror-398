import os

import pytest
from dotenv import load_dotenv

from aps_viewer_sdk.helper import get_2lo_token
from aps_viewer_sdk import APSViewer
from aps_viewer_sdk.plugins import Draw3DSpheres


@pytest.mark.requires_secrets
def test_draw_3d_spheres_plugin_is_injected_into_html() -> None:
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    test_urn = os.getenv("TEST_URN")
    if not client_id or not client_secret or not test_urn:
        pytest.skip("Missing CLIENT_ID/CLIENT_SECRET/TEST_URN for sphere plugin test")

    token = get_2lo_token(client_id, client_secret)
    viewer = APSViewer(
        urn=test_urn,
        token=token,
        views_selector=False,
    )

    viewer.add_plugin(Draw3DSpheres(initial_radius=1.25, color="#00ff00").spec())

    html = viewer.write()
    viewer.show()

    assert "PLUGINS_PLACEHOLDER" not in html
    assert "PLUGINS_JS_PLACEHOLDER" not in html

    assert '"extensionId": "My.SphereMarkers"' in html
    assert '"only2d": false' in html
    assert '"initialRadius": 1.25' in html
    assert '"color": "#00ff00"' in html

    assert 'const EXT_ID = "My.SphereMarkers";' in html


if __name__ == "__main__":
    test_draw_3d_spheres_plugin_is_injected_into_html()
