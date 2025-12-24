from dataclasses import dataclass
from typing import Optional

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget


@dataclass
class ActionSpec:
    text: str
    callback_name: str
    shortcut: Optional[str] = None
    _action: Optional[QAction] = None

    def build(self, parent: QWidget, receiver: object) -> QAction:
        if self._action is None:
            action = QAction(self.text, parent)
            if self.shortcut is not None:
                action.setShortcut(self.shortcut)

            callback = getattr(receiver, self.callback_name)

            action.triggered.connect(callback)
            self._action = action
        return self._action


@dataclass
class ActionCatalog:
    open_frac = ActionSpec(text="Fraction Cube", callback_name="load_frac")
    open_resi = ActionSpec(text="Residual Cube", callback_name="load_resi")
    open_model = ActionSpec(text="Hypmix Model", callback_name="load_model")
    set_base = ActionSpec(text="Set Base", callback_name="set_base")
