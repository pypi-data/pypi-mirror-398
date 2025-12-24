import pytest
from mrid.utils.python_utils import LazyLoader


def test_lazy_loader():
    loader = LazyLoader("os")
    assert loader is not None

    assert hasattr(loader, 'path')


def test_lazy_loader_nonexistent_module():
    loader = LazyLoader("this_module_does_not_exist_12345")

    with pytest.raises(ImportError):
        _ = loader.some_attribute