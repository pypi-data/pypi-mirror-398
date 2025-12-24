import os
import tempfile
import numpy as np
import pytest
import SimpleITK as sitk

from mrid import Study


def test_study_init():
    # numpy
    study1 = Study(
        t1=np.random.rand(10, 20, 30).astype(np.float32),
        t2=np.random.rand(10, 20, 30).astype(np.float32)
    )
    assert len(study1) == 2

    # sitk
    sitk_img1 = sitk.Image(10, 20, 30, sitk.sitkFloat32)
    sitk_img2 = sitk.Image(15, 25, 35, sitk.sitkFloat32)
    study2 = Study(t1=sitk_img1, t2=sitk_img2)
    assert len(study2) == 2


def test_study_get():
    study = Study(
        t1=np.random.rand(10, 20, 30),
        t2=np.random.rand(10, 20, 30),
        seg_brain=np.random.randint(0, 2, (10, 20, 30)),
        info_patient={'age': 25, 'gender': 'M'}
    )

    assert 't1' in study
    assert 't2' in study
    assert 'seg_brain' in study
    assert 'info_patient' in study

    # test get_images
    images = study.get_images()
    assert tuple(images.keys()) == ("t1", "t2", "seg_brain")

    # test get_scans method (excludes segmentations and info)
    scans = study.get_scans()
    assert tuple(scans.keys()) == ("t1", "t2",)

    # test get_segmentations
    segmentations = study.get_segmentations()
    assert tuple(segmentations.keys()) == ("seg_brain", )

    #test get_info
    info = study.get_info()
    assert tuple(info.keys()) == ("info_patient", )


def test_apply():
    study = Study(t1=np.random.rand(10, 20, 30))
    result = study.apply(lambda x: x, lambda x: x)
    assert 't1' in result

    result2 = study.apply(None, None)
    assert 't1' in result2


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_cast(dtype):
    data = np.random.rand(5, 10, 15).astype(np.float32)
    study = Study(t1=data)

    if dtype == np.float32:
        casted = study.cast_float32()
    else:
        casted = study.cast_float64()

    assert 't1' in casted


def test_normalize():
    study = Study(t1=np.random.rand(10, 20, 30).astype(np.float32))
    normalized = study.normalize()
    assert 't1' in normalized


def test_rescale_intensity():
    study = Study(t1=np.random.rand(10, 20, 30).astype(np.float32))
    rescaled = study.rescale_intensity(0.0, 1.0)
    assert 't1' in rescaled


def test_numpy_method():
    data = np.random.rand(10, 20, 30).astype(np.float32)
    study = Study(t1=data)

    numpy_array = study.numpy('t1')
    assert isinstance(numpy_array, np.ndarray)
    assert numpy_array.shape == (10, 20, 30)


def test_stack_numpy():
    data = {
        't1': np.random.rand(10, 20, 30),
        't2': np.random.rand(10, 20, 30)
    }
    study = Study(data)

    stacked = study.stack_numpy(scans=True, seg=False)
    assert stacked.shape == (2, 10, 20, 30)  # 2 images, each 10x20x30

@pytest.mark.parametrize("prefix", ("", "prefix"))
@pytest.mark.parametrize("suffix", ("", "suffix"))
def test_serialization(prefix,suffix):
    data = dict(
        t1=np.random.rand(10,20,30),
        t2=np.random.rand(40,50,60),
        seg_brain=np.random.randint(0,2, (10,20,30)),
        seg_tumor=np.random.randint(0,5, (40,50,60)),
        info_id=10,
        info_name="Name"
    )

    study = Study(data)
    assert sorted(study.keys()) == sorted(["t1", "t2", "seg_brain", "seg_tumor", "info_id", "info_name"])

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = os.path.join(tmpdir, "study")
        study.save(out_dir, prefix=prefix, suffix=suffix)
        loaded = Study.from_dir(out_dir, prefix=prefix, suffix=suffix)

    assert sorted(loaded.keys()) == sorted(["t1", "t2", "seg_brain", "seg_tumor", "info_id", "info_name"])

    for k, v in study.items():
        if isinstance(v, sitk.Image):
            assert sitk.GetArrayFromImage(v).shape == sitk.GetArrayFromImage(loaded[k]).shape
            assert sitk.GetArrayFromImage(v).dtype == sitk.GetArrayFromImage(loaded[k]).dtype
            assert np.all(sitk.GetArrayFromImage(v) == sitk.GetArrayFromImage(loaded[k]))
        else:
            assert v == loaded[k]