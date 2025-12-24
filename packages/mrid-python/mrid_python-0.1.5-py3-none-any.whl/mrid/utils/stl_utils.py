import os
import warnings

import numpy as np
import SimpleITK as sitk

from ..loading.convert import tositk

# def stl2sitk(
#     stl_path: str | os.PathLike,
#     reference: str | os.PathLike | sitk.Image,
#     fix_holes: bool = False,
# ):
#     """
#     Loads an STL file under ``stl_path`` and converts it to ``sitk.Image`` aligned with ``reference``.
#     Note that this might take a few minutes.

#     Args:
#         stl_path (str): Path to the STL segmentation file. The STL coordinates
#                         MUST be in the same coordinate system as the ``reference``.
#         reference (str | os.PathLike | sitk.Image): path to a directory of DICOM files or a NIfTI file, or a ``sitk.Image``.
#         fix_holes (bool, optional): whether to try to fix holes in STL if they are detected (this can be very slow).
#     """
#     import trimesh

#     # ------------------------------ load reference ------------------------------ #
#     reference = tositk(reference)

#     origin = np.array(reference.GetOrigin())
#     spacing = np.array(reference.GetSpacing())
#     # ct_direction = np.array(ct_image.GetDirection()).reshape(3, 3)
#     size = np.array(reference.GetSize()) # Order: x, y, z
#     shape_xyz = size
#     shape_zyx = size[::-1]

#     # --------------------------------- load STL --------------------------------- #
#     mesh = trimesh.load_mesh(stl_path)

#     if not mesh.is_watertight:
#         warnings.warn(f"Warning: STL mesh '{stl_path}' is not watertight. Voxelization using 'contains' might be inaccurate.")
#         if fix_holes:
#             mesh.fill_holes()
#             if not mesh.is_watertight:
#                 warnings.warn("Warning: Failed to make mesh watertight after filling holes.")

#     # ------------------------------- voxelize STL ------------------------------- #
#     x_coords = origin[0] + np.arange(shape_xyz[0]) * spacing[0]
#     y_coords = origin[1] + np.arange(shape_xyz[1]) * spacing[1]
#     z_coords = origin[2] + np.arange(shape_xyz[2]) * spacing[2]

#     # Use meshgrid to create a grid of coordinates
#     # Note the 'ij' indexing to match the z, y, x array structure
#     zz, yy, xx = np.meshgrid(z_coords, y_coords, x_coords, indexing='ij')

#     # Stack coordinates into a (N, 3) array where N = Z*Y*X
#     voxel_centers_xyz = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=-1)

#     # This checks which voxel center points fall inside the mesh volume
#     voxel_mask_flat = mesh.contains(voxel_centers_xyz)

#     # Reshape the flat boolean mask back into the 3D CT shape (z, y, x)
#     stl_array = voxel_mask_flat.reshape(shape_zyx).astype(np.uint8) # Use uint8 for masks

#     # ------------------------------ make sitk.Image ----------------------------- #
#     stl_sitk = sitk.GetImageFromArray(stl_array)

#     stl_sitk.SetOrigin(reference.GetOrigin())
#     stl_sitk.SetSpacing(reference.GetSpacing())
#     stl_sitk.SetDirection(reference.GetDirection())
#     return stl_sitk

def stl2sitk(
    stl_path: str | os.PathLike,
    reference: str | os.PathLike | sitk.Image,
    fix_holes: bool = False,
):
    """
    Loads an STL file under ``stl_path`` and converts it to ``sitk.Image`` aligned with ``reference``.
    Note that this might take a few minutes.

    Args:
        stl_path (str): Path to the STL segmentation file. The STL coordinates
                        MUST be in the same coordinate system as the ``reference``.
        reference (str | os.PathLike | sitk.Image): path to a directory of DICOM files or a NIfTI file, or a ``sitk.Image``.
        fix_holes (bool, optional): whether to try to fix holes in STL if they are detected (this can be very slow).
    """
    import trimesh

    # ------------------------------ load reference ------------------------------ #
    reference = tositk(reference)
    origin = np.array(reference.GetOrigin())
    spacing = np.array(reference.GetSpacing())
    size = np.array(reference.GetSize())  # x, y, z

    shape_xyz = size
    shape_zyx = size[::-1]

    # --------------------------------- load STL --------------------------------- #
    mesh = trimesh.load_mesh(stl_path)

    if not mesh.is_watertight:
        warnings.warn(f"STL mesh '{stl_path}' is not watertight.")
        if fix_holes:
            mesh.fill_holes()

    # ----------------------- find bounding box of the mask ---------------------- #
    bounds = mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    voxel_min = np.floor((bounds[0] - origin) / spacing).astype(int)
    voxel_max = np.ceil((bounds[1] - origin) / spacing).astype(int)

    z_min, z_max = np.clip([voxel_min[2], voxel_max[2]], 0, shape_xyz[2] - 1)

    # --------------------------------- voxelize --------------------------------- #
    stl_array = np.zeros(shape_zyx, dtype=np.uint8)
    x_coords = origin[0] + np.arange(shape_xyz[0]) * spacing[0]
    y_coords = origin[1] + np.arange(shape_xyz[1]) * spacing[1]

    yy, xx = np.meshgrid(y_coords, x_coords, indexing='ij')
    points_2d = np.stack([xx.ravel(), yy.ravel()], axis=-1)

    for z_idx in range(z_min, z_max + 1):
        z_val = origin[2] + z_idx * spacing[2]

        # Create 3D points for this slice: [X, Y, current_Z]
        points_3d = np.column_stack([
            points_2d,
            np.full(points_2d.shape[0], z_val)
        ])

        # Check containment for this slice only
        mask_flat = mesh.contains(points_3d)

        # Reshape and insert into the 3D array
        stl_array[z_idx, :, :] = mask_flat.reshape(shape_xyz[1], shape_xyz[0])

    # ------------------------------ make sitk.Image ----------------------------- #
    stl_sitk = sitk.GetImageFromArray(stl_array)
    stl_sitk.SetOrigin(reference.GetOrigin())
    stl_sitk.SetSpacing(reference.GetSpacing())
    stl_sitk.SetDirection(reference.GetDirection())

    return stl_sitk
