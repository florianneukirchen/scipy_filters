import hashlib
from osgeo import gdal
from qgis.core import QgsRasterLayer


def rasterhash(rlayer):
    if isinstance(rlayer, QgsRasterLayer):
        rlayer = rlayer.source()
    if not isinstance(rlayer, str):
        raise TypeError("rlayer must be a string (file path) or QgsRasterLayer")
    ds = gdal.Open(rlayer)
    data = ds.ReadAsArray()

    return hashlib.sha224(data.data).hexdigest()