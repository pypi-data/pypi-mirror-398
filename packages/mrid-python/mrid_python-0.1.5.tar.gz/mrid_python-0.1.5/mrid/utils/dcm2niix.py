import warnings
import os
import shutil
import subprocess
import tempfile

import SimpleITK as sitk


def run_dcm2niix(
    inpath: str | os.PathLike,
    outfolder: str | os.PathLike,
    outfname: str,
    mkdirs=True,
    save_BIDS=False,
    allow_stacking=True,
) -> str:
    """Convert dicom folder to NIfTI format and return path to the output ``nii.gz`` file,
    uses dcm2niix (https://github.com/rordenlab/dcm2niix) which needs to be installed.

    This is a simple wrapper around dcm2niix command line interface using subprocess, it also handles non-ascii paths.

    Args:
        inpath (str):
            Path to the dicom files of a single study and single modality.
            Software like Weasis has DICOM export functionality that can be
            used to organize DICOM files into folders by patients studies and modalities.

        outfolder (str): Path to the output folder (e.g. ``D:/MRI/patient001/0``).

        outname (str):
            Output filename, excluding ``.nii.gz`` because it will be added by ``dcm2niix``.
            Can use modifiers (e.g. `%d` will be replaced with series description string from DICOM metadata),
            as explained here https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage#General_Usage

        mkdirs (bool, optional): Whether to create ``outfolder`` if it doesn't exist, otherwise throws an error. Defaults to True.

        save_BIDS (bool, optional):
            Whether to save extra BIDS sidecar - extra info in JSON format that can't be saved into nifti. Defaults to False.

        allow_stacking (bool, optional):
            Whether to allow stacking different studies into a single file.
            Sometimes this may help with malformed DICOMs that are recognized as separate studies.
    """
    # dicom2niix doesnt support non-ascii paths, so convert to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:

        # create temporary folders
        tmp_input_dir = os.path.join(tmpdir, "mrid_dcm2niix_input")
        tmp_output_dir = os.path.join(tmpdir, "mrid_dcm2niix_output")
        if os.path.exists(tmp_output_dir): shutil.rmtree(tmp_output_dir)
        os.mkdir(tmp_output_dir)
        shutil.copytree(inpath, tmp_input_dir)

        # create output dir if it doesn't exist
        if outfolder != '':
            if not os.path.exists(outfolder):
                if mkdirs: os.makedirs(outfolder)
                else: raise NotADirectoryError(f"Output path {outfolder} doesn't exist")

        # run dcm2niix
        subprocess.run(["dcm2niix",
                        "-z", "y", # compression
                        "-m", "y" if allow_stacking else 'n', # disable stacking images from different studies
                        "-b", 'y' if save_BIDS else 'n', # save additional JSON info that can't be saved into nifti (https://bids.neuroimaging.io/ BIDS sidecar format)
                        "-o", os.path.normpath(tmp_output_dir), # output folder
                        "-f", outfname, # output filename
                        os.path.normpath(tmp_input_dir)], # input folder
                    check=True)

        # find what new nifti files were created
        out_files = [i for i in os.listdir(tmp_output_dir) if i.lower().strip().endswith('.nii.gz')]

        # move them to output folder
        shutil.copytree(tmp_output_dir, outfolder)

        if len(out_files) > 1:
            warnings.warn(f"More than one NIfTI file was created in {outfolder}, path to the first one will be returned. Something may be wrong.")

        if len(out_files) == 0:
            raise RuntimeError(f"No nifti files were created in {outfolder}")

        # return path to the created nifti file
        return os.path.join(outfolder, out_files[0])


def dcm2sitk(inpath:str | os.PathLike) -> sitk.Image:
    with tempfile.TemporaryDirectory() as tmpdir:
        nifti_path = run_dcm2niix(inpath=inpath, outfolder=tmpdir, outfname='temp', mkdirs=False, save_BIDS=False)
        return sitk.ReadImage(nifti_path)