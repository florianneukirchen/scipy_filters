import hashlib
from osgeo import gdal
from qgis.core import QgsRasterLayer
from qgis.utils import iface


def rasterhash(rlayer=None):
    """Return a SHA224 hash of the raster data for unittests

    Can be used to compare raster data between runs of the same algorithm.
    It is calucated in the same way as in QGIS core TestTools.py, 
    but more convienient to use e.g. in the console. 
    Default is the active layer.
    
    :param rlayer: raster layer or file path, default is active layer.
    :type rlayer: QgsRasterLayer or str, optional
    :return: SHA224 hash of the raster data
    :rtype: str
    """
    if rlayer is None:
        rlayer = iface.activeLayer()
    if isinstance(rlayer, QgsRasterLayer):
        rlayer = rlayer.source()
    if not isinstance(rlayer, str):
        raise TypeError("rlayer must be a string (file path) or QgsRasterLayer")
    ds = gdal.Open(rlayer)
    data = ds.ReadAsArray()

    return hashlib.sha224(data.data).hexdigest()