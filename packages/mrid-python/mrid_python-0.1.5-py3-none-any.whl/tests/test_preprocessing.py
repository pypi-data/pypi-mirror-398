"""sanity tests"""
import numpy as np
import SimpleITK as sitk

from mrid.preprocessing import bias_field_correction


def test_resize():
    from mrid import Study
    study = Study(t1=np.random.rand(10, 20, 30).astype(np.float32))
    resized = study.resize([5, 10, 15])
    assert 't1' in resized
    assert study.numpy("t1").shape == (10, 20, 30)
    assert resized.numpy("t1").shape == (5, 10, 15)


def test_downsample():
    from mrid import Study
    study = Study(t1=np.random.rand(10, 20, 30).astype(np.float32))
    downsampled = study.downsample(factor=2.0)  # 2x downsampling
    assert 't1' in downsampled
    assert study.numpy("t1").shape == (10, 20, 30)
    assert downsampled.numpy("t1").shape == (5, 10, 15)


def test_bias_field_correction():
    img = sitk.Image(10, 10, 10, sitk.sitkFloat32)
    corrected = bias_field_correction.n4_bias_field_correction(img, shrink=4)
    assert isinstance(corrected, sitk.Image)


def test_crop_bg():
    from mrid import Study
    data = {
        't1': np.random.rand(20, 20, 20).astype(np.float32),
        't2': np.random.rand(20, 20, 20).astype(np.float32)
    }
    study = Study(data)
    cropped = study.crop_bg('t1')
    assert 't1' in cropped
    assert 't2' in cropped

    assert study.numpy("t1").shape == study.numpy("t2").shape