"""Unit tests for viewer plugins without requiring API credentials."""

from aps_viewer_sdk import APSViewer
from aps_viewer_sdk.plugins import Draw2DCircles, Draw3DSpheres, OverlayMeshes


def test_draw_2d_circles_plugin_spec() -> None:
    """Test that Draw2DCircles plugin generates correct spec."""
    plugin = Draw2DCircles(initial_radius=0.5, color="#00ff00")
    spec = plugin.spec()

    assert spec.extension_id == "My.CircleMarkers"
    assert spec.only_2d is True
    assert spec.options["initialRadius"] == 0.5
    assert spec.options["color"] == "#00ff00"
    assert len(spec.js_content) > 0


def test_draw_3d_spheres_plugin_spec() -> None:
    """Test that Draw3DSpheres plugin generates correct spec."""
    plugin = Draw3DSpheres(initial_radius=1.25, color="#ff0000")
    spec = plugin.spec()

    assert spec.extension_id == "My.SphereMarkers"
    assert spec.only_2d is False
    assert spec.options["initialRadius"] == 1.25
    assert spec.options["color"] == "#ff0000"
    assert len(spec.js_content) > 0


def test_overlay_meshes_plugin_spec() -> None:
    """Test that OverlayMeshes plugin generates correct spec."""
    plugin = OverlayMeshes(scene_id="test-scene")
    spec = plugin.spec()

    assert spec.extension_id == "My.OverlayMeshes"
    assert spec.only_2d is False
    assert "items" in spec.options
    assert isinstance(spec.options["items"], list)
    assert len(spec.js_content) > 0


def test_plugin_injection_into_viewer() -> None:
    """Test that plugins are correctly injected into viewer HTML."""
    viewer = APSViewer(
        urn="test-urn-12345",
        token="test-token",
        views_selector=False,
    )

    viewer.add_plugin(Draw2DCircles(initial_radius=0.5, color="#00ff00").spec())
    html = viewer.write()

    assert "PLUGINS_PLACEHOLDER" not in html
    assert "PLUGINS_JS_PLACEHOLDER" not in html
    assert '"extensionId": "My.CircleMarkers"' in html
    assert '"only2d": true' in html
    assert '"initialRadius": 0.5' in html
    assert '"color": "#00ff00"' in html


def test_multiple_plugins_injection() -> None:
    """Test that multiple plugins can be added to viewer."""
    viewer = APSViewer(
        urn="test-urn-12345",
        token="test-token",
        views_selector=False,
    )

    viewer.add_plugin(Draw2DCircles(initial_radius=0.5, color="#00ff00").spec())
    viewer.add_plugin(Draw3DSpheres(initial_radius=1.25, color="#ff0000").spec())

    html = viewer.write()

    assert '"extensionId": "My.CircleMarkers"' in html
    assert '"extensionId": "My.SphereMarkers"' in html
    assert '"initialRadius": 0.5' in html
    assert '"initialRadius": 1.25' in html
