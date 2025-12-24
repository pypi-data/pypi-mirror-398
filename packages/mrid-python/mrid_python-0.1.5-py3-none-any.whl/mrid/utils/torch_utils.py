import importlib.util
from typing import TYPE_CHECKING, cast

from .python_utils import LazyLoader

lazy_torch = LazyLoader("torch")
if TYPE_CHECKING:
    import torch
    lazy_torch = cast(torch, lazy_torch)

TORCH_INSTALLED = importlib.util.find_spec("torch") is not None

if TORCH_INSTALLED:
    CUDA_IF_AVAILABLE = 'cuda' if lazy_torch.cuda.is_available() else 'cpu'
else:
    CUDA_IF_AVAILABLE = 'cpu'
