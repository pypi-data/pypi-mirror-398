import os
import subprocess
import tempfile
from collections.abc import Mapping
from typing import Literal

import SimpleITK as sitk

from ..loading.convert import ImageLike, tositk
from ..utils.torch_utils import CUDA_IF_AVAILABLE
from .simple_elastix import register, register_D
from .mask import expand_binary_mask, apply_mask

# hd_bet -h

# -i INPUT, --input INPUT
#                         input. Can be either a single file name or an input folder. If file: must be nifti (.nii.gz) and can only be 3D. No support for 4d images, use fslsplit to split 4d sequences into 3d images. If folder: all files ending with .nii.gz within that folder will be brain extracted.
# -o OUTPUT, --output OUTPUT
#                         output. Can be either a filename or a folder. If it does not exist, the folder will be created
# -device DEVICE        used to set on which device the prediction will run. Can be 'cuda' (=GPU), 'cpu' or 'mps'. Default: cuda
# --disable_tta         Set this flag to disable test time augmentation. This will make prediction faster at a slight decrease in prediction quality. Recommended for device cpu
# --save_bet_mask       Set this flag to keep the bet masks. Otherwise they will be removed once HD_BET is done
# --no_bet_image        Set this flag to disable generating the skull stripped/brain extracted image. Only makes sense if you also set --save_bet_mask
# --verbose             Talk to me.

def run_hd_bet(
    input: str | os.PathLike,
    output: str | os.PathLike,
    device: Literal['cpu', 'cuda', 'mps'] = CUDA_IF_AVAILABLE,
    disable_tta: bool = False,
    save_bet_mask: bool = True,
    no_bet_image: bool = False,
    verbose: bool = False,
) -> None:
    """Runs HD-BET command-line routine via ``subprocess.run``.

    Args:
        input (str | os.PathLike):
            input. Can be either a single file name or an input folder.
            If file: must be nifti (.nii.gz) and can only be 3D.
            No support for 4d images, use fslsplit to split 4d sequences into 3d images.
            If folder: all files ending with .nii.gz within that folder will be brain extracted.
        output (str | os.PathLike):
            output. Can be either a filename or a folder. If it does not exist, the folder will be created
        device (str, optional):
            used to set on which device the prediction will run.
            Can be 'cuda' (=GPU), 'cpu' or 'mps'. Default: cuda. Defaults to CUDA_IF_AVAILABLE.
        disable_tta (bool, optional):
            Set this flag to disable test time augmentation.
            This will make prediction faster at a slight decrease in prediction quality.
            Recommended for device cpu. Defaults to False.
        save_bet_mask (bool, optional):
            Set this flag to keep the bet masks.
            Otherwise they will be removed once HD_BET is done. Defaults to True.
        no_bet_image (bool, optional):
            Set this flag to disable generating the skull stripped/brain extracted image.
            Only makes sense if you also set --save_bet_mask. Defaults to False.
        verbose (bool, optional): Talk to me. Defaults to False.
    """

    command = [
        "hd-bet",
        "-i", os.path.normpath(input),
        "-o", os.path.normpath(output),
        "-device", device,
    ]
    if disable_tta: command.append("--disable_tta")
    if save_bet_mask: command.append("--save_bet_mask")
    if no_bet_image: command.append("--no_bet_image")
    if verbose: command.append("--verbose")

    # run dcm2niix
    subprocess.run(command, check=True)


def predict_brain_mask(
    input: ImageLike,
    register_to_mni152: Literal["T1", "T2"] | None = None,
    device: Literal["cpu", "cuda", "mps"] = CUDA_IF_AVAILABLE,
    disable_tta: bool = False,
    verbose: bool = False,
) -> sitk.Image:
    """Returns brain mask of ``input`` predicted by HD-BET.

    Args:
        input (ImageLike): input to skullstrip. Recommended T1-w, postcontrast T1-w, T2-w or FLAIR sequence in MNI152 space.
        register_to_mni152 (str | None, optional):
            Modality of MNI152 template to pre-register ``input`` to. Should be ``"T1"``, ``"T2"`` or ``None``.
            if specified, ``input`` will be registered to specified MNI152 template,
            then after prediction the brain mask registered back to original ``input``.
            Note that HD-BET expects images to be in MNI152 space. Defaults to None.
        device (str, optional):
            used to set on which device the prediction will run. Can be 'cuda' (=GPU), 'cpu' or 'mps'.
            Defaults to CUDA_IF_AVAILABLE.
        disable_tta (bool, optional):
            Set this flag to disable test time augmentation.
            This will make prediction faster at a slight decrease in prediction quality.
            Recommended for device cpu. Defaults to False.
        verbose (bool, optional): Talk to me. Defaults to False.
    """
    input = tositk(input)

    # ---------------------------- register to mni152 ---------------------------- #
    if register_to_mni152 is not None:
        from ..atlas.MNI152 import get_mni152
        mni152 = get_mni152(f"2009a {register_to_mni152}w asymmetric", skullstripped=False) # type:ignore
        input_mni = register(input, mni152)

    else:
        input_mni = input

    # ---------------------------- predict brain mask ---------------------------- #
    with tempfile.TemporaryDirectory() as tmpdir:
        sitk.WriteImage(input_mni, os.path.join(tmpdir, "input.nii.gz"))

        run_hd_bet(
            input = os.path.join(tmpdir, "input.nii.gz"),
            output = os.path.join(tmpdir, "output.nii.gz"),
            device=device, disable_tta=disable_tta, save_bet_mask=True, verbose=verbose,
        )

        brain_mask_mni = tositk(os.path.join(tmpdir, "output_bet.nii.gz"))

    # ------------------------- unregister mask if needed ------------------------ #
    if register_to_mni152 is not None:
        study_mni = dict(image=input_mni, seg_brain=brain_mask_mni)
        study = register_D(study_mni, key="image", to=input)
        brain_mask = study["seg_brain"]

    else:
        brain_mask = brain_mask_mni

    return brain_mask

def skullstrip(
    input: ImageLike,
    register_to_mni152: Literal["T1", "T2"] | None = None,
    device: Literal["cpu", "cuda", "mps"] = CUDA_IF_AVAILABLE,
    disable_tta: bool = False,
    verbose: bool = False,

    expand: int = 0,
) -> sitk.Image:
    """Skullstrips ``input`` using HD-BET.

    Args:
        input (ImageLike): input to skullstrip. Recommended T1-w, postcontrast T1-w, T2-w or FLAIR sequence in MNI152 space.
        register_to_mni152 (str | None, optional):
            Modality of MNI152 template to pre-register ``input`` to. Should be ``"T1"``, ``"T2"`` or ``None``.
            if specified, ``input`` will be registered to specified MNI152 template,
            then after prediction the brain mask registered back to original ``input``.
            Note that HD-BET expects images to be in MNI152 space. Defaults to None.
        device (str, optional):
            used to set on which device the prediction will run. Can be 'cuda' (=GPU), 'cpu' or 'mps'.
            Defaults to CUDA_IF_AVAILABLE.
        disable_tta (bool, optional):
            Set this flag to disable test time augmentation. This will make prediction faster
            at a slight decrease in prediction quality. Recommended for device cpu. Defaults to False.
        verbose (bool, optional): Talk to me. Defaults to False.
        expand (int, optional):
            Positive values expand brain mask by this many pixels, meaning inner parts of the skull will be included;
            Negative values dilate brain mask by this many pixels, meaning outer parts of the brain will be excluded.

    """
    input = tositk(input)
    mask = predict_brain_mask(input=input, register_to_mni152=register_to_mni152,
                                  device=device, disable_tta=disable_tta, verbose=verbose)

    if expand != 0:
        mask = expand_binary_mask(mask, expand=expand)

    return apply_mask(input, mask)


def skullstrip_D(
    images: Mapping[str, ImageLike],
    key: str,
    register_to_mni152: Literal["T1", "T2"] | None = None,
    device: Literal["cpu", "cuda", "mps"] = CUDA_IF_AVAILABLE,
    disable_tta: bool = False,
    verbose: bool = False,

    expand: int = 0,

    include_mask: bool = False,
    keep_original: bool = False,
) -> dict[str, sitk.Image]:
    """Predicts brain mask of ``images[key]`` using HD-BET, then uses this mask to skull strip all values in ``images``.

    Args:
        images (Mapping[str, ImageLike]): dictionary of images that align with each other.
        key (str): key of the image to pass to HD-BET for brain mask prediction.
        register_to_mni152 (str | None, optional):
            Modality of MNI152 template to pre-register ``input`` to. Should be ``"T1"``, ``"T2"`` or ``None``.
            if specified, ``input`` will be registered to specified MNI152 template,
            then after prediction the brain mask registered back to original ``input``.
            Note that HD-BET expects images to be in MNI152 space. Defaults to None.
        device (str, optional):
            used to set on which device the prediction will run. Can be 'cuda' (=GPU), 'cpu' or 'mps'.
            Defaults to CUDA_IF_AVAILABLE.
        disable_tta (bool, optional):
            Set this flag to disable test time augmentation. This will make prediction faster
            at a slight decrease in prediction quality. Recommended for device cpu. Defaults to False.
        verbose (bool, optional): Talk to me. Defaults to False.
        expand (int, optional):
            Positive values expand brain mask by this many pixels, meaning inner parts of the skull will be included;
            Negative values dilate brain mask by this many pixels, meaning outer parts of the brain will be excluded.
        include_mask (bool, optional):
            if True, adds ``"seg_seg_hd_bet"`` with brain mask predicted by HD-BET to returned dictionary.
            This adds brain mask BEFORE expanding/dilating if ``expand`` argument is specified.
        keep_original (bool, Optional):
            if True, skull-stripped images are added to the dictionary
            with ``"_hd_bet" ``postfix, rather than replacing.
    """
    images = {k: tositk(v) for k,v in images.items()}

    mask = predict_brain_mask(input=images[key], register_to_mni152=register_to_mni152,
                          device=device, disable_tta=disable_tta, verbose=verbose)

    skullstripped = {}

    # include mask before expanding
    if include_mask:
        mask_sitk = tositk(mask)
        mask_sitk.CopyInformation(images[key])
        skullstripped["seg_hd_bet"] = mask_sitk

    # expand
    if expand != 0:
        mask = expand_binary_mask(mask, expand=expand)

    # apply mask
    for k,v in images.items():
        skullstripped[k] = apply_mask(v, mask)

    # optionally add with skullstripped postfix
    if keep_original:
        skullstripped = {(f"{k}_hd_bet" if k != "seg_hd_bet" else k): v for k,v in skullstripped.items()}
        skullstripped.update(images.copy())

    return skullstripped

