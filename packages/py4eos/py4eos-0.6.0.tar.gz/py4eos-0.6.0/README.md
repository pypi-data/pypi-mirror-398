Python Tools for HDF4-EOS Format
================================

Unfortunately, many important NASA datasets are still distributed as HDF4-EOS granules. These can be difficult or impossible to work with using GIS software. Even when opened using a library like GDAL, key spatial metadata are not accessed, resulting in the failure to fix the dataset's true spatial coordinates.

This small library may help you to avoid needing to install GDAL just to read the file. It is capable of reading an an HDF4 file (and HDF4-EOS files, in particular) and writing out a spatial dataset using `rasterio`, based on some strict assumptions about the file-level attributes; assumptions that are usually satisfied by an HDF4-EOS file.

The problems solved by `py4eos` include:

- Reading an HDF4-EOS file without needing `GDAL` installed
- Figuring out the coordinate reference system (CRS) and affine transformation of an HDF4-EOS granule
- Converting an HDF4-EOS file to a more convenient raster format
- Applying the scale and offset to an HDF4-EOS dataset's values to obtain true, geophysical values


Example Use
-----------

```python
import earthaccess
import py4eos

# Download a MOD16A3GF granule
result = earthaccess.search_data(
    short_name = 'MOD16A3GF',
    temporal = ('2014-01-01', '2014-12-31'),
    bounding_box = (-106, 42, -103, 43))
earthaccess.download(result, TEST_DIR)

# Write the file to a GeoTIFF
hdf = py4eos.read_hdf4eos(granule_mod16a3)
hdf.to_rasterio('ET_500m', 'output_file.tiff')
```


Installation
------------

The easiest way to install `py4eos` is using `mamba` (see [installation instructions](https://github.com/conda-forge/miniforge#mambaforge)) or `conda`. This is the recommended way to install `py4eos` on Windows or Mac OS X:

```sh
mamba install py4eos
```

If the HDF4, `zlib`, and `libjpeg` libraries are already installed, then you can use `pip` on any system to install `py4eos`:

```sh
pip install py4eos
```

**Installing dependencies on GNU/Linux:**

- On Ubuntu GNU/Linux: `sudo apt install python3-dev libhdf4-dev`

**Running the test suite,** from the root directory of the repository:

```sh
python -m pytest
```

**Because data has to be downloaded as part of running the tests, they may fail the first time. Try running once more.**


Acknowledgements
----------------

Development of the `py4eos` library was supported by a grant from NASA (80NSSC23K0864).
