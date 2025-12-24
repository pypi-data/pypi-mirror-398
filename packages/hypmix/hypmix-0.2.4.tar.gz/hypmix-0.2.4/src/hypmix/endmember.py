# Standard Libraries
from dataclasses import dataclass
from typing import Tuple

# Dependencies
import numpy as np

# Relative Imports
from .typing import Spectrum, PathLike


@dataclass
class EndMember:
    name: str
    spectrum: Spectrum


@dataclass
class InSceneEndMember(EndMember):
    coord: Tuple[int, int]


@dataclass
class ExternalEndMember(EndMember):
    file_path: PathLike


class EndMemberGroup:
    def __init__(self, endmember_list: list[EndMember]):
        self.endmember_list = endmember_list
        self.endmember_array = np.empty(
            (len(endmember_list[0].spectrum.data), len(endmember_list)),
            dtype=np.float32,
        )
        self.endmember_name_list: list[str] = []

        for n, i in enumerate(endmember_list):
            self.endmember_array[:, n] = i.spectrum.data
            self.endmember_name_list.append(i.name)

    def __len__(self):
        return len(self.endmember_name_list)


def read_endmember_set(
    names: list[str], arr: np.ndarray, wvl: np.ndarray
) -> list[EndMember]:
    em_list: list[EndMember] = []
    for n, name in enumerate(names):
        spec = Spectrum(arr[n, :], wvl)
        em_list.append(EndMember(name, spec))
    return em_list
