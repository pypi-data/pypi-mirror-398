'''
Tests for input-output of EOS-HDF4 datasets.
'''

import glob
import os
import numpy as np
import pytest
import earthaccess
import rasterio as rio
import py4eos
from py4eos import read_hdf4eos
from test_formats import granule_mod15a2h

TEST_DIR = os.path.join(os.path.dirname(py4eos.__file__), '../tests')


def test_to_rasterio(granule_mod15a2h):
    'Test that the `to_rasterio()` method works as expected'
    hdf = read_hdf4eos(granule_mod15a2h)
    ds = hdf.to_rasterio('Lai_500m', filename = '', driver = 'MEM')
    arr = ds.read(1)
    assert isinstance(ds, rio.io.DatasetWriter)
    assert isinstance(arr, np.ndarray)
