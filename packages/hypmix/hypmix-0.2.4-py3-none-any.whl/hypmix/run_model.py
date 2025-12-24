# Standard Libraries
from dataclasses import dataclass, field

# Dependencies
import numpy as np

# Relative Imports
from .typing import ImageCube, Spectrum, PathLike
from .io import ModelResult
from .model_math import unmix_spectral_cube, MixedCube
from .endmember import EndMember, EndMemberGroup


class EndmemberAlreadyExistsError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class ModelState:
    has_reflector: bool = False
    has_shade: bool = False
    has_blackbody: bool = False
    endmember_count: int = 0


@dataclass
class MixtureModel:
    """
    Parameters
    ----------
    endmembers: list[EndMember]
        List of model endmembers to use.
    data_cube: ImageCube
        Spectral data cube.
    """

    endmembers: list[EndMember]
    data_cube: ImageCube
    state: ModelState = field(default_factory=ModelState)

    def __post_init__(self):
        if self.data_cube.bands_first:
            self.data_cube.data = np.transpose(self.data_cube.data, (1, 2, 0))
        self.state.endmember_count = len(self.endmembers)

    def add_endmember(self, endmember: EndMember) -> None:
        if endmember.name in [i.name for i in self.endmembers]:
            raise EndmemberAlreadyExistsError(
                f"{endmember} has the same name as an existing endmember."
            )
        self.endmembers.append(endmember)
        self.state.endmember_count += 1

    def add_virtual_reflector(self):
        if not self.state.has_reflector:
            self.endmembers.append(
                EndMember(
                    "Reflector",
                    Spectrum(
                        np.ones(len(self.data_cube.wvl)), self.data_cube.wvl
                    ),
                )
            )
            self.state.endmember_count += 1
            self.state.has_reflector = True

    def add_virtual_shade(self):
        if not self.state.has_shade:
            self.endmembers.append(
                EndMember(
                    "Shade",
                    Spectrum(
                        0.001 * np.ones(len(self.data_cube.wvl)),
                        self.data_cube.wvl,
                    ),
                )
            )
            self.state.endmember_count += 1
            self.state.has_shade = True
        else:
            raise EndmemberAlreadyExistsError(
                "Virtual Shade already exists in this model."
            )

    def add_virtual_blackbody(self) -> None:
        if not self.state.has_blackbody:
            self.endmembers.append(
                EndMember(
                    "Blackbody",
                    Spectrum(
                        np.ones(len(self.data_cube.wvl)), self.data_cube.wvl
                    ),
                )
            )
            self.state.endmember_count += 1
            self.state.has_blackbody = True
        else:
            raise EndmemberAlreadyExistsError(
                "Virtual blackbody already exists in this model."
            )

    def run(self, dst_path: PathLike, modelID: str) -> ModelResult:
        G = np.empty(
            [len(self.data_cube.wvl), len(self.endmembers)], dtype=np.float32
        )
        for n, em in enumerate(self.endmembers):
            G[:, n] = em.spectrum.data
        mixed_cube = MixedCube(G, self.data_cube.data)
        unmixed_cube = unmix_spectral_cube(mixed_cube)
        rsquared = np.sqrt(np.sum(unmixed_cube.res**2, axis=2))

        result = ModelResult(
            dst_path,
            modelID,
            unmixed_cube,
            EndMemberGroup(self.endmembers),
            rsquared,
        )

        return result
