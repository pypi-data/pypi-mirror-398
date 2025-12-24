# Standard Libraries
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from typing import Optional

# Dependencies
import rasterio as rio  # type: ignore
from rasterio.crs import CRS  # type: ignore
import numpy.typing as npt
import h5py as h5  # type: ignore

# Relative Imports
from .typing import PathLike, Spectrum
from .endmember import EndMemberGroup, EndMember
from .model_math import UnMixedCube


type GeotransformType = tuple[float, float, float, float, float, float]


class UnsupportedFileExtensionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class ModelResult:
    savefile: PathLike
    modelID: str
    unmixed_image: UnMixedCube
    endmembers: EndMemberGroup
    rsquared: npt.NDArray


class SaveMode(Enum):
    HDF5 = ".hdf5"
    SMA = ".sma"
    CSV = ".csv"


def save_model_result(res: ModelResult):
    file_ext = Path(res.savefile).suffix

    try:
        mode = SaveMode(file_ext)
    except ValueError:
        raise UnsupportedFileExtensionError(
            f"{file_ext} is not a supported" "file type."
        )
    match mode:
        case SaveMode.HDF5:
            if Path(res.savefile).is_file():
                open_flag = "r+"
            else:
                open_flag = "w"

            with h5.File(res.savefile, open_flag) as f:
                try:
                    g = f.create_group(res.modelID)
                except ValueError:
                    del f[res.modelID]
                    g = f.create_group(res.modelID)

                g.attrs["wavelengths"] = res.endmembers.endmember_list[
                    0
                ].spectrum.wvl
                gg = g.create_group("endmembers")
                for n, name in enumerate(res.endmembers.endmember_name_list):
                    gg.create_dataset(
                        name,
                        data=res.endmembers.endmember_list[n].spectrum.data,
                    )
                    gg[name].attrs["index"] = n
                g.create_dataset("fractions", data=res.unmixed_image.fracs)
                g.create_dataset("residuals", data=res.unmixed_image.res)
                g.create_dataset("model", data=res.unmixed_image.model)
                g.create_dataset("rsquared", data=res.rsquared)
        case SaveMode.SMA:
            raise NotImplementedError(
                "Saving to .sma has not been implemented."
            )
        case SaveMode.CSV:
            raise NotImplementedError(
                "Saving to .csv has not been implemented."
            )


def load_model_result(p: PathLike, model_name: str):
    with h5.File(p) as f:
        g = f[model_name]
        endmember_list_with_idx = [
            [
                EndMember(
                    name,
                    Spectrum(dat[...], g.attrs["wavelengths"]),  # type: ignore
                ),
                dat.attrs["index"][...],  # type: ignore
            ]
            for (name, dat) in g["endmembers"].items()  # type: ignore
        ]
        endmember_list_sorted = [
            i[0] for i in sorted(endmember_list_with_idx, key=lambda x: x[1])
        ]

        endmember_grp = EndMemberGroup(endmember_list_sorted)

        return ModelResult(
            p,
            model_name,
            UnMixedCube(
                g["model"][...],  # type: ignore
                g["fractions"][:, :, :-1],  # type: ignore
                g["residuals"][...],  # type: ignore
            ),
            endmember_grp,
            g["rsquared"][...],  # type: ignore
        )


def write_model_to_gis(
    model: ModelResult,
    geotransform: GeotransformType,
    crs: str,
    save_directory: str | Path,
    name_prefix: Optional[str] = None,
):
    profile = {
        "driver": "ENVI",
        "height": model.unmixed_image.fracs.shape[0],
        "width": model.unmixed_image.fracs.shape[1],
        "count": model.unmixed_image.fracs.shape[2],
        "transform": geotransform,
        "crs": CRS.from_wkt(crs),
        "dtype": "float32",
        "nodata": -999,
    }

    if name_prefix is not None:
        file_name = f"{name_prefix}_"
    else:
        file_name = f"{model.modelID}_"
    with rio.open(
        Path(save_directory, f"{file_name}fractions").with_suffix(".bsq"),
        "w",
        **profile,
    ) as f:
        for n in range(model.unmixed_image.fracs.shape[-1]):
            f.write(model.unmixed_image.fracs[:, :, n], n + 1)
    with open(
        Path(save_directory, f"{file_name}fractions").with_suffix(".hdr"), "a"
    ) as f:
        f.write("band_names = {\n")
        for i in model.endmembers.endmember_name_list:
            f.write(f"    {i},\n")
        f.write("}")

    profile["count"] = 1
    with rio.open(
        Path(save_directory, f"{file_name}residual").with_suffix(".bsq"),
        "w",
        **profile,
    ) as f:
        f.write(model.rsquared, 1)
