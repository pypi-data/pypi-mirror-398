from collections.abc import Mapping

import numpy as np
from ..loading import ImageLike, tonumpy

def plot_study(data: Mapping[str, ImageLike]):
    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt

    data = {k: tonumpy(v) for k,v in data.items()}
    n_vals = len(data)

    # 1. Determine layout for the Outer Grid (Modalities)
    # We try to make it roughly square (e.g., 4 items -> 2x2, 5 items -> 2x3)
    n_cols_outer = int(np.ceil(np.sqrt(n_vals)))
    n_rows_outer = int(np.ceil(n_vals / n_cols_outer))

    # Figure size scaling
    fig = plt.figure(figsize=(n_cols_outer * 5, n_rows_outer * 5))

    # Create the Outer Grid
    outer_grid = gridspec.GridSpec(n_rows_outer, n_cols_outer, figure=fig, wspace=0.3, hspace=0.3)

    # 2. Iterate through each modality
    for i, (modality_name, volume) in enumerate(data.items()):
        # Create an Inner Grid (3x3) inside the specific cell of the Outer Grid
        inner_grid = gridspec.GridSpecFromSubplotSpec(
            3, 3,
            subplot_spec=outer_grid[i],
            wspace=0.05, hspace=0.05
        )

        # Calculate slicing indices for 25%, 50%, 75%
        shapes = volume.shape
        percentages = [0.25, 0.50, 0.75]

        # Loop through dimensions (Rows of the 3x3)
        for dim_idx in range(3):

            # Get the exact indices for this dimension
            slice_indices = [int(shapes[dim_idx] * p) for p in percentages]

            # Loop through the slices (Columns of the 3x3)
            for col_idx, slice_loc in enumerate(slice_indices):

                # Create the subplot in the inner grid
                ax = fig.add_subplot(inner_grid[dim_idx, col_idx])

                # 3. Extract the 2D Slice
                if dim_idx == 0:
                    img_slice = volume[slice_loc, :, :]
                    row_label = f"Dim 0\n(Slice {slice_loc})"
                elif dim_idx == 1:
                    img_slice = volume[:, slice_loc, :]
                    row_label = f"Dim 1\n(Slice {slice_loc})"
                else: # dim_idx == 2
                    img_slice = volume[:, :, slice_loc]
                    row_label = f"Dim 2\n(Slice {slice_loc})"

                # Plot image
                ax.imshow(img_slice, cmap='gray', aspect='auto')

                # Remove ticks for cleanliness
                ax.set_xticks([])
                ax.set_yticks([])

                # Labels: Only add row labels to the first column
                if col_idx == 0:
                    ax.set_ylabel(row_label, fontsize=9, rotation=90)

                # Labels: Only add col labels to the first row
                if dim_idx == 0:
                    ax.set_title(f"{int(percentages[col_idx]*100)}%", fontsize=10)

        # Add the main Modality Name on top of the grid block
        # We fetch the geometric center of the top row of the inner grid
        box = outer_grid[i].get_position(fig)
        fig.text(box.x0 + box.width/2, box.y1 + 0.04, modality_name,
                 ha='center', va='bottom', fontsize=14, fontweight='bold')

    # plt.show()
    return fig

if __name__ == "__main__":

    def dummy_data(shape, type='sphere'):
        x, y, z = np.indices(shape)
        cx, cy, cz = shape[0]//2, shape[1]//2, shape[2]//2
        mask = np.zeros(shape)
        if type == 'sphere':
            r = min(shape)//3
            mask[(x-cx)**2 + (y-cy)**2 + (z-cz)**2 < r**2] = 1
        elif type == 'cube':
            r = min(shape)//4
            mask[cx-r:cx+r, cy-r:cy+r, cz-r:cz+r] = 1
        elif type == 'noise':
            mask = np.random.rand(*shape)

        return mask

    plot_study({
        "Sphere": dummy_data((60, 60, 60), 'sphere'),
        "Cube": dummy_data((60, 60, 60), 'cube'),
        "Noise": dummy_data((60, 60, 60), 'noise'),
        "Another sphere": dummy_data((60, 60, 60), 'sphere'),
    })