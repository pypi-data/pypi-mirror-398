import random
from collections.abc import Sequence, Callable
from typing import Any, Literal, TypeVar

import torch

ARR = TypeVar("ARR", bound=Any)

def crop(
    arr: ARR,
    reduction: Sequence[int],
    where: Literal["start", "end", "center", "random"] = "center",
) -> ARR:
    """Crop ``arr`` such that ``output.shape[i] = input.shape[i] - reduction[i]``"""

    shape = arr.shape[-len(reduction):]
    slices = []

    for r, sh in zip(reduction, shape):
        if r == 0:
            slices.append(slice(None))
            continue

        if r < 0: raise ValueError("Reduction cannot be negative")
        if r > sh: raise ValueError(f"Reduction {r} exceeds dimension size {sh}")

        if where == 'start': start, end = 0, sh - r
        elif where == 'end': start, end = r, sh
        elif where == 'center':
            start = r // 2
            end = start + (sh - r)
        elif where == 'random':
            start = random.randint(0, r)
            end = start + (sh - r)
        else:
            raise ValueError(f"Invalid where: {where}")

        slices.append(slice(start, end))

    # apply with broadcasting
    return arr[(..., *slices)]

def crop_to_shape(
    input: ARR,
    shape: Sequence[int],
    where: Literal["start", "end", "center", "random"] = "center",
) -> ARR:
    """Crop ``input`` to ``shape``."""

    # broadcast
    if len(shape) < input.ndim:
        shape = list(input.shape[:input.ndim - len(shape)]) + list(shape)

    return crop(input, [i - j for i, j in zip(input.shape, shape)], where=where)


def shuffle_channels(x:torch.Tensor):
    """Shuffle first axis in a ``(C, *)`` tensor"""
    return x[torch.randperm(x.shape[0])]

def shuffle_channel_groups(x:torch.Tensor, channels_per: int):
    """Shuffle first axis in a ``(C, *)`` tensor in groups of ``channels_per``."""
    num_groups = int(x.shape[0] / channels_per)
    perm = torch.randperm(num_groups, dtype=torch.int32)
    img = x.reshape(num_groups, channels_per, *x.shape[1:])[perm].flatten(0, 1)
    return img

class ShuffleChannelGroups:
    """Shuffle first axis in a ``(C, *)`` tensor in groups of ``channels_per`` with probability ``p``."""
    def __init__(self, channels_per: int, p: float):
        self.channels_per = channels_per
        self.p = p

    def __call__(self, x: torch.Tensor):
        return shuffle_channel_groups(x, self.channels_per) if random.random() < self.p else x

def groupwise_apply(x:torch.Tensor, fn: Callable[[torch.Tensor], torch.Tensor], channels_per = 3):
    """Apply ``fn`` to each ``channels_per`` group of channels in a ``(C, *)`` tensor."""
    n_channels = x.shape[0]

    assert n_channels % channels_per == 0, (
        f"x.shape[0] must be divisible by channels_per, but {x.shape[0]} is not divisible by {channels_per}"
    )

    num_groups = int(n_channels / channels_per)
    groups = x.reshape(num_groups, channels_per, *x.shape[1:]).unbind(0)
    groups = [fn(i) for i in groups]
    return torch.cat(groups, 0)

def batched_groupwise_apply(x:torch.Tensor, fn: Callable[[torch.Tensor], torch.Tensor], channels_per = 3):
    """Apply ``fn`` to each ``channels_per`` group of channels in a ``(B, C, *)`` tensor, input tensor to fn is ``(B, H, W)``"""
    batch_size, n_channels = x.shape[0], x.shape[1]

    assert n_channels % channels_per == 0, (
        f"x.shape[0] must be divisible by channels_per, but {x.shape[0]} is not divisible by {channels_per}"
    )

    num_groups = int(n_channels / channels_per)
    groups = x.reshape(batch_size, num_groups, channels_per, *x.shape[2:]).unbind(1)
    groups = [fn(i) for i in groups]
    return torch.cat(groups, 1)

class GroupwiseApply:
    """Apply ``fn`` to each ``channels_per`` group of channels in a ``(C, *)`` tensor."""
    def __init__(self, fn: Callable[[torch.Tensor], torch.Tensor], channels_per: int):
        self.fn = fn
        self.channels_per = channels_per
    def __call__(self, x: torch.Tensor):
        return groupwise_apply(x, self.fn, self.channels_per)