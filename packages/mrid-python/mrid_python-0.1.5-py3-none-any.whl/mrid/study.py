import os
import pickle
import shutil
import tempfile
import warnings
from collections import UserDict
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, overload

import numpy as np
import SimpleITK as sitk

from . import preprocessing
from .loading.convert import ImageLike, tonumpy, tositk, totensor
from .utils.torch_utils import CUDA_IF_AVAILABLE

if TYPE_CHECKING:
    import torch

def _identity(x): return x

class Study(UserDict[str, sitk.Image | Any]):
    """A dictionary of scans, segmentations and other info.

    Segmentations should have keys starting with ``"seg"``, for example ``"seg_tumor"``.
    Segmentation should NOT be one-hot encoded.

    Non-image values should have keys starting with ``"info"``, for example ``"info_id=12345"``.

    You can pass:
    - path to file to be opened with SimpleITK (e.g. nii/nii.gz);
    - path to a DICOM dir, make sure it contains one series.
    - ``sitk.Image``
    - ``np.ndarray``
    - ``torch.Tensor``.

    Everything except info will be converted to ``sitk.Image``.

    Please note that multi-channel scans are currently not supported.
    """
    @overload
    def __init__(self, /, **kwargs): ...
    @overload
    def __init__(self, dict, /): ...
    def __init__(self, dict=None, /, **kwargs):
        if dict is None: dict = kwargs

        proc = {}
        for k,v in dict.items():
            if k.startswith("info"):
                proc[k] = v
            else:
                proc[k] = tositk(v)

        super().__init__(proc)

    def __setitem__(self, key: str, item: "ImageLike | Any") -> None:
        if not key.startswith("info"): item = tositk(item)
        return super().__setitem__(key, item)

    def add(self, key: str, item: "ImageLike | Any", reference_key: str | None = None):
        """Returns a new study with an extra item inserted under ``key``.

        Args:
            key (str): Key to insert new item under.
            item (ImageLike | Any): Item to insert.
            reference_key (str | None, optional):
                if specified, ``item`` will have SimpleITK attributes copied from ``self[reference_key]``. Defaults to None.
        """
        study = self.copy()
        if key.startswith('info'):
            if reference_key: raise RuntimeError(f"Can't copy sitk attributes for an non-image item {key}")
            study[key] = item
            return study

        item = tositk(item)
        if reference_key is not None: item.CopyInformation(study[reference_key])
        study[key] = item
        return study

    def remove(self, *keys: str | Sequence[str]):
        """Returns a new study without specified keys"""
        keys_proc = []
        for k in keys:
            if isinstance(k, str): keys_proc.append(k)
            else: keys_proc.extend(k)

        study = self.copy()
        for k in keys_proc:
            del study[k]

        return study

    def get_scans(self):
        """Returns a new ``Study`` with segmentations and info removed."""
        return self.__class__({k:v for k,v in self.items() if not k.startswith(("seg", "info"))})

    def get_images(self):
        """Returns a new ``Study`` with info removed."""
        return self.__class__({k:v for k,v in self.items() if not k.startswith("info")})

    def get_segmentations(self):
        """Returns a new ``Study`` with scans and info removed."""
        return self.__class__({k:v for k,v in self.items() if k.startswith("seg")})

    def get_info(self):
        """Returns a new ``Study`` with scans and segmentations removed."""
        return self.__class__({k:v for k,v in self.items() if k.startswith("info")})

    def apply(self, fn:Callable[[sitk.Image], sitk.Image] | None, seg_fn: Callable[[sitk.Image], sitk.Image] | None,) -> "Study":
        """Returns a new ``Study`` with ``fn`` applied to scans and ``seg_fn`` applied to segmentations.

        Args:
            fn: Function to apply to scan images. Must take and return ``sitk.Image``.
                If None, identity function is used.
            seg_fn: Function to apply to segmentation images. Must take and return ``sitk.Image``.
                If None, identity function is used.
        """
        if fn is None: fn = _identity
        if seg_fn is None: seg_fn = _identity

        scans = {k: fn(v) for k,v in self.get_scans().items()}
        seg = {k: seg_fn(v) for k,v in self.get_segmentations().items()}

        return Study(**scans, **seg, **self.get_info())

    def cast(self, dtype) -> "Study":
        """Returns a new study with all scans cast to the specified SimpleITK dtype.

        Note:
            This operation does not affect segmentations.
        """
        return self.apply(partial(sitk.Cast, pixelID=dtype), seg_fn=None)

    def cast_float64(self) -> "Study":
        """Returns a new study with all scans cast to float64.

        Note:
            This operation does not affect segmentations.
        """
        return self.cast(sitk.sitkFloat64)

    def cast_float32(self) -> "Study":
        """Returns a new study with all scans cast to float32.

        Note:
            This operation does not affect segmentations.
        """
        return self.cast(sitk.sitkFloat32)

    def normalize(self) -> "Study":
        """Returns a new study where all scans are separately z-normalized to 0 mean and 1 variance.

        Note:
            This operation does not affect segmentations.
        """
        return self.apply(sitk.Normalize, seg_fn=None)

    def rescale_intensity(self, min: float, max: float) -> "Study":
        """Returns a new study where all scans are separately rescaled to the specified intensity range.

        Args:
            min: Minimum value for the output intensity range.
            max: Maximum value for the output intensity range.
        """
        return self.apply(partial(sitk.RescaleIntensity, outputMinimum = min, outputMaximum = max), seg_fn=None) # type:ignore

    def crop_bg(self, key: str) -> "Study":
        """Returns a new study with cropped black background. Finds the foreground bounding box of ``study[key]``,
        and uses that bounding box to crop all other images, including segmentations.

        Args:
            key: The key of the image (scan or segmentation) to use for finding the foreground bounding box.
        """
        d = preprocessing.cropping.crop_bg_D(self.get_images(), key)
        return Study(**d, **self.get_info())

    def skullstrip_hd_bet(
        self,
        key: str,
        register_to_mni152: Literal["T1", "T2"] | None = None,
        device: Literal["cpu", "cuda", "mps"] = CUDA_IF_AVAILABLE,
        disable_tta: bool = False,
        verbose: bool = False,

        expand: int = 0,

        include_mask: bool = False,
        keep_original: bool = False,

    ) -> "Study":
        """Returns a new study with all scans skullstripped.

        This predicts brain mask of ``study[key]`` via HD-BET,
        then uses this mask to skullstrip all scans. Doesn't affect segmentations.

        Args:
            key: Key of the image to pass to HD-BET for brain mask prediction.
            register_to_mni152:
                Modality of MNI152 template to pre-register ``study[key]`` to. Should be ``"T1"``, ``"T2"`` or ``None``.
                If specified, ``input`` will be registered to specified MNI152 template,
                then after prediction the brain mask registered back to original ``input``.
                Note that HD-BET expects images to be in MNI152 space. Defaults to None.
            device:
                Used to set on which device the prediction will run. Can be 'cuda' (=GPU), 'cpu' or 'mps'.
                Defaults to CUDA_IF_AVAILABLE.
            disable_tta:
                Set this flag to disable test time augmentation. This will make prediction faster
                at a slight decrease in prediction quality. Recommended for device cpu. Defaults to False.
            verbose (bool, optional): Talk to me. Defaults to False.
            expand (int, optional):
                Positive values expand brain mask by this many pixels, meaning inner parts of the skull will be included;
                Negative values dilate brain mask by this many pixels, meaning outer parts of the brain will be excluded.
            include_mask (bool, optional):
                if True, adds ``"seg_hd_bet"`` with brain mask predicted by HD-BET to returned dictionary.
                This adds brain mask BEFORE expanding/dilating if ``expand`` argument is specified.
            keep_original (bool, Optional):
                if True, skull-stripped images are added to the returned study with ``"_hd_bet"`` postfix,
                and do not replace original images.
        """
        d = preprocessing.hd_bet.skullstrip_D(
            images=self.get_scans(),
            key=key,
            register_to_mni152=register_to_mni152,
            device=device,
            disable_tta=disable_tta,
            verbose=verbose,
            include_mask=include_mask,
            keep_original=keep_original,
            expand=expand,
        )
        return Study(**d, **self.get_segmentations(), **self.get_info())

    def skullstrip_synthstrip(
        self,
        synthstrip_script_path: str | os.PathLike,
        key: str,
        gpu: bool | None = None,
        border: int | None = None,
        threads: int | None = None,
        model: str | os.PathLike | None = None,
        expand: int = 0,

        include_mask: bool = False,
        keep_original: bool = False,

        verbose: bool = True,
    ):
        """Returns a new study with all scans skullstripped.

        This predicts brain mask of ``study[key]`` via synthstrip,
        then uses this mask to skullstrip all scans. Doesn't affect segmentations.

        Args:
            synthstrip_script_path (str | os.PathLike): path to synthstrip script.
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
        d = preprocessing.synthstrip.skullstrip_D(
            synthstrip_script_path=synthstrip_script_path,
            images=self.get_scans(),
            key=key,
            gpu=gpu, border=border, threads=threads, model=model,
            expand=expand, include_mask=include_mask, keep_original=keep_original,
            verbose=verbose,
        )
        return Study(**d, **self.get_segmentations(), **self.get_info())

    def resize(self, size: Sequence[int], interpolator=sitk.sitkLinear):
        """Returns a new study with all images resized to to ``size``.

        Args:
            size: Target size as a sequence of integers (e.g., [height, width, depth]).
            interpolator: Interpolation method for scans (segmentations always use nearest neighbor).
        """
        return self.apply(
            partial(preprocessing.resize, new_size=size, interpolator=interpolator,),
            partial(preprocessing.resize, new_size=size, interpolator=sitk.sitkNearestNeighbor,),
        )

    def downsample(self, factor: float, dims = None, interpolator=sitk.sitkLinear):
        """Returns a new study with all images downsampled by ``factor`` along ``dims``.
        For example, ``factor=2`` for 2x downsampling.
        Set ``dims`` to ``None`` to downsample along all dimensions.

        Args:
            factor: Downsampling factor (e.g., 2 for 2x downsampling).
            dims: Specific dimensions to downsample, or None for all dimensions.
            interpolator: Interpolation method for scans (segmentations always use nearest neighbor).
        """
        return self.apply(
            partial(preprocessing.downsample, factor=factor, dims=dims, interpolator=interpolator,),
            partial(preprocessing.downsample, factor=factor, dims=dims, interpolator=sitk.sitkNearestNeighbor,),
        )

    def register_SE(self, key: str, to: ImageLike, pmap=None, log_to_console=False) -> "Study":
        """Returns a new Study.
        Registers ``study[key]`` to ``to`` via SimpleElastix,
        and use transformation parameters to register all other images including segmentation.
        This assumes that all images are aligned, if they are not, use ``register_many`` method.

        Args:
            key: The key of the image to use as reference for registration.
            to: Target image or path to register to.
            pmap: Parameter map for registration. If None, uses default parameters.
            log_to_console: Whether to log registration progress to console.
        """
        d = preprocessing.simple_elastix.register_D(
            images=self.get_images(),
            key=key,
            to=to,
            pmap=pmap,
            log_to_console=log_to_console,
        )
        return Study(**d, **self.get_info())

    def register_each_SE(self, key: str, to: "ImageLike | None" = None, pmap=None, log_to_console=False) -> "Study":
        """Returns a new study.
        Registers all other images to ``study[key]``.
        If ``to`` is specified, register ``study[key]`` to ``to`` beforehand.
        Uses SimpleElastix.

        Args:
            key: The key of the image to use as reference for registration.
            to: Target image or path to register the reference image to. If None, uses key as reference.
            pmap: Parameter map for registration. If None, uses default parameters.
            log_to_console: Whether to log registration progress to console.

        Note:
            If called on a study with segmentations, they will be removed from the returned study.
        """
        if len(self.get_segmentations()) > 0:
            keys = ', '.join(self.get_segmentations().keys())
            warnings.warn(f"`register_many` was called on a study with segmentations ({keys}), "
                          "they will be removed from the returned study", stacklevel=3)

        d = self.get_scans()
        if to is not None:
            d[key] = preprocessing.simple_elastix.register(d[key], to=to, pmap=pmap, log_to_console=log_to_console)

        for k in d:
            if k != key:
                d[k] = preprocessing.simple_elastix.register(d[k], to=d[key], pmap=pmap, log_to_console=log_to_console)

        return Study(**d, **self.get_info())

    def resample_to(self, to: "np.ndarray | sitk.Image | torch.Tensor | str", interpolation=sitk.sitkLinear) -> "Study":
        """Returns a new study with all images including segmentation resampled to ``to``.
        Segmentation always uses nearest interpolation"""
        to = tositk(to)

        return self.apply(
            partial(preprocessing.resample_to, to=to, interpolation=interpolation),
            partial(preprocessing.resample_to, to=to, interpolation=sitk.sitkNearestNeighbor),
        )

    def n4_bias_field_correction(self, key: str, shrink: int = 4, postfix: str = "") -> "Study":
        """Returns a new study with corrected bias field of the image under ``key``. Doesn't affect other images.

        Args:
            key (str): The key of the image for which to correct the bias field.
            shrink (int, optional): By how many times to shrink the size of input image for calculating the bias field.
                The bias field is then applied to original size (unshrunk) image.
                Setting shrink to 1 disables it, but n4 algorithm may take several minutes.
                Setting it to ~4 is good enough in most cases and will be significantly faster (usually few seconds).
            postfix (str, optional):
                if specified, N4-corrected image is added to returned study with specified postfix rather than
                replacing current ``key``.
        """
        new = self.copy()
        new[f"{key}{postfix}"] = preprocessing.bias_field_correction.n4_bias_field_correction(new[key], shrink=shrink)
        return new

    def expand_binary_mask(self, key: str, expand: int, postfix: str = ""):
        """Returns a new study with binary mask under ``key`` expanded or dilated by ``expand`` pixels.

        Args:
            key (str): The key of the mask to expand/dilate.
            expand (int, optional):
                Positive values expand the mask by this many pixels;
                Negative values dilate the mask by this many pixels.
            postfix (str, optional):
                if specified, expanded/dilated mask is added to returned study with specified postfix rather than
                replacing current ``key``.
        """
        new = self.copy()
        new[f"{key}{postfix}"] = preprocessing.mask.expand_binary_mask(new[key], expand=expand)
        return new

    def remove_small_objects(
        self,
        key: str,
        min_size=64,
        connectivity=1,
        independent_channels: bool = False,
        postfix: str = "",
    ):
        """Returns a new study with small objects removed in mask under ``key``,
        this uses ``skimage.morphology.remove-small-objects`` or
        ``monai.transforms.remove_small_objects``.

        See: https://scikit-image.org/docs/dev/api/skimage.morphology.html#remove-small-objects.

        Args:
            key (str): The key of the mask to remove small objects in.
            min_size (int, optional): objects smaller than this size are removed. Defaults to 64.
            connectivity (int, optional):
                Maximum number of orthogonal hops to consider a pixel/voxel as a neighbor.
                Accepted values are ranging from 1 to input.ndim.
                If None, a full connectivity of input.ndim is used.
                For more details refer to linked scikit-image documentation. Defaults to 1.
            independent_channels (bool, optional):
                Whether to consider each channel independently (requires monai). Defaults to False.
            postfix (str, optional):
                if specified, processed mask is added to returned study with specified postfix rather than
                replacing current ``key``.
        """
        arr = self.numpy(key)

        if independent_channels:
            from monai.transforms import remove_small_objects
            # Data should be one-hotted.
            num_classes = arr.max() + 1
            one_hot = np.zeros((num_classes, *arr.shape))
            i, j, k = np.indices(arr.shape)
            one_hot[arr[i,j,k], i, j, k] = 1
            one_hot = remove_small_objects(
                one_hot, min_size=min_size, connectivity=connectivity, independent_channels=independent_channels)
            arr = one_hot.argmax(0)
            return self.add(f'{key}{postfix}', arr, reference_key=key)

        from skimage.morphology import remove_small_objects
        binary = (arr != 0)
        arr *= remove_small_objects(binary, min_size=min_size, connectivity=connectivity)
        return self.add(f'{key}{postfix}', arr, reference_key=key)

    def keep_largest_connected_component(self, key: str, applied_labels=None, independent=True, connectivity=None, num_components=1, postfix: str = ""):
        """Returns a new study with largest components kept in mask under ``key``,
        this uses ``monai.transforms.KeepLargestConnectedComponent``.

        Args:
            key (str): The key of the mask to remove keep largest components in.
            applied_labels: Labels for applying the connected component analysis on.
                If given, voxels whose value is in this list will be analyzed.
                If `None`, all non-zero values will be analyzed.
            independent: whether to treat ``applied_labels`` as a union of foreground labels.
                If ``True``, the connected component analysis will be performed on each foreground label independently
                and return the intersection of the largest components.
                If ``False``, the analysis will be performed on the union of foreground labels.
                default is `True`.
            connectivity: Maximum number of orthogonal hops to consider a pixel/voxel as a neighbor.
                Accepted values are ranging from  1 to input.ndim. If ``None``, a full
                connectivity of ``input.ndim`` is used. for more details:
                https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.label.
            num_components: The number of largest components to preserve.
            postfix (str, optional):
                if specified, processed mask is added to returned study with specified postfix rather than
                replacing current ``key``.
        """
        from monai.transforms import KeepLargestConnectedComponent
        tfm = KeepLargestConnectedComponent(applied_labels=applied_labels, is_onehot=False, independent=independent,
                                            connectivity=connectivity, num_components=num_components)
        arr = tfm(self.numpy(key))
        return self.add(f'{key}{postfix}', arr, reference_key=key)

    def numpy(self, key: str):
        """returns ``study[key]`` converted to a numpy array."""
        return tonumpy(self[key])

    def tensor(self, key: str):
        """returns ``study[key]`` converted to a tensor."""
        return totensor(self[key])

    def _get_sorted_items(self, scans: bool, seg: bool, order: Sequence[str] | None = None) -> list[tuple[str, sitk.Image]]:
        if not (scans or seg): raise ValueError("At least one of `scans` or `seg` must be True")

        if order is not None:
            return [(k, self[k]) for k in order]

        # make sure items are always sorted in the same order
        items = []
        if scans: items = sorted(self.get_scans().items(), key = lambda x: x[0])
        if seg: items.extend(sorted(self.get_segmentations().items(), key = lambda x: x[0]))
        return items


    def stack_numpy(self, scans:bool = True, seg: bool = False, dtype=None, order: Sequence[str] | None = None) -> np.ndarray:
        """Stack images into a numpy array, returns an array of shape ``(n_images, *dims)``.

        Args:
            scans: Whether to include scan images in the stack.
            seg: Whether to include segmentation images in the stack.
            dtype: Data type for the output array. If None, uses the default type.
            order:
                Specific order for the images in the stack. If specified, ignores ``scans`` and ``seg`` options.
                If None, uses alphabetic sorting.
        """
        items = self._get_sorted_items(scans=scans, seg=seg, order=order)

        stacked = np.array([sitk.GetArrayFromImage(v) for k, v in items])
        if dtype is not None: stacked = stacked.astype(dtype, copy=False)
        return stacked

    def stack_tensor(self, scans:bool = True, seg: bool = False, device=None, dtype=None, order: Sequence[str] | None = None) -> "torch.Tensor":
        """Stack images into a torch tensor, returns an tensor of shape ``(n_images, *dims)``.

        Args:
            scans: Whether to include scan images in the stack.
            seg: Whether to include segmentation images in the stack.
            device: Device for the output tensor. If None, uses the default device.
            dtype: Data type for the output tensor. If None, uses the default type.
            order:
                Specific order for the images in the stack. If specified, ignores ``scans`` and ``seg`` options.
                If None, uses alphabetic sorting.
        """
        import torch
        items = self._get_sorted_items(scans=scans, seg=seg, order=order)
        stacked = torch.stack([torch.from_numpy(sitk.GetArrayFromImage(v)) for _,v in items])
        return stacked.to(device=device, dtype=dtype, memory_format=torch.contiguous_format)

    def numpy_dict(self) -> dict[str, np.ndarray | Any]:
        """Returns a dictionary with all images converted to numpy arrays, info is included as is."""
        return {k: (sitk.GetArrayFromImage(v) if isinstance(v, sitk.Image) else v) for k, v in self.items()}

    def tensor_dict(self) -> "dict[str, torch.Tensor | Any]":
        """Returns a dictionary with all images converted to tensors, info is included as is."""
        import torch
        return {k: (torch.from_numpy(v) if isinstance(v, np.ndarray) else v) for k,v in self.numpy_dict()}

    def plot(self):
        from .utils.plotting import plot_study
        return plot_study(self.get_images().numpy_dict())

    def save(
        self,
        dir: str | os.PathLike,
        prefix: str = "",
        suffix: str = "",
        ext: str = "nii.gz",
        mkdir=True,
        use_compression=True,
        pickle_module = pickle,
    ):
        """Writes this study to a directory, with filenames being ``{path}/{prefix}{key}{suffix}.{ext}``

        Args:
            dir: Directory to save the study to.
            prefix: Prefix to add to all filenames.
            suffix: Suffix to add to all filenames (before extension).
            ext: File extension for image files. Default is 'nii.gz'.
            mkdir: Whether to create the directory if it doesn't exist. Default is True.
            use_compression: Whether to use compression for image files. Default is True.
            pickle_module: Module to use for pickling info objects. Default is pickle.
        """
        if ext.startswith('.'): ext = ext[1:]

        # make directory
        if not os.path.exists(dir):
            if mkdir: os.mkdir(dir)
            else: raise FileNotFoundError(f"Directory {dir} doesn't exist and {mkdir = }")

        # save
        for k,v in self.items():

            # save infos
            if k.startswith('info'):
                try:
                    with open(os.path.join(dir, f"{prefix}{k}{suffix}.pkl"), "wb") as file:
                        pickle_module.dump(v, file)

                except Exception as e:
                    print(f"Couldn't save {k}:\n{e!r}")

            # save images
            else:
                # this handles non ascii chars
                with tempfile.TemporaryDirectory() as temp_path:
                    sitk.WriteImage(v, os.path.join(temp_path, f"{prefix}{k}{suffix}.{ext}"), useCompression=use_compression)
                    shutil.move(os.path.join(temp_path, f"{prefix}{k}{suffix}.{ext}"), dir)

    def load(self, dir: str | os.PathLike, prefix: str = '', suffix: str = '', ext: str = 'nii.gz', pickle_module = pickle):
        """Returns a new study, updated by data loaded from ``dir``, which can be created by calling ``study.save(dir)``.

        Args:
            dir: Directory to load the study from.
            prefix: Expected prefix of filenames.
            suffix: Expected suffix of filenames.
            ext: Expected file extension for image files. Default is 'nii.gz'.
            pickle_module: Module used for unpickling info objects. Default is pickle.
        """
        study = self.copy()

        files = os.listdir(dir)

        for f in files:
            full = os.path.join(dir, f)
            name:str = f

            # check prefix
            if prefix == '' or name.startswith(prefix):
                name = name[len(prefix):]

                # load images
                if name.endswith(f'{suffix}.{ext}'):
                    name = name[:-len(f'{suffix}.{ext}')]
                    study[name] = tositk(full)

                # load infos
                elif name.endswith(f'{suffix}.pkl'):
                    name = name[:-len(f'{suffix}.pkl')]

                    try:
                        with open(full, 'rb') as file:
                            study[name] = pickle_module.load(file)
                    except Exception as e:
                        print(f"Couldn't load {full}:\n{e!r}")

        return study

    @classmethod
    def from_dir(cls, dir: str | os.PathLike, prefix: str = '', suffix: str = '', ext: str = 'nii.gz', pickle_module = pickle):
        """Load a study from a directory.

        Args:
            dir: Directory to load the study from.
            prefix: Expected prefix of filenames.
            suffix: Expected suffix of filenames.
            ext: Expected file extension for image files. Default is 'nii.gz'.
            pickle_module: Module used for unpickling info objects. Default is pickle.
        """
        return cls().load(dir=dir, prefix=prefix, suffix=suffix, ext=ext, pickle_module=pickle_module)