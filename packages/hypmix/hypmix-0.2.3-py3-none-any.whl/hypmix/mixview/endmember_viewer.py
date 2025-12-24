from PySide6.QtWidgets import QWidget, QHBoxLayout
import pyqtgraph as pg  # type: ignore
import hypmix
import cmap
import reflspeckit as rsk


class EndmemberViewerWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.plot_widget = pg.PlotWidget()
        self.contrem_widget = pg.PlotWidget()
        self.legend = self.plot_widget.addLegend()

        layout = QHBoxLayout()
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.contrem_widget)
        self.setLayout(layout)

    def show_endmembers(self, model: hypmix.ModelResult):
        item1 = self.plot_widget.getPlotItem()
        item2 = self.contrem_widget.getPlotItem()
        if item1 is not None:
            item1.clear()
        if item2 is not None:
            item2.clear()
        base_cmap = cmap.Colormap("crameri:hawaii")
        ncolors = len(model.endmembers.endmember_list)
        cmap_lut = base_cmap.lut(ncolors) * 255
        for n, em in enumerate(model.endmembers.endmember_list):
            c = pg.mkColor(tuple(cmap_lut[n, :]))
            _spec = pg.PlotDataItem(
                em.spectrum.wvl,
                em.spectrum.data,
                name=em.name,
                pen=pg.mkPen(color=c, width=1),
            )

            rspec = rsk.Spec1D(em.spectrum.data, em.spectrum.wvl)
            rspec.outlier_removal()
            rspec.noise_reduction("box_filter", 7)
            rspec.continuum_removal("double_line")

            _contrem = pg.PlotDataItem(
                rspec.wavelength.values,
                rspec.contrem,
                name=em.name,
                pen=pg.mkPen(color=c, width=1),
            )

            self.plot_widget.addItem(_spec)
            self.contrem_widget.addItem(_contrem)
