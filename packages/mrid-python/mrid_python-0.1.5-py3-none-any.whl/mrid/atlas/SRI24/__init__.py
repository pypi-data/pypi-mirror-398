"""This subpackage allows one to download SRI-24 brain atlas files from https://www.nitrc.org/projects/sri24/.

The SRI24 atlas is licensed under the terms of the

  Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)

license (https://creativecommons.org/licenses/by-...).

In publications using the SRI24 atlas, please cite the following paper:

  T. Rohlfing, N.M. Zahr, E.V. Sullivan, A. Pfefferbaum, "The SRI24
  Multichannel Atlas of Normal Adult Human Brain Structure," Human
  Brain Mapping, vol. 31, no. 5, pp. 798-819, 2010.

  http://dx.doi.org/10.1002/hbm.20906

"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Literal

__all__ = [
    "get_sri24",
]

_ROOT = Path(os.path.dirname(__file__))

_sri24_url = "https://www.nitrc.org/frs/download.php/4841/sri24_spm8.zip//?i_agree=1&download_now=1"

def _download_sri24() -> None:
    import requests

    response = requests.get(_sri24_url, stream=True, timeout=30)
    response.raise_for_status()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        with open(tmpdir / "sri24_spm8.zip", 'wb') as file:
            shutil.copyfileobj(response.raw, file) # type:ignore

        shutil.unpack_archive(tmpdir / "sri24_spm8.zip", tmpdir / "sri24_spm8")

        for file in os.listdir(tmpdir / "sri24_spm8" / "templates"):
            shutil.copyfile(tmpdir / "sri24_spm8" / "templates" / file, _ROOT / file)


def get_sri24(type: Literal["EPI", "EPI_brain", "PD", "PD_brain", "T1", "T1_brain", "T2", "T2_brain"]) -> str:
    """Returns path to .nii file of specified SRI-24 template. Templates are downloaded if they haven't been downloaded already.

    The following templates are available:
    - `"T1"`: post-contrast T1-weighted MRI with skull;
    - `"T1_brain"`: post-contrast T1-weighted MRI without skull;
    - `"T2"`: T2-weighted MRI with skull;
    - `"T2_brain"`: T2-weighted MRI without skull;
    - `"EPI"`: echo-planar imaging MRI with skull;
    - `"EPI_brain"`: echo-planar imaging MRU without skull;
    - `"PD"`: proton density weighted spin-echo imaging MRI with skull;
    - `"PD_brain"`: proton density weighted spin-echo imaging MRI without skull;

    """
    filename = f"{type}.nii"
    if filename in os.listdir(_ROOT):
        return str(_ROOT / filename)

    print("SRI24 will be downloaded from https://www.nitrc.org/projects/sri24/, this may take a few minutes.")
    _download_sri24()

    if filename not in os.listdir(_ROOT):
        raise RuntimeError(
            f"Failed to download {filename}; try downloading it manually from https://www.nitrc.org/projects/sri24/, "
            "then unpack the zip file, open it, open `templates` folder, you will see files such as `EPI.nii`. "
            f"Copy all of those files to {_ROOT}."
        )

    return str(_ROOT / filename)