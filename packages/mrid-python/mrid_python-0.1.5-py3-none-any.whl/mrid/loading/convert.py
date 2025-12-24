import importlib.util
import os
from typing import TYPE_CHECKING, TypeAlias

import numpy as np
import SimpleITK as sitk

from ..utils.torch_utils import TORCH_INSTALLED

if TYPE_CHECKING:
    import torch

PREFER_DCM2NIIX = False
ImageLike: TypeAlias = "np.ndarray | sitk.Image | torch.Tensor | str | os.PathLike"

def read_dicoms(dir: str | os.PathLike) -> sitk.Image:
    """reads a directory of DICOM files and returns a ``sitk.Image``"""
    # load with dcm2niix
    if PREFER_DCM2NIIX and importlib.util.find_spec("dcm2niix") is not None:
        from ..utils.dcm2niix import dcm2sitk
        return dcm2sitk(dir)

    # load with SimpleITK
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(str(dir))

    if not dicom_names:
        raise FileNotFoundError(f"No DICOM series found in directory: {dir}")

    reader.SetFileNames(dicom_names)
    return reader.Execute()

def _read_sitk(path: str | os.PathLike) -> sitk.Image:
    if os.path.isfile(path): return sitk.ReadImage(str(path))
    if os.path.isdir(path): return read_dicoms(str(path))
    raise FileNotFoundError(f"{path} doesn't exist")

def tositk(x: ImageLike) -> sitk.Image:
    """Load an image into an ``sitk.Image`` object.
    ``x`` can be a numpy array, a ``sitk.Image``, a ``torch.Tensor`` or a string (path to an image file)."""
    if isinstance(x, np.ndarray): return sitk.GetImageFromArray(x)
    if isinstance(x, sitk.Image): return x
    if isinstance(x, (str, os.PathLike)): return _read_sitk(x)
    if TORCH_INSTALLED:
        import torch
        if isinstance(x, torch.Tensor): return sitk.GetImageFromArray(x.numpy())
    raise TypeError(f"Unsupported type {type(x)}")

def tonumpy(x: ImageLike) -> np.ndarray:
    """Load an image into a numpy.ndarray.
    ``x`` can be a numpy array, a ``sitk.Image``, a ``torch.Tensor`` or a string (path to an image file)."""
    if isinstance(x, np.ndarray): return x
    if isinstance(x, sitk.Image): return sitk.GetArrayFromImage(x)
    if isinstance(x, (str, os.PathLike)): return sitk.GetArrayFromImage(_read_sitk(x))
    if TORCH_INSTALLED:
        import torch
        if isinstance(x, torch.Tensor): return x.numpy()
    raise TypeError(f"Unsupported type {type(x)}")

def totensor(x: ImageLike) -> "torch.Tensor":
    """Load an image into a torch.Tensor.
    ``x`` can be a numpy array, a ``sitk.Image``, a ``torch.Tensor`` or a string (path to an image file)."""
    import torch
    if isinstance(x, np.ndarray): return torch.from_numpy(x)
    if isinstance(x, sitk.Image): return torch.from_numpy(sitk.GetArrayFromImage(x))
    if isinstance(x, (str, os.PathLike)): return  torch.from_numpy(sitk.GetArrayFromImage(_read_sitk(x)))
    if isinstance(x, torch.Tensor): return x
    raise TypeError(f"Unsupported type {type(x)}")