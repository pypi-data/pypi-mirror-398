# Built-Ins
from dataclasses import dataclass
from pathlib import Path

# Dependency
from PySide6.QtWidgets import (
    QMainWindow,
    QHBoxLayout,
    QWidget,
    QMenu,
    QFileDialog,
    QDockWidget,
)
from PySide6.QtCore import Qt
import pyqtgraph as pg  # type: ignore
import numpy as np

from hypmix.io import load_model_result

# Local Imports
from .image_view_container import ImViewContainer
from .model_tree import ModelTreeWidget
from .endmember_viewer import EndmemberViewerWidget
from .catalog.actions import ActionCatalog

# Top-Level Imports
from hypmix.file_opening_utils import open_cube

USER_ROLE = Qt.ItemDataRole.UserRole
VERSION_NUM = "0.2.0"


@dataclass
class MasterState:
    base_dir: Path = Path.cwd()


class MixView(QMainWindow):
    def __init__(
        self,
        frac: Path | None = None,
        resi: Path | None = None,
        model: Path | None = None,
        base: Path | None = None,
    ) -> None:
        super().__init__()

        self.state = MasterState()

        self.setWindowTitle("MixView v0.2.0")

        self.frac_view = pg.ImageView()
        self.resi_view = pg.ImageView()
        self.model_tree = ModelTreeWidget()
        self.em_view = EndmemberViewerWidget()
        self.tree_dock: QDockWidget | None = None

        self.frac_container = ImViewContainer(self.frac_view, parent=self)
        self.resi_container = ImViewContainer(
            self.resi_view, parent=self, color_extremes=False
        )

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.frac_container)
        main_layout.addWidget(self.resi_container)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Make the model tree dockable on the right (can be moved/floated)
        tree_dock = QDockWidget("Models", self)
        tree_dock.setWidget(self.model_tree)
        tree_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        tree_dock.setMinimumWidth(200)
        self.tree_dock = tree_dock

        em_dock = QDockWidget("Endmembers", self)
        em_dock.setWidget(self.em_view)
        em_dock.setAllowedAreas(
            Qt.DockWidgetArea.TopDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        em_dock.setMinimumHeight(200)
        self.em_dock = em_dock

        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, em_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, tree_dock)

        menubar = self.menuBar()

        file_menu = QMenu("File")
        data_menu = QMenu("Data")
        menubar.addMenu(file_menu)
        menubar.addMenu(data_menu)

        open_menu = QMenu("Open")
        file_menu.addMenu(open_menu)

        file_menu.addAction(ActionCatalog.set_base.build(main_widget, self))

        open_menu.addAction(ActionCatalog.open_frac.build(main_widget, self))
        open_menu.addAction(ActionCatalog.open_resi.build(main_widget, self))
        open_menu.addAction(ActionCatalog.open_model.build(main_widget, self))

        data_menu.addAction(tree_dock.toggleViewAction())
        data_menu.addAction(em_dock.toggleViewAction())

        self.model_tree.tree.itemSelectionChanged.connect(self.set_model)

        if frac is not None:
            self.load_frac(fp=frac)
        if resi is not None:
            self.load_resi(fp=resi)
        if base is not None:
            self.state.base_dir = base
        if model is not None:
            self.load_model(fp=model)

        self.resize(1400, 1000)

    def load_model(self, *, fp: Path | None = None):
        if fp is None:
            fp_str, fp_type = QFileDialog.getOpenFileName(
                caption="Select Model Result",
                filter=("HDF5 Files (*.hdf5)"),
                dir=str(self.state.base_dir),
            )
            fp = Path(fp_str)

        self.model_tree.add_model(fp)

    def load_frac(self, *, fp: Path | None = None):

        if fp is None:
            fp_str, fp_type = QFileDialog.getOpenFileName(
                caption="Select Fraction Cube",
                filter=(
                    "Rasterio-Compatible Files (*.bsq *.img *.tif);;"
                    "Spectral Cube Files (*.spcub *.geospcub)"
                ),
                dir=str(self.state.base_dir),
            )
            fp = Path(fp_str)
        cube, _suffix = open_cube(fp)
        self.set_frac(cube)

    def load_resi(self, *, fp: Path | None = None):
        if fp is None:
            fp_str, fp_type = QFileDialog.getOpenFileName(
                caption="Select Residual Cube",
                filter=(
                    "Rasterio-Compatible Files (*.bsq *.img *.tif);;"
                    "Spectral Cube Files (*.spcub *.geospcub)"
                ),
                dir=str(self.state.base_dir),
            )
            fp = Path(fp_str)
        cube, _suffix = open_cube(fp)
        self.set_resi(cube)

    def set_frac(self, cube: np.ndarray):
        self.frac_view.setImage(cube, axes={"y": 0, "x": 1, "t": 2})
        self.frac_view.setLevels(0, 1)

    def set_resi(self, cube: np.ndarray):
        self.resi_view.setImage(cube, axes={"y": 0, "x": 1, "t": 2})
        idx = self.resi_view.currentIndex
        vals = cube[np.isfinite(cube[:, :, idx]), idx]
        lo, hi = np.percentile(vals, [0.5, 99.5])
        self.resi_view.setLevels(lo, hi)

    def set_base(self):
        fp = QFileDialog.getExistingDirectory()
        self.state.base_dir = Path(fp)

    def set_model(self) -> None:
        selection = self.model_tree.get_selection_path()
        if selection is None:
            return
        model = load_model_result(selection.fp, selection.model)
        self.set_frac(model.unmixed_image.fracs)
        self.set_resi(model.unmixed_image.res)
        self.frac_container.connect_title(model.endmembers.endmember_name_list)
        wvl = list(model.endmembers.endmember_list[0].spectrum.wvl)
        wvl = [f"{str(i)} nm" for i in wvl]
        self.resi_container.connect_title(wvl)
        self.em_view.show_endmembers(model)
