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

    To be used in the QGIS Python console for raster processing with `numpy <https://numpy.org/>`_, 
    `SciPy <https://scipy.org/>`_, `scikit-image <https://scikit-image.org/>`_, `scikit-learn <https://scikit-learn.org/stable/>`_ 
    or other python libraries. Great for prototype development and experimenting with algorithms.

    The resulting numpy array can be loaded back into QGIS as a new raster layer, as long as the
    number of pixels is the same as the input layer and the geotransform is not changed (no reprojection, no subsetting in numpy).
    The number of bands and the datatype can be different. See :py:meth:`.toarray` and :py:meth:`.tolayer`.

    .. note:: As in QGIS and GDAL, the first band is indexed with 1 in :py:meth:`.toarray`. In NumPy it is indexed with 0.

    On very large rasters, the processing can be done in windows (tiles) to avoid crashes, see :py:meth:`.get_windows`.

    :param layer: instance of qgis.core.QgsRasterLayer, the layer to be processed. Optional, default is the active layer.
    :type layer: QgsRasterLayer, optional

    Example::

            from scipy_filters.helpers import RasterWizard
            from scipy import ndimage

            wizard = RasterWizard() # Uses active layer if layer is not given
            a = wizard.toarray()    # Returns numpy array with all bands

            # Any calculation, for example a sobel filter with Scipy
            # In the example, the result is a numpy array with dtype float32
            b = ndimage.sobel(a, output="float32") 

            # Write the result to a geotiff and load it back into QGIS
            wizard.tolayer(b, name="Sobel", filename="/path/to/sobel.tif")

            # You can also get pixel values at [x, y]
            wizard[0,10] 

            # or information like shape, CRS, etc.
            wizard.shape   # like numpy_array.shape
            wizard.crs_wkt # CRS as WKT string
            wizard.crs     # CRS as QgsCoordinateReferenceSystem

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

        if not isinstance(layer, QgsRasterLayer):
            raise TypeError("Layer is not a raster layer, must be QgsRasterLayer with a local file")
        
        if not layer.providerType() == "gdal":
            raise TypeError(f"Raster provider {layer.providerType()} is not supported, must be raster layer with a local file")

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
        :rtype: tuple
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

        :return: Path and filename
        :rtype: str
        """
        return self._filename
    
    @property
    def out_filename(self):
        """
        Path and filename of the output geotiff file.

        Is None if no output file is set. Normally, the output file is set when calling :py:meth:`tolayer`.
        When iterating over windows, the output file should be set with :py:meth:`.set_out_ds`.

        :return: Path or None
        :rtype: str or None
        """
        return self._out_filename
    
    @property
    def ds(self):
        """
        `GDAL <https://gdal.org/en/latest/>`_ dataset of the raster layer.

        :return: GDAL dataset
        :rtype: osgeo.gdal.Dataset
        """
        return self._ds
       
    @property
    def geotransform(self):
        """
        Geotransform of the raster layer as used by `GDAL <https://gdal.org/en/latest/>`_.

        The geotransform is a tuple with 6 elements of type float: 
        top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution.

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

        :return: CRS as qgis.core.QgsCoordinateReferenceSystem
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

        :return: True if axis order is inverted
        :rtype: bool
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

        .. note:: In GeoTiff, the same no data value is used for all bands.

        :param band: Band index, default is 1. The fist band is indexed with 1.
        :type band: int, optional
        :return: No data value
        :rtype: float or None
        """
        return self._ds.GetRasterBand(band).GetNoDataValue()
    
    
    def toarray(self, band=None, win=None, wrapping=False, bands_last=False):
        """
        Get the raster data as numpy array.

        With parameter band, a 2D array is returned; otherwise, all bands are returned as a 3D array 
        (or as 2D array if there is only one band). The order of the dimensions is [bands,] x, y.

        Alternatively, by setting :code:`bands_last=True`, the order of the dimensions is x, y [,bands] 
        (e.g. expected by scikit-image).

        .. note:: In QGIS and GDAL, the first band is indexed with 1, in numpy with 0.

        Can be used together with the RasterWindow class to calculate in a moving window, see :py:meth:`.get_windows` for an example.

        .. versionchanged:: 1.5
            Accept a string as band parameter to select a band by band description.

        :param band: Band index (int) or band description (str), default is None (all bands). The first band is indexed with 1. Using the band description returns the first band with the given name.
        :type band: int, str, optional
        :param win: RasterWindow instance for processing in a moving window, default is None
        :type win: RasterWindow, optional
        :param wrapping: Fill the margins of the window with the data of the far side of the dataset, to be used with scipy filters with mode='wrap', default is False
        :type wrapping: bool, optional
        :param bands_last: If True, the order of the dimensions is x, y [,bands], default is False, expecting [bands,] x, y
        :type bands_last: bool, optional
        :return: Numpy array with the raster data. 2D if only one band, 3D if multiple bands.
        :rtype: numpy.ndarray
        """
        if isinstance(band, str):
            if band == "":
                raise ValueError("Empty string is not a valid band description")
            band = self.banddesc().index(band) + 1 # ValueError if not in list

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
        Get the name of the `GDAL <https://gdal.org/en/latest/>`_ datatype of a band.

        :param band: Band index, default is 1. The fist band is indexed with 1.
        :type band: int, optional
        :param as_int: Return the datatype as integer instead, as defined in enum GDALDataType; default is False
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
    

    def banddesc(self):
        """
        Get a list of the band descriptions of the raster layer.

        Helps to find the right band for processing if the band descriptions of the layer are set.
        Otherwise, an empty string is returned for the respective band.
        The band descriptions can be set with GDAL, and QGIS shows a band name in the format "Band 1: description".
                
        To get the index of a band (in the NumPy) array by description, 
        use :code:`wizard.banddesc().index("description")`. 
        The band index in QGIS / GDAL or :py:meth:`tolayer` is + 1.

        .. versionadded:: 1.5

        :return: List of band descriptions
        :rtype: list
        """
        return [self._ds.GetRasterBand(i).GetDescription() for i in range(1, self._ds.RasterCount + 1)]
    

    def _memfile(self):
        """
        Get a virtual filename, the file will be written to memory only.
        """
        name = uuid.uuid4().hex
        return f"/vsimem/{name}.tif"


    def set_out_ds(self, filename=None, bands=None, dtype=None, nodata=None, banddesc=None):
        """
        Set up a new output dataset for writing.

        Only to be used directly when iterating over windows, see :py:meth:`.get_windows` for example.
        Otherwise, the output is set in :py:meth`tolayer`.

        With default values, the file is written to memory only and has the dtype matching the NumPy array.

        .. versionchanged:: 1.5
            It is now possible to set the band descriptions with the banddesc parameter. They show up in QGIS as "Band 1: description".

        :param filename: Filename or full file path for the output geotiff, default is None (in-memory only)
        :type filename: str, optional
        :param bands: Number of bands in the output dataset, default is None (same as input)
        :type bands: int, optional
        :param dtype: Datatype of the output dataset, accepts numpy dtypes: "uint8", "int8", "uint16", "int16", "uint32", "int32", "float32", "float64", "complex64", "complex128"
            default is None, using the datatype of the input layer (same as "input"). 
        :type dtype: str, optional
        :param nodata: No data value, default is None
        :type nodata: int, optional
        :param banddesc: List of band descriptions, default is None
        :type banddesc: list of str, optional
        """
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

        # Set band descriptions
        if banddesc and isinstance(banddesc, list):
            for i in range(bands):
                if i < len(banddesc):
                    self._dst_ds.GetRasterBand(i+1).SetDescription(str(banddesc[i]))


    def tolayer(self, array, name="Wizard", dtype="auto", filename=None, stats=True, bands_last=False, nodata=None, banddesc=None):
        """
        Save a numpy array as geotiff or in-memory and load it as a new raster layer in QGIS.

        The array must have the same dimensions in x and y as the input layer. The number of bands and the datatype can be different.
        By default, the datatype is inferred from the NumPy array.
        First, the data is saved as geotiff if a filename (full file path) is given. Otherwise, the geotiff is in-memory only, using `GDAL <https://gdal.org/en/latest/>`_ virtual file system.

        If iterating over windows, use :py:meth:`.write_window` and :py:meth:`.load_output` instead.

        .. versionchanged:: 1.5
            It is now possible to set the band descriptions with the banddesc parameter. They show up in QGIS as "Band 1: description".

        :param array: Numpy array with the raster data
        :type array: numpy.ndarray
        :param name: Name of the new layer in QGIS, default is "Wizard"
        :type name: str, optional
        :param dtype: Datatype of the output layer, accepts numpy dtypes: "uint8", "int8", "uint16", "int16", "uint32", "int32", "float32", "float64", "complex64", "complex128"
            default is "auto", using the `GDAL <https://gdal.org/en/latest/>`_ datatype matching the numpy array datatype. 
            "input" uses the datatype of the input layer.
        :type dtype: str, optional
        :param filename: Filename or full file path for the output geotiff, default is None (in-memory only)
        :type filename: str, optional
        :param stats: Calculate and write band statistics (min, max, mean, std), default is True
        :type stats: bool, optional
        :param bands_last: If True, the order of the dimensions is x, y [,bands], default is False, expecting [bands,] x, y
        :type bands_last: bool, optional
        :param nodata: No data value, default is None
        :type nodata: int, optional
        :param banddesc: List of band descriptions, default is None
        :type banddesc: list of str, optional
        :return: QgsRasterLayer instance of the new layer
        :rtype: QgsRasterLayer
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

        self.set_out_ds(filename=filename, bands=bands, dtype=dtype, banddesc=banddesc)

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
    

    def number_of_windows(self, windowsize=5000):
        """
        Returns the number of windows that would be generated with :py:meth:`.get_windows` with a given windowsize. 
        
        Since :py:meth:`.get_windows` is a generator, it can only be used once. 
        Use this function to get the number of windows if you need it for a progress bar etc.

        :param windowsize: Size of the windows in pixels, default is 2048
        :type windowsize: int, optional
        :return: Number of windows
        :rtype: int
        """
        return number_of_windows(self._ds.RasterXSize, self._ds.RasterYSize, windowsize)
    
    def get_windows(self, windowsize=5000, margin=0):
        """
        Generator to get windows for processing large rasters in tiles.

        The generated windows are instances of :py:class:`RasterWindow`. These do not contain the data, 
        only the pixel indices and sizes that are used internally to read and write the data with `GDAL <https://gdal.org/en/latest/>`_.
        You can iterate over the generated windows, read the data with :py:meth:`.toarray` and write the data with :py:meth:`.write_window`.
        The output dataset should be set first with :py:class:`set_out_ds()`, otherwise a virtual in-memory file is used.
        After processing all windows, the file is written and loaded back into QGIS with :py:meth:`load_output`.

        Note that numpy, scipy etc. are very performant on large arrays. It is best to use a 
        large windowsize or even the whole raster, as long as enough memory is avaible.
        The windows can have a margin, for algorthims that consider the neighborhood of a pixel as well.
        For example, a 3x3 kernel needs a margin of 1.

        If you need the number of windows (e.g. for a progress bar), use :py:meth:`.number_of_windows`.

        :param windowsize: Size of the windows in x and y direction in pixels, default is 5000
        :type windowsize: int, optional
        :param margin: Size of the margin in pixels, default is 0
        :type margin: int, optional

        :return: Generator yielding :py:class:`RasterWindow` instances

        Example::

            from scipy_filters.helpers import RasterWizard
            from scipy import ndimage

            wizard = RasterWizard()

            wizard.set_out_ds(filename="/path/to/sobel.tif", dtype="float32")

            for win in wizard.get_windows(windowsize=2048, margin=1):
                a = wizard.toarray(win=win)
                # Your calculation with numpy array a
                a = ndimage.sobel(a, output="float32")
                wizard.write_window(a, win)

            wizard.load_output()

        """
        if margin > windowsize / 2:
            print("Note: margins are larger than windowsize")
        return get_windows(self._ds.RasterXSize, self._ds.RasterYSize, margin=margin, windowsize=windowsize)

    def write_window(self, array, win, band=None, bands_last=False):
        """
        Write a numpy array into the window of the output dataset.

        The window is an instance of :py:class:`RasterWindow`, generated with :py:meth:`.get_windows`. 
        The margin of the window is automatically sliced off before writing the data back to the raster.
        After processing all windows, the file is written and loaded back into QGIS with :py:meth:`.load_output`.
        For a full example with reading and writing windows and loading the result,
        see :py:meth:`.get_windows`.

        :param array: Numpy array with the data to be written
        :type array: numpy.ndarray
        :param win: Window, RasterWindow instance
        :type win: RasterWindow
        :param band: Band index, default is None (all bands). The fist band is indexed with 1.
        :type band: int, optional
        :param bands_last: If True, the order of the dimensions is x, y [,bands], default is False, expecting [bands,] x, y
        :type bands_last: bool, optional
        """
        if not isinstance(win, RasterWindow):
            raise TypeError("Window must be instance of RasterWindow")
        
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

        if self._out_nodata:
            # Replace nan with no data value
            array[np.isnan(array)] = self._out_nodata

        if band is None:
            dst_ds = self._dst_ds
        else:
            dst_ds = self._dst_ds.GetRasterBand(band)

        slices = win.getslice(array.ndim)
        dst_ds.WriteArray(array[slices], *win.gdalout)

        
    def load_output(self, name="Wizard", stats=True):
        """
        After processing windows, write the output file and load it back into QGIS.

        The output file is written to the path given with :py:meth:`set_out_ds` or to a virtual in-memory file.
        See :py:meth:`.get_windows` for a full example.

        :param name: Name of the new layer in QGIS, default is "Wizard"
        :type name: str, optional
        :param stats: Calculate and write band statistics (min, max, mean, std), default is True
        :type stats: bool, optional
        :return: QgsRasterLayer instance of the new layer
        :rtype: QgsRasterLayer
        """
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