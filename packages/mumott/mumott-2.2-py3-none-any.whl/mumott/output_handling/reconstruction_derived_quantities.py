from dataclasses import dataclass
import h5py
import importlib.resources
import os
import shutil
import numpy as np
from matplotlib.colors import hsv_to_rgb


def get_sorted_eigenvectors(tensors_array: np.array):
    """ Calculate eigenvectors and eigenvalues of an array of
    3 by 3 matrices and sort according to increasing eigenvalues.

    Parameters
    ----------
    tensors_array
        numpy array containing the 3 by 3 tensors with the tensor
        indicies as the two last.

    Returns
    -------
    eigenvalues
        numpy array containing the eigenvalues of the tensors where
        the last dimension indexes the eigenvalues. Smallest eigenvalues
        come first.
    eigenvectors
        numpy array containing the eigenvalues of the tensors where
        the last dimension indexes the eigenvalues and the second
        to last dimension is the vector index.
    """

    volume_shape = tensors_array.shape[:-2]

    # Compute and sort eigenvectors
    w, v = np.linalg.eigh(tensors_array.reshape(-1, 3, 3))
    sorting = np.argsort(w, axis=1).reshape(-1, 3, 1)
    v = v.transpose(0, 2, 1)
    v = np.take_along_axis(v, sorting, axis=1)
    v = v.transpose(0, 2, 1)
    v = v / np.sqrt(np.sum(v ** 2, axis=1).reshape(-1, 1, 3))
    eigenvectors = v.reshape(volume_shape + (3, 3,))
    eigenvalues = np.sort(w, axis=-1).reshape(volume_shape + (3,))

    # Flip eigenvectors to have a positive z-component
    for ii in range(3):
        whereflip = eigenvectors[..., 2, ii] < 0.0
        eigenvectors[whereflip, :, ii] = -eigenvectors[whereflip, :, ii]

    return eigenvalues, eigenvectors


@dataclass
class ReconstructionDerivedQuantities:
    """ A number of useful quantities that have been computed from the coefficients of a
    reconstruction.

    Attributes
    ----------
    volume_shape : tuple
        The shape if the reconstructed volume.
    mean_intensity : np.array
        The mean intensity of the reconstructed functions over the unit sphere for each voxel.
    fractional_anisostropy : np.array
        A measure of the relative amount of anisotropic scattering in each voxel.
    eigenvector_1
    eigenvector_2
    eigenvector_3 : np.array
        The eingenvectors of the second order tensor component of the function.
        Sorted by ascending eigenvalue.
    eigenvalue_1
    eigenvalue_2
    eigenvalue_3 : np.array
        The eingenvalues of the second order tensor component of the function.
        Sorted by ascending eigenvalue.
    second_moment_tensor : np.array
        The second-moment tensor, which includes both the zero-th and second-order
        parts of the reconstructed functions.
    """

    volume_shape: tuple
    mean_intensity: np.array
    fractional_anisotropy: np.array
    eigenvector_1: np.array
    eigenvector_2: np.array
    eigenvector_3: np.array
    eigenvalue_1: np.array
    eigenvalue_2: np.array
    eigenvalue_3: np.array
    second_moment_tensor: np.array

    def write(self, filename: str) -> None:
        """ Save the derived reconstruction quantities in both an HDF5 file and a Paraview readable
        XDMF file.

        Parameters
        ----------
        filename : str
            The filename to save the data in. The extension `.h5` and `.xdmf` will be added
            to the filename.
        """

        if filename.endswith('.h5') or filename.lower().endswith('.xdmf'):

            filename, _ = os.path.splitext(filename)
            basename = os.path.basename(filename)

        # Make .h5 data file
        with h5py.File(filename + '.h5', 'w') as file:

            file.create_dataset('mean_intensity', data=self.mean_intensity.transpose((2, 1, 0)))
            file.create_dataset('fractional_anisotropy', data=self.fractional_anisotropy.transpose((2, 1, 0)))

            file.create_dataset('eigenvector_1', data=self.eigenvector_1.transpose((2, 1, 0, 3)))
            file.create_dataset('eigenvector_2', data=self.eigenvector_2.transpose((2, 1, 0, 3)))
            file.create_dataset('eigenvector_3', data=self.eigenvector_3.transpose((2, 1, 0, 3)))

            file.create_dataset('eigenvector_1_rgb',
                                data=get_colors_on_halfsphere(self.eigenvector_1).transpose((2, 1, 0, 3)))
            file.create_dataset('eigenvector_2_rgb',
                                data=get_colors_on_halfsphere(self.eigenvector_2).transpose((2, 1, 0, 3)))
            file.create_dataset('eigenvector_3_rgb',
                                data=get_colors_on_halfsphere(self.eigenvector_3).transpose((2, 1, 0, 3)))

            file.create_dataset('eigenvalue_1', data=self.eigenvalue_1.transpose((2, 1, 0)))
            file.create_dataset('eigenvalue_2', data=self.eigenvalue_2.transpose((2, 1, 0)))
            file.create_dataset('eigenvalue_3', data=self.eigenvalue_3.transpose((2, 1, 0)))

            file.create_dataset('second_moment_tensor',
                                data=self.second_moment_tensor.transpose((2, 1, 0, 3, 4)))

        # Make XDMF file for paraview
        with open(filename + '.xdmf', 'w') as file:

            # Header
            file.write("""<?xml version="1.0" ?>
<!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []>
<Xdmf Version="2.0">
<Domain>
<Grid Name="Structured Grid" GridType="Uniform">
""")
            file.write('<Topology TopologyType="3DCoRectMesh" NumberOfElements="' +
                       f'{self.volume_shape[2]} {self.volume_shape[1]} {self.volume_shape[0]}"/>\n')
            file.write("""   <Geometry GeometryType="Origin_DxDyDz">
    <DataItem Name="Origin" Dimensions="3" NumberType="Float" Precision="8" Format="XML">
        0.5 0.5 0.5
    </DataItem>
    <DataItem Name="Spacing" Dimensions="3" NumberType="Float" Precision="8" Format="XML">
        1.0 1.0 1.0
    </DataItem>
</Geometry>

""")

            # Scalars
            for data_string in [
                    'mean_intensity',
                    'fractional_anisotropy',
                    'eigenvalue_1',
                    'eigenvalue_2',
                    'eigenvalue_3',]:
                file.write(f'<Attribute Name="{data_string}" AttributeType="Scalar" Center="Node">\n')
                file.write('    <DataItem Dimensions="' +
                           f'{self.volume_shape[2]} {self.volume_shape[1]} {self.volume_shape[0]}"' +
                           ' NumberType="Float" Precision="8" Format="HDF">\n')
                file.write(f'        {basename}.h5:/{data_string}')
                file.write("""
    </DataItem>
</Attribute>

""")

            # Vectors
            for data_string in [
                    'eigenvector_1',
                    'eigenvector_2',
                    'eigenvector_3',
                    'eigenvector_1_rgb',
                    'eigenvector_2_rgb',
                    'eigenvector_3_rgb',]:
                file.write(f'<Attribute Name="{data_string}" AttributeType="Vector" Center="Node">\n')
                file.write('    <DataItem Dimensions="' +
                           f'{self.volume_shape[2]} {self.volume_shape[1]} {self.volume_shape[0]} 3"' +
                           ' NumberType="Float" Precision="8" Format="HDF">\n')
                file.write(f'        {basename}.h5:/{data_string}')
                file.write("""
    </DataItem>
</Attribute>

""")

            file.write("""</Grid>
</Domain>
</Xdmf>
""")

        # Color legend
        with importlib.resources.path(__package__, 'color_map.png') as p:
            path = p
        shutil.copyfile(path, 'direction_colormap.png')


def get_colors_on_halfsphere(vectors: np.array) -> np.array:
    """ A colourmap on the unit halfsphere with inversion symmetry.
    Vectors along the `y` direction are grey and the 'x-z' equator goes through the
    hsv hue cycle. The +y+z and -y-z sections  are made brighter than the
    +y-z and -y+z sections such that the pairs (x, y, 0) and (x, -y, 0) are the
    only non-equivalent points given the same colour.

    Parameters
    ----------
    unit-vectors
        Array where the last dimension is of length 3, corresponding to the vector index.


    Returns
    -------
        Array of the same shape as the input where the third dimension is an RGB value in
        floating point format.

    """

    vectors = np.copy(vectors)
    whereflip = vectors[..., 1] < 0
    vectors[whereflip, :] = -vectors[whereflip, :]

    theta = np.arccos(vectors[..., 1])
    phi = np.arctan2(vectors[..., 2], vectors[..., 0])
    hue = ((phi) % (np.pi))/np.pi
    saturation = (np.arctan(theta/2) / np.arctan(np.pi/4))**2
    modifier = -np.sin(phi)*np.sin(2*theta)**2
    modifier = np.sign(modifier) * np.abs(modifier)
    value = np.ones(theta.shape)*0.7 + 0.2*modifier

    hsv = np.stack([hue, saturation, value], axis=-1)
    rgb_colours = hsv_to_rgb(hsv)
    return rgb_colours
