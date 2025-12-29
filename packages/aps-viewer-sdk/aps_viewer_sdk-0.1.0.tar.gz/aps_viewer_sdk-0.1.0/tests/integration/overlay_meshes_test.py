import os

import pytest
from dotenv import load_dotenv

from aps_viewer_sdk.helper import get_2lo_token
from aps_viewer_sdk import APSViewer
from aps_viewer_sdk.plugins import OverlayMeshes


@pytest.mark.requires_secrets
def make_tree_plugin() -> OverlayMeshes:
    trees = OverlayMeshes(scene_id="trees-overlay")
    specs = [
        {
            "base": (0, 0, -25),
            "trunk_size": (2.0, 10.0, 2.0),
            "canopy": [
                {"radius": 6.0, "height": 8.0, "z": -25 + 10.0 + 4.0},
                {"radius": 5.0, "height": 6.5, "z": -25 + 10.0 + 8.0},
                {"radius": 4.0, "height": 5.0, "z": -25 + 10.0 + 11.0},
            ],
            "trunk_color": "#8b5a2b",
            "leaves_color": "#2e8b57",
        },
        {
            "base": (18, -12, -22),
            "trunk_size": (1.6, 9.0, 1.6),
            "canopy": [
                {"radius": 5.5, "height": 7.5, "z": -22 + 9.0 + 3.5},
                {"radius": 4.4, "height": 6.0, "z": -22 + 9.0 + 7.0},
                {"radius": 3.5, "height": 4.5, "z": -22 + 9.0 + 9.5},
            ],
            "trunk_color": "#7a4a2a",
            "leaves_color": "#2f7d50",
        },
        {
            "base": (-15, 8, -20),
            "trunk_size": (2.2, 11.0, 2.2),
            "canopy": [
                {"radius": 6.8, "height": 8.5, "z": -20 + 11.0 + 4.2},
                {"radius": 5.5, "height": 7.0, "z": -20 + 11.0 + 8.0},
                {"radius": 4.2, "height": 5.5, "z": -20 + 11.0 + 11.0},
            ],
            "trunk_color": "#654321",
            "leaves_color": "#3c9b63",
        },
    ]

    for spec in specs:
        x, y, z = spec["base"]
        trunk_w, trunk_h, trunk_d = spec["trunk_size"]
        trees.add_box(
            (x, y, z + trunk_h / 2.0),
            size=(trunk_w, trunk_h, trunk_d),
            color=spec["trunk_color"],
            opacity=1.0,
            align_to_world_up=True,
        )
        for canopy in spec["canopy"]:
            trees.add_cone(
                (x, y, canopy["z"]),
                radius=canopy["radius"],
                height=canopy["height"],
                color=spec["leaves_color"],
                opacity=1.0,
                radial_segments=14,
                align_to_world_up=True,
            )

    return trees


@pytest.mark.requires_secrets
def test_overlay_meshes_plugin_is_injected_into_html() -> None:
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    test_urn = os.getenv("TEST_URN")
    if not client_id or not client_secret or not test_urn:
        pytest.skip("Missing CLIENT_ID/CLIENT_SECRET/TEST_URN for overlay meshes test")

    token = get_2lo_token(client_id, client_secret)
    viewer = APSViewer(
        urn=test_urn,
        token=token,
        views_selector=False,
    )

    trees = make_tree_plugin()
    viewer.add_plugin(trees.spec())

    html = viewer.write()
    viewer.show()

    assert "PLUGINS_PLACEHOLDER" not in html
    assert "PLUGINS_JS_PLACEHOLDER" not in html

    assert '"extensionId": "My.OverlayMeshes"' in html
    assert '"only2d": false' in html
    assert '"sceneId": "trees-overlay"' in html

    assert "#8b5a2b" in html
    assert "#2e8b57" in html

    assert 'const EXT_ID = "My.OverlayMeshes";' in html


if __name__ == "__main__":
    test_overlay_meshes_plugin_is_injected_into_html()
