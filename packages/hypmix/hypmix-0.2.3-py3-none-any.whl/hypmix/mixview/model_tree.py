# Built-Ins
from dataclasses import dataclass
from pathlib import Path

# Dependencies
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
import h5py as h5  # type: ignore

USER_ROLE = Qt.ItemDataRole.UserRole


@dataclass
class LoadedModel:
    header: str
    fp: Path
    model: str = ""


class ModelTreeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.setMinimumWidth(200)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def add_model(self, fp: Path):
        with h5.File(fp) as f:
            top_level_groups = [
                name for name, obj in f.items() if isinstance(obj, h5.Group)
            ]
        self._populate_tree(fp.stem, top_level_groups, fp)

    def _populate_tree(self, heading: str, values: list[str], fp: Path):
        parent_item = QTreeWidgetItem([heading])
        parent_item.setFlags(
            parent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable
        )
        self.tree.addTopLevelItem(parent_item)

        for child_text in values:
            item = QTreeWidgetItem(parent_item, [child_text])
            metadata = LoadedModel(header=heading, fp=fp, model=child_text)
            item.setData(0, USER_ROLE, metadata)

        parent_item.setExpanded(True)

    def get_selection_path(self) -> LoadedModel | None:
        items = self.tree.selectedItems()
        if not items:
            return None

        return items[0].data(0, USER_ROLE)
