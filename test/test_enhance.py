import unittest
import os
import sys
import numpy as np
import numpy.testing as npt
from osgeo import gdal
from qgis.core import *
from scipy_filters.helpers.rasterhash import rasterhash


dir_path = os.path.dirname(os.path.realpath(__file__))

app = QgsApplication([], True)
# app.setPrefixPath("/usr/lib/qgis/plugins", True)
app.setPrefixPath("/usr", True)
app.initQgis()

sys.path.append('/usr/share/qgis/python/plugins')
sys.path.append(os.path.abspath(os.path.join(dir_path, '../../')))

from scipy_filters.scipy_filters_provider import SciPyFiltersProvider
import processing
from processing.core.Processing import Processing
 
Processing.initialize()
# QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
provider = SciPyFiltersProvider()
QgsApplication.processingRegistry().addProvider(provider)


testfile = os.path.join(dir_path, "testimage_landsat.tif")


class TestEnhanceFilters(unittest.TestCase):

    def test_unsharp_mask(self):
        output = processing.run("scipy_filters:unsharp_mask", {'INPUT':testfile,'DIMENSION':0,'AMOUNT':1,'SIGMA':5,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '2e72c15a53efec0413428a122c1d4afa80d335f73becb7e9d3e5c3f6', "Unsharp mask hash does not match")

    def test_wiener(self):
        output = processing.run("scipy_filters:wiener", {'INPUT':testfile,'DIMENSION':0,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','NOISE':None})
        self.assertEqual(rasterhash(output['OUTPUT']), 'f029b5e390547509ff67af615b70a3045fb37ac11fe10d8c02bbff64', "Wiener filter hash does not match")