import numpy as np
import pytest
import SimpleITK as sitk
from mrid.loading.convert import tositk, tonumpy, totensor


def test_tositk_with_numpy():
    data = np.random.rand(10, 20, 30).astype(np.float32)
    sitk_img = tositk(data)

    assert isinstance(sitk_img, sitk.Image)
    assert sitk.GetArrayFromImage(sitk_img).shape == (10, 20, 30)


def test_tositk_with_sitk_image():
    original_img = sitk.Image(10, 20, 30, sitk.sitkFloat32)
    result_img = tositk(original_img)

    assert result_img is original_img


def test_tositk_with_pathlike():
    with pytest.raises(FileNotFoundError):
        tositk("/nonexistent/path.nii.gz")


def test_tonumpy_with_numpy():
    data = np.random.rand(10, 20, 30).astype(np.float32)
    result = tonumpy(data)

    assert isinstance(result, np.ndarray)
    assert np.array_equal(data, result)


def test_tonumpy_with_sitk():
    sitk_img = sitk.Image(10, 20, 30, sitk.sitkFloat32)
    array = sitk.GetArrayFromImage(sitk_img)

    result = tonumpy(sitk_img)

    assert isinstance(result, np.ndarray)
    assert result.shape == array.shape


def test_tonumpy_with_pathlike():
    with pytest.raises(FileNotFoundError):
        tonumpy("/nonexistent/path.nii.gz")


def test_totensor_with_numpy():
    try:
        import torch
        data = np.random.rand(10, 20, 30).astype(np.float32)
        tensor = totensor(data)

        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape == torch.Size([10, 20, 30])
    except ImportError:
        pytest.skip("no torch")


def test_totensor_with_sitk():
    try:
        import torch
        sitk_img = sitk.Image(30, 20, 10, sitk.sitkFloat32) # note that dims are reversed in sitk
        tensor = totensor(sitk_img)

        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape == torch.Size([10, 20, 30])
    except ImportError:
        pytest.skip("no torch")


def test_totensor_with_tensor():
    try:
        import torch
        original_tensor = torch.rand(10, 20, 30)
        result = totensor(original_tensor)

        assert result is original_tensor
    except ImportError:
        pytest.skip("no torch")
