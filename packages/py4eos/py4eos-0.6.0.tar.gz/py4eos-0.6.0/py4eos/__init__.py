'''
Tools for working with HDF4-EOS granules. Example uses:

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
'''

import numpy as np
import h5py
import rasterio as rio
from functools import cached_property
from affine import Affine
from pyhdf.SD import SD, SDC
from py4eos.srs import SRS

__version__ = '0.6.0'

PLATFORMS_SUPPORTED = ('MODIS', 'VIIRS', 'SMAP')

class HDF4EOS(object):
    '''
    Represents an HDF4-EOS granule.

    Parameters
    ----------
    dataset : pyhdf.SD
        A pyhdf Scientific Dataset (SD) instance
    platform : str
        The name of the data platform the SD originates from; currently
        limited to one of: ("MODIS",)
    '''
    MODIS_TILE_SIZE = 1111950.0 # Width and height of MODIS tile in projection plane
    GRID_DIM_TO_RES = { # Mapping of grid dimensions to spatial resolution
        'MODIS': {
            # 2400 x 2400 pixels ~= 500 meters, but really 463.3
            2400: MODIS_TILE_SIZE / 2400
        },
        'VIIRS': {
            2400: MODIS_TILE_SIZE / 2400
        },
        'SMAP': {
            964: 36000.0,
            1383: 25000.0,
            3856: 9000.0,
            11568: 3000.0,
            34704: 1000.0,
        }
    }
    GROUPS = {
        'VIIRS': 'HDFEOS/GRIDS/VIIRS_Grid_ETLE/Data Fields',
    }
    # One or more datasets that *might* exist in a dataset, if its
    #   (inconsistent) metadata don't provide any hints
    FIELDS_FOR_INFERENCE = {
        'SMAP': [
            'NEE/nee_mean',
            'Soil_Moisture_Retrieval_Data_AM/soil_moisture_dca',
        ]
    }

    def __init__(self, dataset, platform = 'MODIS'):
        self.dataset = dataset
        self.platform = platform
        if self.platform not in PLATFORMS_SUPPORTED:
            raise NotImplementedError(f'No support for the platform "{platform}"')

    @cached_property
    def attrs(self):
        if self.platform == 'MODIS':
            meta = self.dataset.attributes()['StructMetadata.0']
        elif self.platform == 'VIIRS':
            meta = self.dataset['HDFEOS INFORMATION/StructMetadata.0'][()]
            if hasattr(meta, 'decode'):
                meta = meta.decode('utf-8')
        elif self.platform == 'SMAP':
            # TODO SMAP metadata is implemented terribly; it is very difficult
            #   to extract all of it, so I'm leaving this for a later day
            meta = ''
        attrs = [line.split('=') for line in meta.replace('\t', '').split('\n')]
        # TODO This is quick and dirty; there are multiple nested
        #   attributes with similar names that will be overwritten when
        #   converitng to a dictionary; it's assumed they're not important
        attrs = list(filter(lambda x: len(x) == 2, attrs))
        return dict(attrs)

    @cached_property
    def crs(self):
        if self.platform in ('MODIS', 'VIIRS'):
            wkt = SRS[6842]
        elif self.platform == 'SMAP':
            wkt = SRS[6933] # Global EASE-Grid 2.0
        return wkt

    @cached_property
    def geotransform(self):
        # TODO Will need to generalize these two attribute checks when support
        #   beyond MODIS is added
        if self.platform in ('MODIS', 'VIIRS'):
            if 'UpperLeftPointMtrs' not in self.attrs.keys():
                raise KeyError('Could not determine upper-left corner coordinates; on one of the following is missing from the attributes: "UpperLeftPointMtrs"')
            if 'XDim' not in self.attrs.keys() or 'YDim' not in self.attrs.keys():
                raise KeyError('Could not determine spatial resolution; "XDim" and "YDim" missing from attributes')
            ul = list(map(float, self.attrs['UpperLeftPointMtrs'].strip('()').split(',')))
            ul_x, ul_y = ul
            xdim = int(self.attrs['XDim'])
        elif self.platform == 'SMAP':
            # These are the same for every global EASE-Grid 2.0, regardless of
            #   grid size; see pyl4c repository
            ul_x = -17367530.45
            ul_y = 7314540.83
            # For SMAP HDF5 files, we have to find a valid dataset before we
            #   can infer what the geotransform should be (because the SMAP
            #   products' metadata are inconsistent)
            xdim = None
            for field in self.FIELDS_FOR_INFERENCE[self.platform]:
                if field in self.dataset.keys():
                    _, xdim = self.dataset[field].shape
            if xdim is None:
                raise ValueError('Could not identify this SMAP product')
        xres = self.GRID_DIM_TO_RES[self.platform][xdim]
        return (ul_x, xres, 0, ul_y, 0, -xres)

    @property
    def subdatasets(self):
        return self.dataset.datasets() # Chain pyhdf.SD.SD.datasets()

    @cached_property
    def transform(self):
        return Affine.from_gdal(*self.geotransform)

    def get(
            self, field, dtype = None, nodata = None, scale_and_offset = False):
        '''
        Returns the array data for the subdataset (field) named.

        Parameters
        ----------
        field : str
            Name of the subdataset to access
        dtype : str or None
            Name of a NumPy data type, e.g., "float32" for `numpy.float32`
        nodata : int or float
            The NoData value to use; otherwise, defaults to the "_FillValue"
            attribute
        scale_and_offset: bool
            True to apply the scale and offset, if specified, in the dataset
            (Default: False)

        Returns
        -------
        numpy.ndarray
        '''
        assert not scale_and_offset or 'float' in dtype,\
            'Cannot apply scale and offset unless the output dtype is floating-point'
        if isinstance(self.dataset, h5py.File):
            _field = field
            if field not in self.dataset.keys():
                _field = f'{self.GROUPS[self.platform]}/{field}'
            ds = self.dataset[_field]
            attrs = self.dataset[_field].attrs
        else:
            ds = self.dataset.select(field)
            attrs = self.dataset.select(field).attributes()
        value = ds[:]
        if dtype is not None:
            dtype = getattr(np, dtype) # Convert from string to NumPy dtype
            value = value.astype(dtype)
        if scale_and_offset:
            assert '_FillValue' in attrs.keys() or nodata is not None,\
                'No "_FillValue" found in attributes; must provide a "nodata" argument'
            if nodata is None:
                nodata = attrs['_FillValue']
            # This is a floating-point type, so we can replace NoData with NaN
            value[value == nodata] = np.nan
            # Also fill values out-of-range with NaN
            if 'valid_range' in attrs.keys():
                vmin, vmax = attrs['valid_range']
                value[np.logical_or(value < vmin, value > vmax)] = np.nan
            if 'scale_factor' in attrs.keys() and 'add_offset' in attrs.keys():
                scale = float(attrs['scale_factor'])
                offset = float(attrs['add_offset'])
            return offset + value * scale
        return value

    def to_rasterio(
            self, field, filename, driver = 'GTiff', dtype = 'float32',
            nodata = None, scale_and_offset = False):
        '''
        Creates a `rasterio` dataset based on the specified HDF4-EOS dataset.
        User `driver = 'MEM'` for an in-memory dataset (no file written).

        Note that the file must be closed before it is written to disk, e.g.:

            hdf = py4eos.read_file(...)
            dset = hdf.to_rasterio(...)
            dset.close()

        Parameters
        ----------
        field : str
            Name of the subdataset to write to the output data file
        filename : str
            File path for the output file
        driver : str
            Name of the file driver; defaults to "GTiff" for GeoTIFF output
        dtype : str
            Name of a NumPy data type, e.g., "float32" for `numpy.float32`
            (Default)
        nodata : int or float
            The NoData value to use; otherwise, defaults to the "_FillValue"
            attribute
        scale_and_offset: bool
            True to apply the scale and offset, if specified, in the dataset
            (Default: False)

        Returns
        -------
        `rasterio.DatasetWriter`
        '''
        arr = self.get(field, dtype, nodata, scale_and_offset)
        rows, cols = arr.shape
        rast = rio.open(
            filename, 'w+', driver = driver, height = rows, width = cols,
            count = 1, dtype = getattr(np, dtype), crs = self.crs,
            transform = self.transform)
        rast.write(arr, 1)
        return rast


def read_file(filename, platform = None, mode = 'r'):
    '''
    Read an HDF4-EOS dataset and return an `HDF4EOS` object.

    Parameters
    ----------
    filename : str
        File path for the input HDF4-EOS file
    platform : str
        The name of the data platform the SD originates from; currently
        limited to one of: ("MODIS", "VIIRS"). Assumes "MODIS" by default.
    mode : str
        The file mode, should be "r" (read) or "w" ("write") (Default: "r")

    Returns
    -------
    HDF4EOS
    '''
    if platform is None or platform == 'MODIS':
        mode = SDC.WRITE if mode == 'w' else SDC.READ
        sd = SD(filename, mode = mode)
        dataset = HDF4EOS(sd)
    elif platform in ('VIIRS', 'SMAP'):
        sd = h5py.File(filename, mode)
        dataset = HDF4EOS(sd, platform = platform)
    return dataset


def read_hdf4eos(*args, **kwargs):
    '''
    Read an HDF4-EOS dataset and return an `HDF4EOS` object.

    Parameters
    ----------
    filename : str
        File path for the input HDF4-EOS file
    platform : str
        The name of the data platform the SD originates from; currently
        limited to one of: ("MODIS", "VIIRS"). Assumes "MODIS" by default.
    mode : str
        The file mode, should be "r" (read) or "w" ("write") (Default: "r")

    Returns
    -------
    HDF4EOS
    '''
    return read_file(*args, **kwargs)


if __name__ == '__main__':
    import fire
    fire.Fire(read_hdf4eos)
