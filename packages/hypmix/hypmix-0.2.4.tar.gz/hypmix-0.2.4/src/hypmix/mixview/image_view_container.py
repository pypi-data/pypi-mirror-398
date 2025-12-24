# Dependencies
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal
import pyqtgraph as pg  # type: ignore
import cmap
import numpy as np

# Top-Level Imports
from hypmix.util_classes import CursorInfo


class ImViewContainer(QWidget):
    mouse_moved = Signal(CursorInfo)

    def __init__(
        self,
        imview_widget: pg.ImageView,
        parent: QWidget | None = None,
        color_extremes: bool = True,
    ) -> None:
        super().__init__(parent)

        layout = QVBoxLayout()
        self.title = QLabel()
        self.imview_widget = imview_widget

        custom_cmap = cmap.Colormap("matlab:gray")
        lut = (custom_cmap.lut(N=8) * 255).astype(np.uint8)
        hist_item = self.imview_widget.getHistogramWidget().item
        if color_extremes:
            pos = np.linspace(0.01, 0.99, lut.shape[0] - 2)
            lut[0] = [255, 0, 0, 255]  # Red
            lut[-1] = [0, 255, 255, 255]  # Cyan
            pos = np.insert(pos, 0, 0)
            pos = np.append(pos, 1)
        else:
            pos = np.linspace(0.0, 1.0, lut.shape[0])

        lut_cmap = pg.ColorMap(pos, lut)
        hist_item.gradient.setColorMap(lut_cmap)

        layout.addWidget(self.title)
        layout.addWidget(self.imview_widget)

        self.setLayout(layout)

        self.imview_widget.scene.sigMouseMoved.connect(self.on_movement)  # type: ignore  # noqa

    def connect_title(self, lbls: list):
        def _update_title():
            title = lbls[self.imview_widget.currentIndex]
            self.title.setText(title)

        _update_title()
        self.imview_widget.timeLine.sigPositionChanged.connect(_update_title)

    def on_movement(self, pos):
        view_pos = self.imview_widget.getView().mapSceneToView(pos)
        x_float = view_pos.x()
        y_float = view_pos.y()
        x_int = int(x_float)
        y_int = int(y_float)
        img = self.imview_widget.getImageItem().image  # axes flipped
        if img is None:
            return
        if 0 <= y_int < img.shape[1] and 0 <= x_int < img.shape[0]:
            ci = CursorInfo(
                x=x_float,
                y=y_float,
                xint=x_int,
                yint=y_int,
                val=img[x_int, y_int],
            )
            self.mouse_moved.emit(ci)
