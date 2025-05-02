import hashlib
from osgeo import gdal
from qgis.core import QgsRasterLayer
from qgis.utils import iface


def rasterhash(rlayer=None):
    """Return a SHA224 hash of the raster data

    For unit testing. Getting the hash of a layer quickly helps to write unit tests faster.
    Can be used to compare raster data between runs of the same algorithm.
    It is calucated in the same way as in QGIS core TestTools.py, 
    but more convienient to use e.g. in the console. 
    Parameter rlayer is a QGIS raster layer or a file path to a raster file.
    Default is the active layer.
    
    :param rlayer: raster layer or file path, default is active layer.
    :type rlayer: QgsRasterLayer or str, optional
    :return: SHA224 hash of the raster data
    :rtype: str

    Example:: 
        >>> from scipy_filters.helpers import rasterhash
        >>> rasterhash()
        'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2'
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