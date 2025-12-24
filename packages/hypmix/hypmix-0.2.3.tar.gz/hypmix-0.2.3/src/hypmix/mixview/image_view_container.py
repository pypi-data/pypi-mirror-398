# Dependencies
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
import pyqtgraph as pg  # type: ignore
import cmap
import numpy as np


class ImViewContainer(QWidget):
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

    def connect_title(self, lbls: list):
        def _update_title():
            title = lbls[self.imview_widget.currentIndex]
            self.title.setText(title)

        _update_title()
        self.imview_widget.timeLine.sigPositionChanged.connect(_update_title)
