from PySide6.QtWidgets import QApplication
from hypmix.mixview.main_window import MixView
import sys
from pathlib import Path


def open_mixview(model_path: str | Path | None = None) -> None:
    """
    Convenience function for opening the main MixView GUI.

    Parameters
    ----------
    model_path: str or Path, optional, default=None
        File path to a model result file (.HDF5 format)
    """
    app = QApplication(sys.argv)
    main = MixView()
    main.show()
    app.exec()


if __name__ == "__main__":
    open_mixview()
