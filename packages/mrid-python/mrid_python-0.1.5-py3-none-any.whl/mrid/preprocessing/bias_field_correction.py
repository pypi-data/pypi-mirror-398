import SimpleITK as sitk
from ..loading.convert import tositk, ImageLike

def n4_bias_field_correction(image: ImageLike, shrink: int = 4) -> sitk.Image:
    """Perform N4 Bias Field Correction to correct low frequency intensity non-uniformity present in MRI image.

    Args:
        image (ImageLike): Input MRI image to be corrected. Can be any format supported by tositk conversion.
        shrink (int, optional): Shrink factor for reducing image size before correction to speed up computation.
                               Default is 4. If set to 1 or less, no shrinking is performed.

    """
    image = tositk(image)

    norm_image = sitk.RescaleIntensity(image, 0, 255)
    mask = sitk.OtsuThreshold(norm_image, 0, 1)

    if shrink > 1:
        reduced = sitk.Shrink(image, [shrink] * image.GetDimension())
        mask = sitk.Shrink(mask, [shrink] * mask.GetDimension())

    else: reduced = image

    corrector = sitk.N4BiasFieldCorrectionImageFilter()
    corrector.Execute(reduced, mask)
    log_bias_field = corrector.GetLogBiasFieldAsImage(image)

    return image / sitk.Cast(sitk.Exp(log_bias_field), image.GetPixelID())
