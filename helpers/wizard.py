# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
                              -------------------
        begin                : 2024-03-03
        copyright            : (C) 2024 by Florian Neukirchen
        email                : mail@riannek.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Florian Neukirchen'
__date__ = '2024-03-03'
__copyright__ = '(C) 2024 by Florian Neukirchen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import *
from qgis.utils import iface
from osgeo import gdal
import numpy as np
import uuid

from .window import RasterWindow, get_windows, number_of_windows, wrap_margin

gdal.UseExceptions()

class RasterWizard():
    """
    Get QGIS raster layers as numpy arrays and the result back into QGIS as a new raster layer. 

    To be used in the QGIS Python console for raster processing with numpy, scipy, scikit-image, sklearn 
    or other python libraries. Great for prototype development and experimenting with algorithms.

    The resulting numpy array can be loaded back into QGIS as a new raster layer, as long as the
    number of pixels is the same as the input layer and the geotransform is not changed (no reprojection, no subsetting in numpy).
    The number of bands and the datatype can be different.

    On very large rasters, the processing can be done in windows (tiles) to avoid crashes.

    :param layer: instance of QgsRasterLayer, the layer to be processed. Optional, default is the active layer.
    :type layer: QgsRasterLayer, optional

    Example::
            from scipy_filters.helpers import RasterWizard
            wizard = RasterWizard()
            a = wizard.toarray() # Returns 3D numpy array with all bands
            a = a.mean(axis=0)   # Or any other calculation
            wizard.tolayer(a, name="Mean", filename="/path/to/mean.tif")
    """

    _ds = None
    _dst_ds = None
    _layer = None

    # Mapping of numpy datatypes to GDAL datatypes
    _gdal_datatypes = {
        "uint8": 1,
        "int8": 1,
        "uint16": 2,
        "int16": 3,
        "uint32": 4,
        "int32": 5,
        "float32": 6,
        "float64": 7,
        "complex64": 10,
        "complex128": 11,
        }

    def __init__(self, layer=None):

        if layer is None:
            layer = iface.activeLayer()

        self._layer = layer
        self._filename = layer.source()
        self._out_filename = None
        self._dst_ds = None
        self._ds = gdal.Open(self._filename)
        self._name = layer.name()
        if not self._ds:
            raise FileNotFoundError("Could not open layer with GDAL")


    def __str__(self):
        return f"<RasterWizard: '{self._name}'>"


    def __repr__(self):
        return f"<RasterWizard: '{self._name}' shape: {self.shape}>"
    
    def __getitem__(self, items):
        """
        Get pixel values at [x, y].

        Returns 1-D numpy array with pixel values of all bands at indices x and y.
        With x or y out of bounds, NaNs are returned.

        Usage::

            wizard = RasterWizard()
            wizard[0,10] # Pixel at x = 0 and y = 10

        """
        try:
            x, y = items
        except (ValueError, TypeError):
            raise IndexError("Two indices of type int are required: x and y")
        
        if not (isinstance(x, int) and isinstance(x, int)):
            raise IndexError("Two indices of type int are required: x and y")
        
        if x < 0 or y < 0 or x >= self._ds.RasterYSize or y >= self._ds.RasterXSize:
            # Return nans if out of bounds
            a = np.empty(self._ds.RasterCount)
            a[:] = np.nan
            return a
        # Numpy x axis is y in gdal and vica versa
        return self._ds.ReadAsArray(y,x,1,1).reshape(-1)

    @property
    def countbands(self):
        """
        Number of bands in the raster layer.

        :return: Number of bands
        :rtype: int
        """
        return self._ds.RasterCount

    @property
    def ndim(self):
        """
        Number of dimensions of the raster layer.

        Returns 2 for single band and 3 for multiple bands.

        :return: Number of dimensions
        :rtype: int
        """
        if self._ds.RasterCount == 1:
            return 2
        else:
            return 3
        
    @property
    def shape(self) -> tuple[int]:
        """
        Shape of the raster layer
         
        Given in the order (bands, x, y); identical to numpy_array.shape 

        :return: Shape of the raster layer
        """
        # Numpy x axis is y in gdal and vica versa
        return (self._ds.RasterCount, self._ds.RasterYSize, self._ds.RasterXSize)
    
    @property
    def name(self):
        """
        Name of the raster layer in QGIS.

        :return: Layer name
        :rtype: str
        """
        return self._name
    
    @property
    def filename(self):
        """
        Path and filename of the raster layer source file.

        :return: Path
        :rtype: str
        """
        return self._filename
    
    @property
    def out_filename(self):
        return self._out_filename
    
    @property
    def ds(self):
        """
        GDAL dataset of the raster layer.

        :return: GDAL dataset
        :rtype: osgeo.gdal.Dataset
        """
        return self._ds
       
    @property
    def geotransform(self):
        """
        Geotransform of the raster layer as used by GDAL.

        :return: Geotransform
        :rtype: tuple
        """
        return self._ds.GetGeoTransform()

    @property
    def crs_wkt(self):
        """
        Get the CRS of the layer as WKT string.

        :return: CRS as WKT string
        :rtype: str
        """
        return self._ds.GetProjection()

    @property
    def crs(self):
        """
        Get the CRS of the layer as QgsCoordinateReferenceSystem.

        :return: CRS
        :rtype: QgsCoordinateReferenceSystem
        """
        return self._layer.crs()

    @property
    def crs_id(self):
        """
        Get the authority identifier of the CRS.

        Returns a string like "EPSG:4326".

        :return: CRS authority identifier
        :rtype: str
        """
        return self._layer.crs().authid()
    
    @property
    def has_axis_inverted(self):
        """
        Returns True if the axis order of the CRS is inverted,
        i.e. not east/north (longitude/latitude).
        """
        return self._layer.crs().hasAxisInverted()
    
    @property
    def pixel_width(self):
        """
        Returns the width of a pixel in map units, read from the geotransform.

        :return: Pixel width
        :rtype: float
        """
        return np.abs(self.geotransform[1])
    
    @property
    def pixel_height(self):
        """
        Returns the height of a pixel in map units, read from the geotransform.

        :return: Pixel height
        :rtype: float
        """
        return np.abs(self.geotransform[5])
    
    @property
    def is_geographic(self):
        """
        Returns True if the CRS is geographic (i.e. not projected).

        :return: True if geographic CRS
        :rtype: bool
        """
        return self._layer.crs().isGeographic()
    
    @property
    def map_units(self):
        """
        Return the units for the projection used by the CRS.

        :return: Map units
        :rtype: Qgis.DistanceUnit enum
        """
        return self._layer.crs().mapUnits()
    
    def nodata(self, band=1):
        """
        Get the no data value of a band. If no no data value is set, None is returned.

        Note: In GeoTiff, the same no data value is used for all bands.

        :param band: Band index, default is 1
        :type band: int, optional
        :return: No data value
        """
        return self._ds.GetRasterBand(band).GetNoDataValue()
    
    
    def toarray(self, band=None, win=None, wrapping=False, bands_last=False):
        """
        Get the raster data as numpy array.

        With parameter band, a 2D array is returned; otherwise, all bands are returned as a 3D array 
        (or as 2D array if there is only one band). The order of the dimensions is [bands,] x, y.

        Alternatively, by setting bands_last=True, the order of the dimensions is x, y [,bands] 
        (e.g. expected by scikit-image).

        Can be used together with the RasterWindow class to calculate in a moving window.

        :param band: Band index, default is None
        :type band: int, optional
        :param win: RasterWindow instance for processing in a moving window, default is None
        :type win: RasterWindow, optional
        :param wrapping: Fill the margins of the window with the data of the far side of the dataset, to be used with scipy filters with mode='wrap', default is False
        """
        if band is None:
            ds = self._ds
        else:
            band = int(band) # just in case
            if band < 1 or band > self._ds.RasterCount:
                raise IndexError("Band index out of range")
            ds = self._ds.GetRasterBand(band)

        if win is None:
            a = ds.ReadAsArray()
            if bands_last and a.ndim == 3:
                a = a.transpose(1,2,0)
            return a
        
        if not isinstance(win, RasterWindow):
            raise TypeError("Window must be instance of RasterWindow")
        
        a = ds.ReadAsArray(*win.gdalin)
        if wrapping:
            wrap_margin(a, self._ds, win, band=band)

        if bands_last and a.ndim == 3:
            a = a.transpose(1,2,0)

        return a
    

    def datatype(self, band=1, as_int=False):
        """
        Get the name of the GDAL datatype of a band.

        :param band: Band index, default is 1
        :type band: int, optional
        :param as_int: Return the datatype as integer instead, as defined in enum GDALDataType, default is False
        :type as_int: bool, optional
        :return: GDAL Datatype as string or integer
        """
        band = int(band) # just in case
        if band < 1 or band > self._ds.RasterCount:
            raise IndexError("Band index out of range")

        i = self._ds.GetRasterBand(band).DataType
        
        if as_int:
            return i
        
        return gdal.GetDataTypeName(i)
    

    def _memfile(self):
        """
        Get a virtual filename, the file will be written to memory only.
        """
        name = uuid.uuid4().hex
        return f"/vsimem/{name}.tif"


    def set_out_ds(self, filename=None, bands=None, dtype=None, nodata=None):
        # To be used by other functions
        # TODO
        self._out_nodata = nodata

        if not filename:
            self._out_filename = self._memfile()
        else:
            self._out_filename = filename

        if (not dtype) or (dtype=="input"):
            dtype = self.datatype(as_int=True)    
        else:
            try:
                dtype = str(dtype)
                dtype = self._gdal_datatypes[dtype]
            except (NameError, KeyError):
                raise ValueError("Invalid dtype")

        if not bands:
            bands = self.countbands

        driver = gdal.GetDriverByName("GTiff")

        dst_ds =  driver.Create(
            self._out_filename,
            xsize = self._ds.RasterXSize,
            ysize = self._ds.RasterYSize,
            bands = bands,
            eType = dtype,
        )

        if not dst_ds:
            raise OSError("Failed to create output GDAL dataset")

        dst_ds.SetGeoTransform(self.geotransform)
        dst_ds.SetProjection(self._ds.GetProjection())

        self._dst_ds = dst_ds

    def tolayer(self, array, name="Wizard", dtype="auto", filename=None, stats=True, bands_last=False, nodata=None):
        """
        Load a numpy array as a new raster layer in QGIS.

        The array must have the same dimensions in x and y as the input layer. The number of bands and the datatype can be different.
        First, the data is saved as geotiff if a filename (full file path) is given. Otherwise, the geotiff is in-memory only, using GDAL virtual file system.

        If iterating over windows, use write_window() and load_output() instead.

        :param array: Numpy array with the raster data
        :type array: numpy.ndarray
        :param name: Name of the new layer in QGIS, default is "Wizard"
        :type name: str, optional
        :param dtype: Datatype of the output layer, accepts numpy dtypes: "uint8", "int8", "uint16", "int16", "uint32", "int32", "float32", "float64", "complex64", "complex128"
            default is "auto", using the GDAL datatype matching the numpy array datatype. 
            "input" uses the datatype of the input layer.
        :type dtype: str, optional
        :param filename: Full file path for the output geotiff, default is None (in-memory only)
        :type filename: str, optional
        :param stats: Calculate and write band statistics (min, max, mean, std), default is True
        :type stats: bool, optional
        :param bands_last: If True, the order of the dimensions is x, y [,bands], default is False, expecting [bands,] x, y
        :type bands_last: bool, optional
        :param nodata: No data value, default is None
        :type nodata: int, optional
        """

        if nodata:
            # Replace nan with no data value
            array[np.isnan(array)] = nodata

        if bands_last and array.ndim == 3:
            array = array.transpose(2,0,1)
    
        if not (array.shape[-1] == self.shape[-1] and array.shape[-2] == self.shape[-2]):
            raise ValueError("Array must have same shape in X and Y directions as the input layer")
        if array.ndim not in (2, 3):
            raise ValueError("Array must be 2D or 3D")
        if array.ndim == 2:
            bands = 1
        else:
            bands = array.shape[0]

        if dtype == "auto":
            dtype = array.dtype

        self.set_out_ds(filename=filename, bands=bands, dtype=dtype)

        if bands == 1:
            self._dst_ds.GetRasterBand(1).WriteArray(array)
        else:
            self._dst_ds.WriteArray(array)

        if nodata:
            for b in range(1, bands + 1):
                self._dst_ds.GetRasterBand(b).SetNoDataValue(nodata)

        # Calculate and write band statistics (min, max, mean, std)
        if stats:
            for b in range(1, bands + 1):
                band = self._dst_ds.GetRasterBand(b)
                stats = band.GetStatistics(0,1)
                band.SetStatistics(*stats)
        
        # Close (and write) file
        self._dst_ds = None

        layer = QgsRasterLayer(self._out_filename, name, 'gdal')

        if not layer.isValid():
            print("Loading the layer failed. Filename: {self._out_filename}")
            return self._out_filename

        QgsProject.instance().addMapLayer(layer)

        return layer
    

    def number_of_windows(self, windowsize=2048):
        """
        Returns the number of windows that would be generated with get_windows() with a given windowsize. 
        
        Since get_windows() is a generator, it can only be used once. 
        Use this function to get the number of windows if you need it for a progress bar etc.

        :param windowsize: Size of the windows in pixels, default is 2048
        :type windowsize: int, optional
        :return: Number of windows
        :rtype: int
        """
        return number_of_windows(self._ds.RasterXSize, self._ds.RasterYSize, windowsize)
    
    def get_windows(self, windowsize=2048, margin=0):
        # TODO
        if margin > windowsize / 2:
            print("Note: margins are larger than windowsize")
        return get_windows(self._ds.RasterXSize, self._ds.RasterYSize, margin=margin, windowsize=windowsize)

    def write_window(self, array, win, band=None, bands_last=False):
        # TODO
        if not isinstance(win, RasterWindow):
            raise TypeError("Window must be instance of RasterWindow")
        
        if self._out_nodata:
            # Replace nan with no data value
            array[np.isnan(array)] = self._out_nodata

        if bands_last and array.ndim == 3:
            array = array.transpose(2,0,1)
        
        if self._dst_ds is None:
            # We create a output ds matching the first array as default option
            # Otherwise set_out_ds() should be called first
            if array.ndim == 2:
                bands = 1
            else:
                bands = array.shape[0]
            self.set_out_ds(bands=bands, dtype=array.dtype)

        if band is None:
            dst_ds = self._dst_ds
        else:
            dst_ds = self._dst_ds.GetRasterBand(band)

        slices = win.getslice(array.ndim)
        dst_ds.WriteArray(array[slices], *win.gdalout)

        
    def load_output(self, name="Wizard", stats=True):
        # TODO
        if self._dst_ds is None:
            raise Exception("No output dataset")
        
        if self._out_nodata:
            for b in range(1, self._dst_ds.RasterCount + 1):
                self._dst_ds.GetRasterBand(b).SetNoDataValue(self._out_nodata)

        # Calculate and write band statistics (min, max, mean, std)
        if stats:
            for b in range(1, self._dst_ds.RasterCount + 1):
                band = self._dst_ds.GetRasterBand(b)
                stats = band.GetStatistics(0,1)
                band.SetStatistics(*stats)
        
        # Close (and write) file
        self._dst_ds = None

        layer = QgsRasterLayer(self._out_filename, name, 'gdal')

        if not layer.isValid():
            print("Loading the layer failed. Filename: {self._out_filename}")
            return self._out_filename

        QgsProject.instance().addMapLayer(layer)

        return layer