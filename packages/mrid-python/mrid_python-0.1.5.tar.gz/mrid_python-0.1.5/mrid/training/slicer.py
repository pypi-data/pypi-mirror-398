import os
import random
from functools import partial
from typing import Any, Literal, cast
from collections.abc import Callable, Sequence
import torch

from ..loading import ImageLike, totensor, tonumpy


class SliceSampler:
    """Samples 2D or 2.5D slices with specified probability given to slices containing segmentation and slices that do not.

    Args:
        data (ImageLike):
            input tensors (e.g. scans) stacked along first dimension, must have a shape of (channels, D, H, W).
        segmentation (ImageLike):
            segmentations in integer data type, not one hot encoded, must have a shape of of (D, H, W).
            Background must have a value of 0.

    Example:
    ```python
    # suppose we have a list of scans and their segmentations
    # data = [(scan1, seg1), (scan2, seg2), ...]

    # make samplers
    samplers = [SliceSampler(scan, seg) for (scan, seg) in data]

    # make dataset
    dataset = SliceDataloader(samplers, around=2, seg_prob=0.5, repeat=100)

    # make dataloader
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True)
    """
    def __init__(self, data: ImageLike, segmentation: ImageLike):
        data = totensor(data)
        segmentation = totensor(segmentation)

        # checks
        if data.ndim != 4:
            raise RuntimeError(f"Scans must have a shape of (channels, D, H, W), got {data.shape}")
        if segmentation.ndim != 3:
            raise RuntimeError(f"Segmentation must have a shape of of (D, H, W), got {segmentation.shape}")
        if segmentation.is_floating_point():
            raise RuntimeError(f"Segmentation must have integer data type, got {segmentation.dtype}")
        if segmentation.shape[1:] != data.shape:
            raise RuntimeError(f"Shapes of scans and segmentation do not match: {data.shape = }, {segmentation.shape = }")
        if segmentation.min() < 0:
            raise RuntimeError(f"Segmentation background must have a value of 0, got {segmentation.min() = }")

        self.data = data
        self.segmentation = segmentation

        # determine slices with segmentation
        self.seg_indexes: dict[Literal[0,1,2], list[int]] = {}
        """Holds indexes of slices that contain segmentation along each dimension"""

        self.empty_indexes: dict[Literal[0,1,2], list[int]] = {}
        """Holds indexes of slices that do not contain segmentation along each dimension"""

        self.seg_indexes[0] = torch.nonzero(self.segmentation.sum((1,2)), as_tuple=True)[0].tolist()
        self.seg_indexes[1] = torch.nonzero(self.segmentation.sum((0,2)), as_tuple=True)[0].tolist()
        self.seg_indexes[2] = torch.nonzero(self.segmentation.sum((0,1)), as_tuple=True)[0].tolist()

        self.empty_indexes[0] = torch.nonzero(self.segmentation.sum((1,2)) == 0, as_tuple=True)[0].tolist()
        self.empty_indexes[1] = torch.nonzero(self.segmentation.sum((0,2)) == 0, as_tuple=True)[0].tolist()
        self.empty_indexes[2] = torch.nonzero(self.segmentation.sum((0,1)) == 0, as_tuple=True)[0].tolist()

        self.empty_dims: list[Literal[0,1,2]] = [i for i,indexes in self.empty_indexes.items() if len(indexes) > 0]
        """Dims that have at least one empty slice"""

    def get_slice(
        self,
        dim: Literal[0, 1, 2],
        coord: int,
        around: int,
        randflip: bool = True,
        flatten: bool = True,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Get a slice along given ``dim`` and ``coord``, plus neigbouring slices if ``around`` > 0.
        Returns a ``(mri, segmentation)`` tuple.

        If ``flatten=True``, ``mri`` is a ``(C, H, W)`` tensor, where ``C = num_channels * (1 + 2*around)``.
        For example, if you have 2 channels: t1 and t2, and ``around = 1``, the 6 resulting channels will be
        ``[t1[coord - 1], t1[coord], t1[coord + 1], t2[coord - 1], t2[coord], t2[coord + 1]``.

        If ``flatten=False``, ``mri`` is a ``(2*around + 1, C, H, W)`` tensor.

        Segmentation is a ``(H, W)`` tensor, not one-hot encoded.

        Args:
            dim (Literal[0,1,2]): dimension to slice along.
            coord (int): coordinate to pick.
            around (int): this number of slices above and below central slice will be returned.
            randflip (bool, optional):
                whether to randomly flip along ``dim``, only has effect when ``around > 0``. Defaults to True.
            flatten (bool, optional):
                whether to merge ``dim`` with channel dimensions. Defaults to True.
        """
        # load tensor with first dimension being one that is being sliced
        if dim == 0:
            tensor = self.data
            seg = self.segmentation
            length = self.data.shape[1]
        elif dim == 1:
            tensor = self.data.swapaxes(1, 2)
            seg = self.segmentation.swapaxes(0,1)
            length = self.data.shape[2]
        else:
            tensor = self.data.swapaxes(1, 3)
            seg = self.segmentation.swapaxes(0,2)
            length = self.data.shape[3]

        # make sure coord is within the shape
        if coord < around: coord = around
        elif coord + around >= length: coord = length - around - 1

        # get slice
        if around == 0:
            if flatten: return tensor[:, coord], seg[coord] # (C, H, W)
            return tensor[None, :, coord], seg[coord] # (1, C, H, W)

        # else get slice + neighbouring slices
        slice = tensor[:, coord - around : coord + around + 1] # (C, D, H, W)

        if randflip and random.random() > 0.5:
            slice = slice.flip((1,))

        if flatten:
            slice = slice.flatten(0, 1)

        return slice, seg[coord]

    def get_random_empty_slice(
        self, around: int, randflip: bool = True, flatten: bool = True
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Returns a random slice with no segmentation"""

        # if there are no empty dims, return random slice
        if len(self.empty_dims) == 0:
            dim = cast(Literal[0,1,2], random.choice([0,1,2]))
            coord = random.randrange(around, self.data.shape[dim+1] - around)

        else:
            dim = random.choice(self.empty_dims)
            coord = random.choice(self.empty_indexes[dim])

        return self.get_slice(dim=dim, coord=coord, around=around, randflip=randflip, flatten=flatten)

    def get_random_seg_slice(
        self, around: int, randflip: bool = True, flatten: bool = True
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Returns a random slice with segmentation"""
        dim = cast(Literal[0,1,2], random.choice([0,1,2]))
        indexes = self.seg_indexes[dim]

        # if there are no non-empty slices, return random slice
        if len(indexes) == 0:
            coord = random.randrange(around, self.data.shape[dim+1] - around)

        else:
            coord = random.choice(indexes)

        return self.get_slice(dim=dim, coord=coord, around=around, randflip=randflip, flatten=flatten)

    # an alternative would be to return a list of slices with segmentation, and a list of callables that return
    # random empty slices. But I've realized the final dataset made of multiple SliceSamplers will then have more
    # slices from scans with larger segmentations.

    def random_empty_callable(
        self, around: int, randflip: bool = True, flatten: bool = True
    ) -> Callable[..., tuple[torch.Tensor, torch.Tensor]]:
        """returns a callable that accepts no arguments and returns a random empty slice."""
        return partial(self.get_random_empty_slice, around=around, randflip=randflip, flatten=flatten)

    def random_seg_callable(
        self, around: int, randflip: bool = True, flatten: bool = True
    ) -> Callable[..., tuple[torch.Tensor, torch.Tensor]]:
        """returns a callable that accepts no arguments and returns a random slice with segmentation."""
        return partial(self.get_random_seg_slice, around=around, randflip=randflip, flatten=flatten)

    def random_weighted_callable(
        self, around: int, seg_prob: float, randflip: bool = True, flatten: bool = True
    ) -> Callable[..., tuple[torch.Tensor, torch.Tensor]]:
        """returns a callable that accepts no arguments and returns a random slice with
        segmentation with probability ``seg_prob``, a random empty slice otherwise."""

        def get_sample():
            if random.random() < seg_prob:
                return self.get_random_seg_slice(around=around, randflip=randflip, flatten=flatten)

            return self.get_random_empty_slice(around=around, randflip=randflip, flatten=flatten)

        return get_sample


class SliceDataset(torch.utils.data.Dataset):
    """A dataset of SliceSamplers.

    Args:
        samplers (Sequence[SliceSampler]): sequence of SliceSampler objects.
        around (int): this number of slices above and below central slice will be returned.
        seg_prob (float):
            probability that a random slice with segmentation is returned, otherwise a random empty slice is returned.
        randflip (bool, optional):
            whether to randomly flip along selected dim, only has effect when ``around > 0``. Defaults to True.
        flatten (bool, optional):
            whether to merge ``dim`` with channel dimensions. Defaults to True.
        repeat (int, optional):
            One epoch will sample random slice from each sampler this many times. Defaults to 1.
    """
    def __init__(
        self,
        samplers: Sequence[SliceSampler],
        around: int,
        seg_prob: float,
        randflip: bool = True,
        flatten: bool = True,
        repeat: int = 1,
        tfm: Callable[[torch.Tensor, torch.Tensor], Any] | None = None,
    ):
        super().__init__()
        self._callables = [s.random_weighted_callable(
            around=around, seg_prob=seg_prob, randflip=randflip, flatten=flatten) for s in samplers]

        self._repeat = repeat

        self.tfm = tfm

    def __len__(self):
        return len(self._callables) * self._repeat

    def __getitem__(self, i: int) -> tuple[torch.Tensor, torch.Tensor]:
        length = len(self)

        if i >= length:
            raise IndexError(f"Index {i} is larger than length of SliceDataset {length}")

        img, seg = self._callables[i % len(self._callables)]()

        if self.tfm is not None:
            return self.tfm(img, seg)

        return img, seg