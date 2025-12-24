import SimpleITK as sitk
import numpy as np

from ..loading.convert import ImageLike, tositk, tonumpy


def expand_binary_mask(binary_mask: ImageLike, expand: int) -> sitk.Image:
    """Expand or dilate a binary mask.

    Args:
        binary_mask (ImageLike): mask
        expand (int, optional):
            Positive values expand the mask by this many pixels;
            Negative values dilate the mask by this many pixels.
    """
    binary_mask = tositk(binary_mask)
    if expand < 0:
        inverted_mask = 1 - binary_mask
        return 1 - sitk.BinaryDilate(inverted_mask, (-expand, -expand, -expand))

    if expand > 0:
        return sitk.BinaryDilate(binary_mask, (expand, expand, expand))

    return binary_mask

def apply_mask(image: ImageLike, mask: ImageLike) -> sitk.Image:
    """Applies ``mask`` to ``image``, that is all values where ``mask > 0`` are kept.

    This function sets all values outside of the mask to smallest value within the mask."""
    image = tositk(image)
    mask = tositk(mask)

    mask = sitk.Cast(mask, image.GetPixelID())

    image_np = sitk.GetArrayFromImage(image)
    mask_np = (tonumpy(mask) > 0).astype(np.bool)
    image_ma = np.ma.masked_array(image_np, ~mask_np)

    image_applied = tositk(image_ma.filled(image_ma.min()))
    image_applied.CopyInformation(image)
    return image_applied