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


class TestEdgeFilters(unittest.TestCase):

    def test_sobel(self):
        output = processing.run("scipy_filters:sobel", {'INPUT':testfile,'DIMENSION':0,'AXIS':0,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '20edee14dc80d4ee04aa5ea455962f99488c017cc1701fb07e5a95e6', "Sobel hash does not match")

        # Data Type
        ds = gdal.Open(output['OUTPUT'])
        dtype = ds.GetRasterBand(1).DataType
        self.assertEqual(dtype, 6, "Data type does not match")

        # 3D
        output = processing.run("scipy_filters:sobel", {'INPUT':testfile,'DIMENSION':1,'AXIS':0,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '0831d97bb2196cffa1d82044b87c72171a2c99baf925c70100dc13d2', "Sobel hash in 3D does not match")

    def test_laplace(self):
        output = processing.run("scipy_filters:laplace", {'INPUT':testfile,'DIMENSION':0,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '9f10f9289598e2e37df3ac6dd4c05e120a8401ca50669bb0698624e5', "Laplace hash does not match")

    def test_prewitt(self):
        output = processing.run("scipy_filters:prewitt", {'INPUT':testfile,'DIMENSION':0,'AXIS':0,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), 'cce172e248f95e8e7087eb9615b06659dda9f69058b27d15fa4f3979', "Prewitt hash does not match")

    def test_gradient(self):
        # Default, Axis Both
        output = processing.run("scipy_filters:gradient", {'INPUT':testfile,'AXIS':2,'MAPUNITS':True,'ABSOLUTE':False,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '0159a98a51445a97991949fb6656b00dd513d25908d756d194f914f5', "Gradient hash (axis both) does not match")

        # x axis
        output = processing.run("scipy_filters:gradient", {'INPUT':testfile,'AXIS':0,'MAPUNITS':True,'ABSOLUTE':False,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'c03cf5dcc7fd6ef1ab8467f1edad40b009684c2b68530504bb19d187', "Gradient hash (x axis) does not match")

        # y axis
        output = processing.run("scipy_filters:gradient", {'INPUT':testfile,'AXIS':1,'MAPUNITS':True,'ABSOLUTE':False,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'aa2dd64648498c09c32551ef1347db9f6564e18c552516360c64002c', "Gradient hash (y axis) does not match")

        # axis both, not in map units
        output = processing.run("scipy_filters:gradient", {'INPUT':testfile,'AXIS':2,'MAPUNITS':False,'ABSOLUTE':False,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'e0928c1d2fa2f483a01669a99d3ae1768f6c46655bab3aae3555128d', "Gradient hash (not in map units) does not match")

        # Absolute value
        output = processing.run("scipy_filters:gradient", {'INPUT':testfile,'AXIS':2,'MAPUNITS':True,'ABSOLUTE':False,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '0159a98a51445a97991949fb6656b00dd513d25908d756d194f914f5', "Gradient hash (absolute value) does not match")

    def test_gaussian_laplace(self):
        output = processing.run("scipy_filters:gaussian_laplace", {'INPUT':testfile,'DIMENSION':0,'SIGMA':5,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '0bdd74299a761eaa741817155cf3dce358ef4e5da4885ac6c0e859af', "Gaussian Laplace hash does not match")

    def test_gaussian_gradient_magnitude(self):
        output = processing.run("scipy_filters:gaussian_gradient_magnitude", {'INPUT': testfile,'DIMENSION':0,'SIGMA':5,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), 'f3e4867d69f6f1d083578656663f147b3feec118b9fb3f45e848acbc', "Gaussian gradient magnitude hash does not match")
