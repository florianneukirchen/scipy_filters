import unittest
import os
import sys
import numpy as np
import numpy.testing as npt
from osgeo import gdal

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append('/usr/share/qgis/python/plugins')
sys.path.append(os.path.abspath(os.path.join(dir_path, '../../')))

from qgis.core import *
from scipy_filters.helpers.rasterhash import rasterhash
from scipy_filters.scipy_filters_provider import SciPyFiltersProvider
import processing
from processing.core.Processing import Processing

app = QgsApplication([], True)
app.setPrefixPath("/usr", True)
app.initQgis()

 
Processing.initialize()
provider = SciPyFiltersProvider()
QgsApplication.processingRegistry().addProvider(provider)

testfile = os.path.join(dir_path, "testimage_landsat.tif")

class TestStdVarFilter(unittest.TestCase):

    def test_std_alg(self):
        output = processing.run("scipy_filters:estimate_std", {'INPUT':testfile,'DIMENSION':0,'SIZES':'3, 3','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'e5263da8a61532e2566ddf2094bdda4f7b13942f0438bc38582eddd7', "Standard deviation hash does not match")

    def test_var_alg(self):
        output = processing.run("scipy_filters:estimate_var", {'INPUT':testfile,'DIMENSION':0,'SIZES':'3, 3','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '7787dd7d82459e80294b775ca954a9c67319d92088a62233dd54586a', "Variance hash does not match")

class TestSimpleStats(unittest.TestCase):

    def test_range_alg(self):
        output = processing.run("scipy_filters:range", {'INPUT':testfile,'DIMENSION':0,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0,'SIZES':'3, 3','FOOTPRINT':'','ORIGIN':'0, 0'})
        self.assertEqual(rasterhash(output['OUTPUT']), '8712fcc73a6d325e0f190a18c0d1ecc6f8c8c7c535d6c227261eaccb', 'Range hash does not match')

    def test_median_alg(self):
        output = processing.run("scipy_filters:median", {'INPUT':testfile,'DIMENSION':0,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0,'SIZES':'3, 3','FOOTPRINT':'','ORIGIN':'0, 0'})
        self.assertEqual(rasterhash(output['OUTPUT']), '2deeb9f3f770430af8a5facc6564d3f45eb5f6a0b7895e3b576468d0', 'Median hash does not match')

if __name__ == '__main__':
    unittest.main()           