import os
import warnings


def fix_dicom_uids(input_folder: str | os.PathLike, output_folder: str | os.PathLike):
    """
    Reads DICOM files from input_folder, assigns a new common SeriesInstanceUID,
    generates new unique SOPInstanceUIDs and sequential InstanceNumbers,
    and saves the modified files to output_folder.

    This can fix malformed DICOMs that are loaded as separate series by some software.

    Args:
        input_folder (str): Path to the folder containing the problematic DICOM files.
        output_folder (str): Path to the folder where fixed DICOM files will be saved.
                             It will be created if it doesn't exist.
    """
    import pydicom
    from pydicom.errors import InvalidDicomError
    from pydicom.uid import generate_uid

    os.makedirs(output_folder, exist_ok=True)

    dicom_files_info = []

    # -------------------------------- load DICOMs ------------------------------- #
    for filename in os.listdir(input_folder):
        input_filepath = os.path.join(input_folder, filename)
        if os.path.isfile(input_filepath):
            try:
                ds = pydicom.dcmread(input_filepath, defer_size="512 KB", stop_before_pixels=False)

                if 'PixelData' in ds:
                    dicom_files_info.append({'dataset': ds, 'original_filename': filename})
                else:
                    warnings.warn(f"Skipping DICOM file with no PixelData: {filename}")

            # except InvalidDicomError as e:
            #     warnings.warn(f"Failed to load {filename}, skipping, exception was: {e}")
            except Exception as e:
                warnings.warn(f"Failed to load {filename}, skipping, exception was: {e}")

    if not dicom_files_info:
        raise FileNotFoundError(f'No valid DICOM files with PixelData found in the "{input_folder}"')

    # ------------------------- sort by instance numbers ------------------------- #
    dicom_files_info.sort(key=lambda info: int(info['dataset'].get('InstanceNumber', 0)))

    # ---------------------- make new dataset with new UIDs ---------------------- #
    new_series_uid = generate_uid()

    for i, file_info in enumerate(dicom_files_info):
        ds = file_info['dataset']
        original_filename = file_info['original_filename']
        instance_number = i + 1 # Generate sequential instance number (1-based)

        # Generate a NEW, UNIQUE SOP Instance UID for this specific file
        new_sop_instance_uid = generate_uid()

        # Update main DICOM tags
        ds.SeriesInstanceUID = new_series_uid
        ds.SOPInstanceUID = new_sop_instance_uid
        ds.InstanceNumber = str(instance_number) # VR 'IS' (Integer String)

        # Update file_meta (Group 0002)
        # Check if file_meta exists (it should for standard DICOM files)
        if hasattr(ds, 'file_meta') and ds.file_meta:
            ds.file_meta.MediaStorageSOPInstanceUID = new_sop_instance_uid

            # update Implementation Class UID and Version Name
            # ds.file_meta.ImplementationClassUID = pydicom.uid.PYDICOM_IMPLEMENTATION_UID
            # ds.file_meta.ImplementationVersionName = f"PYDICOM {pydicom.__version__}"
        else:
            warnings.warn(f"Warning: File Meta Information (Group 0002) missing or empty in {original_filename}. Cannot update MediaStorageSOPInstanceUID.")

        # other potentially helpful tags (but avoid geometry if unsure)
        # ds.add_new(0x00080013, 'TM', datetime.datetime.now().strftime('%H%M%S.%f')[:16]) # Instance Creation Time (dummy)
        # ds.add_new(0x00080033, 'TM', datetime.datetime.now().strftime('%H%M%S.%f')[:16]) # Content Time (dummy)

    # ----------------------------- save new dataset ----------------------------- #
    for file_info in dicom_files_info:
        ds = file_info['dataset']
        output_filepath = os.path.join(output_folder, file_info['original_filename'])

        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        ds.save_as(output_filepath, write_like_original=True)
