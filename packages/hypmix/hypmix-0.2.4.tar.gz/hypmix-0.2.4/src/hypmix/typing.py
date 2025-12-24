# Standard Libraries
from dataclasses import dataclass
from typing import TypeVar
from typing_extensions import Annotated
import os
from pathlib import Path

# Dependencies
import numpy.typing as npt
import numpy as np

PathLike = str | os.PathLike | Path

DType = TypeVar("DType", bound=np.generic)
SpectrumLike = Annotated[npt.NDArray[DType], (1,)]
ImageCubeLike = Annotated[npt.NDArray[DType], (3,)]
ImageLike = Annotated[npt.NDArray[DType], (2,)]


@dataclass
class Spectrum:
    data: SpectrumLike
    wvl: SpectrumLike


@dataclass
class ImageCube:
    data: ImageCubeLike
    wvl: SpectrumLike
    bands_first: bool = False

    def __post_init__(self):
        bands_dim = np.argmin(self.data.shape)
        self.data = np.moveaxis(self.data, bands_dim, -1)
