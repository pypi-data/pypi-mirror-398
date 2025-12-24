# https://zenodo.org/api/records/15470657/files-archive

import os
import shutil
import tempfile
from pathlib import Path
from typing import Literal

__all__ = [
    "get_mni152",
]

_ROOT = Path(os.path.dirname(__file__))

_URLS = {
    "2006 T1w symmetric": (
        "https://zenodo.org/records/15470657/files/icbm_mni152_t1_06_sym.nii.gz?download=1",
        "https://zenodo.org/records/15470657/files/icbm_mni152_t1_06_sym_bet.nii.gz?download=1",
    ),
    "2009a T1w symmetric": (
        "https://zenodo.org/records/15470657/files/icbm_mni152_t1_09a_sym.nii.gz?download=1",
        "https://zenodo.org/records/15470657/files/icbm_mni152_t1_09a_sym_bet.nii.gz?download=1",
    ),
    "2009a T2w symmetric": (
        "https://zenodo.org/records/15470657/files/icbm_mni152_t2_09a_sym.nii.gz?download=1",
        "https://zenodo.org/records/15470657/files/icbm_mni152_t2_09a_sym_bet.nii.gz?download=1",
    ),
    "2009a T1w asymmetric": (
        "https://zenodo.org/records/15470657/files/icbm_mni152_t1_09a_asym.nii.gz?download=1",
        "https://zenodo.org/records/15470657/files/icbm_mni152_t1_09a_asym_bet.nii.gz?download=1",
    ),
    "2009a T2w asymmetric": (
        "https://zenodo.org/records/15470657/files/icbm_mni152_t2_09a_asym.nii.gz?download=1",
        "https://zenodo.org/records/15470657/files/icbm_mni152_t2_09a_asym_bet.nii.gz?download=1",
    ),
}

_mni152_url = "https://zenodo.org/records/15470657/files/icbm_mni152_t1_06_sym_bet.nii.gz?download=1"

def _download_template(type: str, bet:bool):
    filename = f"{type} {bool(bet)}.nii.gz"
    if filename in os.listdir(_ROOT):
        raise RuntimeError(f"Template {type} is already downloaded")

    import requests

    response = requests.get(_URLS[type][bet], stream=True, timeout=30)
    response.raise_for_status()

    with open(_ROOT / f"{filename}", 'wb') as file:
        shutil.copyfileobj(response.raw, file) # type:ignore

def get_mni152(
    type: Literal[
        "2006 T1w symmetric",
        "2009a T1w symmetric",
        "2009a T2w symmetric",
        "2009a T1w asymmetric",
        "2009a T2w asymmetric",
    ],
    skullstripped: bool = False,
):
    """Returns path to .nii.gz file of specified MNI-152 template.

    The following templates are available:
    - ``"2006 T1w symmetric"``
    - ``"2009a T1w symmetric"``
    - ``"2009a T2w symmetric"``
    - ``"2009a T1w asymmetric"``
    - ``"2009a T2w asymmetric"``

    Descriptions of templates are available here https://zenodo.org/records/15470657
    """
    filename = f"{type} {bool(skullstripped)}.nii.gz"

    if filename in os.listdir(_ROOT):
        return str(_ROOT / filename)

    print(f"{filename} will be downloaded from https://zenodo.org/records/15470657, this may take a few minutes.")
    _download_template(type, skullstripped)

    if filename not in os.listdir(_ROOT):
        raise RuntimeError(
            f"Failed to download {filename}; try downloading it manually from https://zenodo.org/records/15470657"
        )

    return str(_ROOT / filename)