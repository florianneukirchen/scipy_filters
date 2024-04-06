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
from osgeo import gdal
import numpy as np
import uuid

from .window import RasterWindow, get_windows, number_of_windows, wrap_margin

gdal.UseExceptions()

class Wizard():

    _ds = None
    _dst_ds = None
    _layer = None

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

    def __init__(self, layer):
        self._layer = layer
        self._filename = layer.source()
        self._ds = gdal.Open(self._filename)
        self._name = layer.name()
        if not self._ds:
            raise FileNotFoundError("Could not open layer with GDAL")


    def __str__(self):
        return f"<MyRaster: '{self._name}' (gdal)>"


    def __repr__(self):
        return f"<MyRaster: '{self._name}' (gdal)>"
    
    def __getitem__(self, items):
        """Returns 1-D numpy array with pixel values of all bands at indices x and y"""
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
        return self._ds.RasterCount

    @property
    def ndim(self):
        if self._ds.RasterCount == 1:
            return 2
        else:
            return 3
        
    @property
    def shape(self):
        # Numpy x axis is y in gdal and vica versa
        return (self._ds.RasterCount, self._ds.RasterYSize, self._ds.RasterXSize)
    
    @property
    def name(self):
        return self._name
    
    @property
    def filename(self):
        return self._filename
    
    @property
    def geotransform(self):
        return self._ds.GetGeoTransform()
    
    def crs_wkt(self):
        return self._ds.GetProjection()
    
    def crs(self):
        return self._layer.crs()
    
    def crs_id(self):
        return self._layer.crs().authid()
    
    @property
    def hasAxisInverted(self):
        return self._layer.crs().hasAxisInverted()
    
    def isGeographic(self):
        return self._layer.crs().isGeographic()
    
    def mapUnits(self):
        return self._layer.crs().mapUnits()
    
    def toarray(self):
        return self._ds.ReadAsArray()
    
    def band(self, idx):
        idx = int(idx) # just in case
        if idx < 1 or idx > self._ds.RasterCount:
            raise IndexError("Band index out of range")
        return self._ds.GetRasterBand(idx).ReadAsArray()

    def datatype(self, band=1, as_int=False):
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


    def outdataset(self, filename=None, bands=None, dtype=None, name=None):
        if not filename:
            filename = self._memfile()

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
            filename,
            xsize = self._ds.RasterXSize,
            ysize = self._ds.RasterYSize,
            bands = bands,
            eType = dtype,
        )

        if not dst_ds:
            raise OSError("Failed to create output GDAL dataset")

        dst_ds.SetGeoTransform(self.geotransform)
        dst_ds.SetProjection(self._ds.GetProjection())

        return dst_ds, filename

    def tolayer(self, array, name="MyRaster", dtype="auto", filename=None, stats=True):
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


        dst_ds, filename = self.outdataset(filename=filename, bands=bands, dtype=dtype)

        if bands == 2:
            dst_ds.GetRasterBand(1).WriteArray(array)
        else:
            dst_ds.WriteArray(array)

        # Calculate and write band statistics (min, max, mean, std)
        if stats:
            for b in range(1, bands + 1):
                band = dst_ds.GetRasterBand(b)
                stats = band.GetStatistics(0,1)
                band.SetStatistics(*stats)
        
        # Close (and write) file
        dst_ds = None

        layer = QgsRasterLayer(filename, name, 'gdal')

        if not layer.isValid():
            print("Loading the layer failed. Filename: {filename}")
            return filename

        QgsProject.instance().addMapLayer(layer)

        return layer
        

    def number_of_windows(self, windowsize):
        return number_of_windows(rasterXSize, rasterYSize, windowsize)
