import logging
import os
from typing import Dict, Any, Union, Tuple, List


import numpy as np
from numpy.typing import NDArray
import h5py as h5

logger = logging.getLogger(__name__)


def save_array_like(key: str, val: Union[Tuple, List, NDArray], group):
    val = np.array(val)
    if val.dtype.kind in 'fcbviuS':
        group.create_dataset(key, data=val, shape=val.shape)
    elif val.dtype.kind in 'U':
        val = val.astype(bytes)
        group.create_dataset(key, data=val, shape=val.shape)
    else:
        logger.warning(f'Data type {val.dtype} not supported, entry will be ignored!')


def save_item(key: str, val: Any, group):
    if val is None:
        logger.warning(f'Entry {key} has value None, which is not supported and will be ignored!')
        return
    if isinstance(val, np.ndarray) or type(val) in (list, tuple):
        save_array_like(key, val, group)
    else:
        val = np.array((val,))
        save_array_like(key, val, group)


def save_dict_recursively(inner_dict: Dict[str, Any], group):
    for key, val in inner_dict.items():
        if isinstance(val, dict):
            group.create_group(key)
            save_dict_recursively(val, group[key])
        else:
            save_item(key, val, group)


def dict_to_h5(dict_to_output: Dict[str, Any], filename: str, overwrite: bool = False) -> None:
    """Function for recursively saving a dictionary as an hdf5 file.

    Example
    -------
    The following snippet demonstrates how to save and read an example dictionary using this functionality.
    In this example, the output file will be overwritten in case it already exists.

    >>> from mumott.output_handling import dict_to_h5
    >>> dict_to_h5(dict_to_output=dict(a=5, b='123', c=dict(L=['test'])),
                   filename='my-example-dict.h5', overwrite=True)

    To read the output file (typically at some later point) we use the ``h5py.File`` context.
    Note that this does not restore the original dictionary.

    >>> import h5py
    >>> file = h5py.File('my-example-dict.h5')

    We can loop over the fields in the hdf5 file using the dict-functionality of the ``h5py.File`` class.

    >>> for k, v in file.items():
    ...     print(k, v)
    a <HDF5 dataset "a": shape (1,), type "<i8">
    b <HDF5 dataset "b": shape (1,), type "|S3">
    c <HDF5 group "/c" (1 members)>

    This allows us also to access individual fields

    >>> print(file['a'][0])
    5

    as well as nested data.

    >>> print(file['c/L'][:])
    [b'test']

    Parameters
    ----------
    dict_to_output
        A ``dict`` with supported entry types, including other ``dict``s. File will be recursively
        structured according to the structure of the ``dict``.
    filename
        The name of the file, including the full path, which will be output.
    overwrite
        Whether to overwrite an existing file with name :attr:`filename`. Default is ``False``.

    Notes
    -----
    Supported entry types in :attr:`dict_to_output`:
        ``int``, ``float``, ``complex``
            Saved as array of size ``1``.
        ``bytes``,  ``str``
            ``str`` is cast to ``bytes-like``. Saved as array of size ``1``.
        ``None``
            Ignored.
        ``np.ndarray``
            Provided ``dtype`` is not ``object``, ``datetime`` or ``timedelta,
            hence arrays of ``None`` are not allowed.
        ``list``, ``tuple``
            Provided they can be cast to allowed, i.e. non-ragged ``np.ndarray``.
        ``dict``
            Assuming entries are allowed types, including ``dict``.
    """
    if os.path.exists(filename) and not overwrite:
        raise FileExistsError('File already exists, and overwrite is set to False.')
    with h5.File(filename, 'w') as file_to_save:
        for key, val in dict_to_output.items():
            if isinstance(val, dict):
                file_to_save.create_group(key)
                save_dict_recursively(val, file_to_save[key])
            else:
                save_item(key, val, file_to_save)
    logger.info(f'File {filename} saved successfully!')
