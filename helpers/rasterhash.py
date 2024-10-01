import hashlib
from osgeo import gdal
from qgis.core import QgsRasterLayer
from qgis.utils import iface


def rasterhash(rlayer=None):
    if rlayer is None:
        rlayer = iface.activeLayer()
    if isinstance(rlayer, QgsRasterLayer):
        rlayer = rlayer.source()
    if not isinstance(rlayer, str):
        raise TypeError("rlayer must be a string (file path) or QgsRasterLayer")
    ds = gdal.Open(rlayer)
    data = ds.ReadAsArray()

    return hashlib.sha224(data.data).hexdigest()