from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PluginSpec:
    extension_id: str
    only_2d: bool
    options: dict[str, Any]
    js_content: str
