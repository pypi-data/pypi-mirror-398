"""
To install synthstrip, go to https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/
and find the "SynthStrip Tool" section.

If you have FreeSurfer installed, you just need to find path to the "mri_synthstrip" file.

If you do not want to install FreeSurfer, you can run SynthStrip in a container.
The webpage has two commands, one for Apptainer/Singularity, and one for Docker.
Pick one and run it, this will download a script file which installs synthstrip container
if it isn't installed, and provides a command-line interface for it.

Pass path to the script to mrid functions in this module.
"""
import os
import subprocess
import tempfile
from collections.abc import Mapping

import SimpleITK as sitk

from ..loading import ImageLike, tositk
from .mask import apply_mask, expand_binary_mask

# Running SynthStrip version 1.8 from Docker
# usage: mri_synthstrip [-h] -i FILE [-o FILE] [-m FILE] [-d FILE] [-g]
#                       [-b BORDER] [-t THREADS] [-f FILL] [--no-csf]
#                       [--model FILE]

# Robust, universal skull-stripping for brain images of any type.

# options:
#   -h, --help            show this help message and exit
#   -i FILE, --image FILE
#                         input image to skullstrip
#   -o FILE, --out FILE   save stripped image to file
#   -m FILE, --mask FILE  save binary brain mask to file
#   -d FILE, --sdt FILE   save distance transform to file
#   -g, --gpu             use the GPU
#   -b BORDER, --border BORDER
#                         mask border threshold in mm, defaults to 1
#   -t THREADS, --threads THREADS
#                         PyTorch CPU threads, PyTorch default if unset
#   -f FILL, --fill FILL  BG fill value, defaults to min(image.min, 0)
#   --no-csf              exclude CSF from brain border
#   --model FILE          alternative model weights

# If you use SynthStrip in your analysis, please cite:
# ----------------------------------------------------
# SynthStrip: Skull-Stripping for Any Brain Image
# A Hoopes, JS Mora, AV Dalca, B Fischl, M Hoffmann
# NeuroImage 206 (2022), 119474
# https://doi.org/10.1016/j.neuroimage.2022.119474

# Website: https://synthstrip.io

def _verify_input(value, t: type, name: str):
    if value is not None:
        if not isinstance(value, t):
            raise TypeError(f"`{name}` should be {t} or None, got {type(value)}")

def run_synthstrip(
    synthstrip_script_path: str | os.PathLike,
    image: str | os.PathLike,
    out: str | os.PathLike | None,
    mask: str | os.PathLike | None = None,
    sdt: str | os.PathLike | None = None,
    gpu: bool | None = None,
    border: int | None = None,
    threads: int | None = None,
    fill: int | None = None,
    no_csf: bool | None = None,
    model: str | os.PathLike | None = None,
    verbose: bool = True,
):
    """Runs ``synthstrip`` command-line routine via ``subprocess.run``.

    Args:
        synthstrip_script_path (str | os.PathLike): path to synthstrip script.
        image (str | os.PathLike): input image to skullstrip.
        out (str | os.PathLike | None): save stripped image to file.
        mask (str | os.PathLike | None): save binary brain mask to file. Defaults to None.
        sdt (str | os.PathLike | None, optional): save distance transform to file. Defaults to None.
        gpu (bool | None, optional): use the GPU, defaults to False if unset.
        border (int | None, optional): mask border threshold in mm, defaults to 1 if unset.
        threads (int | None, optional): PyTorch CPU threads, PyTorch default if unset.
        fill (int | None, optional): BG fill value, defaults to min(image.min, 0) if unset.
        no_csf (bool | None, optional): exclude CSF from brain border.
        model (str | os.PathLike | None, optional): alternative model weights
    """
    # verify inputs that go into subprocess
    _verify_input(border, int, "border")
    _verify_input(threads, int, "threads")
    _verify_input(fill, int, "fill")

    command = [
        "python",
        os.path.normpath(synthstrip_script_path),
        "-i", os.path.normpath(image),
    ]

    if out is not None: command.extend(["-o", os.path.normpath(out)])
    if mask is not None: command.extend(["-m", os.path.normpath(mask)])
    if sdt is not None: command.extend(["-d", os.path.normpath(sdt)])
    if gpu is not None: command.append("-g")
    if border is not None: command.extend(["-b", f"{border}"])
    if threads is not None: command.extend(["-t", f"{threads}"])
    if fill is not None: command.extend(["-f", f"{fill}"])
    if no_csf is not None: command.append("--no_csf")
    if model is not None: command.extend(["--model", os.path.normpath(model)])

    # run
    if verbose:
        subprocess.run(command, check=True)
    else:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def predict_brain_mask(
    synthstrip_script_path: str | os.PathLike,
    image: ImageLike,
    gpu: bool | None = None,
    border: int | None = None,
    threads: int | None = None,
    model: str | os.PathLike | None = None,
    verbose: bool = True,
):
    """Returns brain mask of ``input`` predicted by ``synthstrip``.

    Args:
        synthstrip_script_path (str | os.PathLike): path to synthstrip script.
        image (ImageLike): image to predict brain mask of.
        gpu (bool | None, optional): use the GPU, defaults to False if unset.
        border (int | None, optional): mask border threshold in mm, defaults to 1 if unset.
        threads (int | None, optional): PyTorch CPU threads, PyTorch default if unset.
        model (str | os.PathLike | None, optional): alternative model weights
    """
    image = tositk(image)
    with tempfile.TemporaryDirectory() as tmpdir:
        sitk.WriteImage(image, os.path.join(tmpdir, "image.nii.gz"))

        run_synthstrip(
            synthstrip_script_path=synthstrip_script_path,
            image=os.path.join(tmpdir, "image.nii.gz"),
            out=None,
            mask=os.path.join(tmpdir, "synthstrip_mask.nii.gz"),
            gpu=gpu,
            border=border,
            threads=threads,
            model=model,
            verbose=verbose,
        )

        brain_mask = tositk(os.path.join(tmpdir, "synthstrip_mask.nii.gz"))

    return brain_mask

def skullstrip(
    synthstrip_script_path: str | os.PathLike,
    image: ImageLike,
    gpu: bool | None = None,
    border: int | None = None,
    threads: int | None = None,
    model: str | os.PathLike | None = None,
    expand: int = 0,
    verbose: bool = True,
):
    """Skullstrips ``input`` using synthstrip.

    Args:
        synthstrip_script_path (str | os.PathLike): path to synthstrip script.
        image (ImageLike): image to skullstrip.
        gpu (bool | None, optional): use the GPU, defaults to False if unset.
        border (int | None, optional): mask border threshold in mm, defaults to 1 if unset.
        threads (int | None, optional): PyTorch CPU threads, PyTorch default if unset.
        model (str | os.PathLike | None, optional): alternative model weights
        expand (int, optional):
            Positive values expand brain mask by this many pixels, meaning inner parts of the skull will be included;
            Negative values dilate brain mask by this many pixels, meaning outer parts of the brain will be excluded.

    Returns:
        _type_: _description_
    """
    image = tositk(image)

    mask = predict_brain_mask(
        synthstrip_script_path=synthstrip_script_path,
        image=image,
        gpu=gpu,
        border=border,
        threads=threads,
        model=model,
        verbose=verbose
    )
    if expand != 0:
        mask = expand_binary_mask(mask, expand=expand)

    return apply_mask(image, mask)



def skullstrip_D(
    synthstrip_script_path: str | os.PathLike,
    images: Mapping[str, ImageLike],
    key: str,
    gpu: bool | None = None,
    border: int | None = None,
    threads: int | None = None,
    model: str | os.PathLike | None = None,
    expand: int = 0,

    include_mask: bool = False,
    keep_original: bool = False,

    verbose: bool = True,

) -> dict[str, sitk.Image]:
    """Predicts brain mask of ``images[key]`` using synthstrip, then uses this mask to skull strip all values in ``images``.

    Args:
        synthstrip_script_path (str | os.PathLike): path to synthstrip script.
        images (Mapping[str, ImageLike]): dictionary of images that align with each other.
        key (str): key of the image to pass to HD-BET for brain mask prediction.
        gpu (bool | None, optional): use the GPU, defaults to False if unset.
        border (int | None, optional): mask border threshold in mm, defaults to 1 if unset.
        threads (int | None, optional): PyTorch CPU threads, PyTorch default if unset.
        model (str | os.PathLike | None, optional): alternative model weights
        expand (int, optional):
            Positive values expand brain mask by this many pixels, meaning inner parts of the skull will be included;
            Negative values dilate brain mask by this many pixels, meaning outer parts of the brain will be excluded.
        include_mask (bool, optional):
            if True, adds ``"seg_synthstrip"`` with brain mask predicted by HD-BET to returned dictionary.
            This adds brain mask BEFORE expanding/dilating if ``expand`` argument is specified.
        keep_original (bool, Optional):
            if True, skull-stripped images are added to the dictionary
            with ``"_synthstrip" ``postfix, rather than replacing.

    """
    images = {k: tositk(v) for k,v in images.items()}

    mask = predict_brain_mask(
        synthstrip_script_path=synthstrip_script_path,
        image=images[key],
        gpu=gpu,
        border=border,
        threads=threads,
        model=model,
        verbose=verbose,
    )
    skullstripped = {}

    # include mask before expanding
    if include_mask:
        mask_sitk = tositk(mask)
        mask_sitk.CopyInformation(images[key])
        skullstripped["seg_synthstrip"] = mask_sitk

    # expand
    if expand != 0:
        mask = expand_binary_mask(mask, expand=expand)

    # apply mask
    for k,v in images.items():
        skullstripped[k] = apply_mask(v, mask)

    # optionally add with skullstripped postfix
    if keep_original:
        skullstripped = {(f"{k}_synthstrip" if k != "seg_synthstrip" else k): v for k,v in skullstripped.items()}
        skullstripped.update(images.copy())

    return skullstripped

