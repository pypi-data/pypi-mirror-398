import json
import tempfile
import webbrowser
from pathlib import Path
from typing import Annotated, Any, TypedDict

from .helper import get_viewables_from_urn, to_md_urn
from .plugins.base import PluginSpec


class ElementsInScene(TypedDict):
    externalElementId: Annotated[
        str,
        "External identifier that identifies the elements in the APS viewer. Can be retrieved using the APS Apis",
    ]
    color: Annotated[
        str, "HEX color in format #RRGGBB (e.g., #ff0000 for red, #00ff00 for green)"
    ]


class APSViewer:
    def __init__(
        self,
        urn: Annotated[
            str, "Version URN e.g urn:adsk.wipprod:fs.file:vf.Skn9c5Q?version=1"
        ],
        token: Annotated[str, "2Lo | 3Lo token"],
        views_selector: Annotated[bool, "Toggle a view picker"] = True,
    ):
        self.urn = urn
        self.token = token
        self.views_selector = views_selector

        self.viewables: list[dict[str, Any]] = []
        self.element2highlight: list[ElementsInScene] = []
        self.selected_view_guid: str | None = None
        self._html_content: str | None = None

        self._plugins: list[PluginSpec] = []

    def add_plugin(self, plugin_spec: PluginSpec) -> None:
        self._plugins.append(plugin_spec)

    def set_view_guid(
        self,
        guid: Annotated[str, "View GUID from the manifest"],
        name: Annotated[str, "Display name in the view selector"] = "Selected View",
        role: Annotated[str, "View role, e.g. 3d or 2d"] = "3d",
    ) -> None:
        self.selected_view_guid = guid
        self.viewables = [{"guid": guid, "name": name, "role": role}]

    def highlight_elements(self, highlightList: list[ElementsInScene]):
        self.element2highlight = highlightList

    def get_viewables(
        self, urn_bs64: Annotated[str, "Version URN in BS64"]
    ) -> list[dict[str, Any]]:
        return get_viewables_from_urn(self.token, urn_bs64)

    def build(self) -> None:
        urn_bs64 = to_md_urn(self.urn)

        if self.views_selector and not self.viewables:
            self.viewables = self.get_viewables(urn_bs64)

        html_path = Path(__file__).resolve().parent / "templates" / "viewer.html"
        html = html_path.read_text(encoding="utf-8")

        html = html.replace("APS_TOKEN_PLACEHOLDER", self.token)
        html = html.replace("URN_PLACEHOLDER", urn_bs64)

        external_ids_json = (
            json.dumps(
                [
                    {item["externalElementId"]: item["color"]}
                    for item in self.element2highlight
                ]
            )
            if self.element2highlight
            else "[]"
        )
        html = html.replace("EXTERNAL_IDS_PLACEHOLDER", external_ids_json)

        viewables_json = json.dumps(self.viewables) if self.viewables else "[]"
        html = html.replace("VIEWABLES_PLACEHOLDER", viewables_json)

        selected_view_guid = self.selected_view_guid or ""
        html = html.replace("SELECTED_VIEW_GUID_PLACEHOLDER", selected_view_guid)

        plugins_json = (
            json.dumps(
                [
                    {
                        "extensionId": p.extension_id,
                        "only2d": bool(p.only_2d),
                        "options": p.options or {},
                    }
                    for p in self._plugins
                ]
            )
            if self._plugins
            else "[]"
        )
        html = html.replace("PLUGINS_PLACEHOLDER", plugins_json)

        plugin_scripts = [f"<script>\n{p.js_content}\n</script>" for p in self._plugins]
        html = html.replace("PLUGINS_JS_PLACEHOLDER", "\n".join(plugin_scripts))

        self._html_content = html

    def write(self) -> Annotated[str, "HTML string with the view"]:
        if self._html_content is None:
            self.build()
        assert self._html_content is not None
        return self._html_content

    def show(self) -> None:
        html_content = self.write()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            temp_path = f.name

        webbrowser.open(f"file://{temp_path}")
