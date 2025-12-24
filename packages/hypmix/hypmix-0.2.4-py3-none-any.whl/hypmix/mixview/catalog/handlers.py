from __future__ import annotations

from hypmix.util_classes import CursorInfo

# Type-Checking Help
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main_window import MixView


class SignalHandlers:
    def __init__(self, window: MixView) -> None:
        self.window = window

    def track_cursor(self, ci: CursorInfo):
        self.window.model_view.update_plots(ci)
