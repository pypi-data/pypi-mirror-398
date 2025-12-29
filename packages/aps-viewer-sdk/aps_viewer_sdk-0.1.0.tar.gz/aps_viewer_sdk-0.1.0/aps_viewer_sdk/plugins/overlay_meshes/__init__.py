from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..base import PluginSpec


@dataclass
class OverlayMeshes:
    scene_id: str = "overlay_meshes"
    _items: list[dict[str, Any]] = field(default_factory=list, init=False, repr=False)

    def add_box(
        self,
        position: Sequence[float],
        size: Sequence[float] = (1, 1, 1),
        color: str = "#00ff00",
        opacity: float = 1.0,
        align_to_world_up: bool = False,
    ) -> None:
        self._items.append(
            {
                "type": "box",
                "sceneId": self.scene_id,
                "position": [
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),
                ],
                "width": float(size[0]),
                "height": float(size[1]),
                "depth": float(size[2]),
                "color": color,
                "opacity": float(opacity),
                "alignToWorldUp": bool(align_to_world_up),
            }
        )

    def add_sphere(
        self,
        position: Sequence[float],
        radius: float = 1.0,
        color: str = "#00ff00",
        opacity: float = 1.0,
        segments: int = 24,
    ) -> None:
        self._items.append(
            {
                "type": "sphere",
                "sceneId": self.scene_id,
                "position": [
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),
                ],
                "radius": float(radius),
                "segments": int(segments),
                "color": color,
                "opacity": float(opacity),
            }
        )

    def add_cone(
        self,
        position: Sequence[float],
        radius: float = 1.0,
        height: float = 1.0,
        color: str = "#00ff00",
        opacity: float = 1.0,
        radial_segments: int = 18,
        align_to_world_up: bool = False,
    ) -> None:
        self._items.append(
            {
                "type": "cone",
                "sceneId": self.scene_id,
                "position": [
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),
                ],
                "radius": float(radius),
                "height": float(height),
                "radialSegments": int(radial_segments),
                "color": color,
                "opacity": float(opacity),
                "alignToWorldUp": bool(align_to_world_up),
            }
        )

    def spec(self) -> PluginSpec:
        js_path = Path(__file__).resolve().parent / "overlay_meshes.js"
        js_content = js_path.read_text(encoding="utf-8")

        return PluginSpec(
            extension_id="My.OverlayMeshes",
            only_2d=False,
            options={"items": list(self._items)},
            js_content=js_content,
        )
