# Standard Libraries
from dataclasses import dataclass
from typing_extensions import Annotated
from typing import Tuple

# Dependencies
import numpy as np
import numpy.typing as npt

# Relative Imports
from .typing import ImageCubeLike


@dataclass
class MixedCube:
    """
    Represents an made up of pixels that are each an areal mixture of spectral
    endmembers.

    Attributes
    ----------
    G: NDArray[np.float32, (2,)]
        Least squares design matrix. The array is of shape NxM where N is the
        number of spectral bands and M is the number of endmembers in the
        unmixing model.
    d: NDArray[np.float32, (3,)]
        Data matrix for every pixel. This is just the spectral cube data.
    """

    G: Annotated[npt.NDArray[np.float32], (2,)]
    d: Annotated[npt.NDArray[np.float32], (3,)]


@dataclass
class UnMixedCube:
    """
    The results of spectral unmixing.

    Attributes
    ----------
    model: NDArray[np.float32, (3,)]
        Modeled spectral cube, where each pixel is a linear combination of
        endmembers that best fits the actual data.
    fracs: NDArray[np.float32, (3,)]
        3D array representing the modeled fractions of endmembers at all
        pixels.
    res: NDArray[np.float32, (2,)]
        Pixel-by-pixel model residuals. That is, a Spectrum-Like vector for
        each pixel that represents model - data in each spectral band.
    """

    model: ImageCubeLike
    fracs: ImageCubeLike
    res: ImageCubeLike


def _solve_cube(
    G: Annotated[npt.NDArray[np.float32], (2,)],
    d: Annotated[npt.NDArray[np.float32], (3,)],
) -> Tuple[ImageCubeLike, ImageCubeLike, ImageCubeLike]:
    prefix = np.linalg.inv(G.T @ G) @ G.T

    fracs = np.einsum("ij,...j->...i", prefix, d)

    model = np.einsum("ij,...j->...i", G, fracs)

    res = model - d

    return model, fracs, res


def unmix_spectral_cube(mixed_cube: MixedCube, add_to_one: bool = True):
    G = mixed_cube.G
    d = mixed_cube.d

    if add_to_one:
        G_aug = np.hstack((G, np.ones([G.shape[0], 1])), dtype=np.float32)
        bottom_row = np.append(np.ones(G.shape[1]), 0)
        G_aug = np.vstack((G_aug, bottom_row), dtype=np.float32)

        d_aug = np.concat(
            [d, np.ones(d.shape[:2])[:, :, None]], axis=2, dtype=np.float32
        )

        model, fracs, res = _solve_cube(G_aug, d_aug)
    else:
        model, fracs, res = _solve_cube(G, d)

    return UnMixedCube(model, fracs, res)
