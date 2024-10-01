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


class TestPixelStats(unittest.TestCase):

    def test_pixel_mean_alg(self):
        output = processing.run("scipy_filters:pixel_mean", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'e9958307ed391e4936c044ac09e93e55bb2d124fae4efb0c9ac03769', "Pixel mean hash does not match")

    def test_pixel_max_alg(self):
        output = processing.run("scipy_filters:pixel_max", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'ec1a07e8a4ca76a4fd942f53d80530d4fcab3abc0a948a2d4f208cca', "Pixel max hash does not match")


    def test_pixel_gradient(self):
        output = processing.run("scipy_filters:pixel_gradient", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','ABSOLUTE':False})
        self.assertEqual(rasterhash(output['OUTPUT']), 'cc800502b7f8e0514c5e660c90f2339825ac2cfcdf2c22e97c7abe91', "Pixel gradient hash does not match")

        # Absolute = True
        output = processing.run("scipy_filters:pixel_gradient", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','ABSOLUTE':True})
        self.assertEqual(rasterhash(output['OUTPUT']), 'f0f2c2727becc2a5e1e579a2daf87f95307be39da058ca0c1c9cc464', "Pixel gradient hash with absolute values does not match")

    def test_pixel_difference(self):

        output = processing.run("scipy_filters:pixel_difference", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','ABSOLUTE':False})
        self.assertEqual(rasterhash(output['OUTPUT']), '769a97e1366ae7dd36b5a48a98d9c97529d3b5df775dd8379507a8b3', "Pixel difference hash does not match")

        # Absolute = True
        output = processing.run("scipy_filters:pixel_difference", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','ABSOLUTE':True})
        self.assertEqual(rasterhash(output['OUTPUT']), '455621b633be7eba12c0f1c48fb2eb6d4be5a430de6108aa7bdc3370', "Pixel difference hash with absolute value does not match")


class TestPixelStdVar(unittest.TestCase):

    def test_pixel_std_alg(self):
        output = processing.run("scipy_filters:pixel_std", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'e9f81c89a470b0c321d1cd3afe5fc06e23bec712728b77fe258bff15', "Pixel standard deviation hash does not match")

    def test_pixel_var_alg(self):
        output = processing.run("scipy_filters:pixel_variance", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '528f63fa5b212a18c3f15bbe07c8f331ed547e869ac185fda2e37b3a', "Pixel variance hash does not match")

class TestPixelCompleteStats(unittest.TestCase):
    def test_complete_pixel_stats(self):
        output = processing.run("scipy_filters:pixel_all", {'INPUT':testfile,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'e4977a976019b90d1f26f71467945b4e4cdbe2e65036919303ffa33f', "Complete pixel stats hash does not match")

        ds = gdal.Open(output['OUTPUT'])

        bandcount = ds.RasterCount
        self.assertEqual(bandcount, 5, "Band count does not match")

        descriptions = ['Min', 'Max', 'Mean', 'Median', 'Std']

        for band in range(1,6):
            description = ds.GetRasterBand(band).GetDescription()
            self.assertEqual(description, descriptions[band-1], "Band description does not match")



if __name__ == '__main__':
    unittest.main()           