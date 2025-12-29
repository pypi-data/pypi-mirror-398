from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..base import PluginSpec


@dataclass(frozen=True)
class Draw2DCircles:
    initial_radius: float = 2.0
    color: str = "#ff0000"

    def spec(self) -> PluginSpec:
        js_path = Path(__file__).resolve().parent / "circle_markers_2d.js"
        js_content = js_path.read_text(encoding="utf-8")

        return PluginSpec(
            extension_id="My.CircleMarkers",
            only_2d=True,
            options={
                "initialRadius": float(self.initial_radius),
                "color": str(self.color),
            },
            js_content=js_content,
        )
