"""Convolution algorithms test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'mail@riannek.de'
__date__ = '2023-05-05'
__copyright__ = 'Copyright 2023, Florian Neukirchen'



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

class TestConvolutionFilters(unittest.TestCase):

    def test_convolution(self):
        output = processing.run("scipy_filters:convolve", {'INPUT':testfile,'DIMENSION':0,'KERNEL':'[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]','NORMALIZATION':0,'ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), 'ae68abe4fe692fbf2f4bac69e76dce59cfd10a32186f02b5e327200f', "Convolution hash does not match")

    def test_correlate(self):
        output = processing.run("scipy_filters:correlate", {'INPUT':testfile,'DIMENSION':0,'KERNEL':'[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]','NORMALIZATION':0,'ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), 'ae68abe4fe692fbf2f4bac69e76dce59cfd10a32186f02b5e327200f', "Correlate hash does not match")

    def test_convolvefft(self):
        output = processing.run("scipy_filters:fft_convolve", {'INPUT':testfile,'KERNEL':'[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]','NORMALIZATION':0,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '5574bd202e0d859150b78e20ead6d893deb39edf69c5905b22fe3c12', "ConvolveFFT hash does not match")

    def test_correlatefft(self):
        output = processing.run("scipy_filters:fft_correlate", {'INPUT':testfile,'KERNEL':'[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]','NORMALIZATION':0,'BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '5574bd202e0d859150b78e20ead6d893deb39edf69c5905b22fe3c12', "CorrelateFFT hash does not match")

    def test_convolution_3D(self):
        output = processing.run("scipy_filters:convolve", {'INPUT':testfile,'DIMENSION':1,'KERNEL':'[[[0.0, 1.0, 0.0],\n[1.0, 1.0, 1.0],\n[0.0, 1.0, 0.0]],\n[[1.0, 1.0, 1.0],\n[1.0, 1.0, 1.0],\n[1.0, 1.0, 1.0]],\n[[0.0, 1.0, 0.0],\n[1.0, 1.0, 1.0],\n[0.0, 1.0, 0.0]]]','NORMALIZATION':0,'ORIGIN':'0, 0, 0','BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '6bed2d27fa14d4263f69f834656e7787ba9dc6034206f44c852a1241', "3D Convolution hash does not match")

    def test_convolve_cross_shifted_origin(self):
        output = processing.run("scipy_filters:convolve", {'INPUT':testfile,'DIMENSION':0,'KERNEL':'[[0.0, 1.0, 0.0],\n[1.0, 1.0, 1.0],\n[0.0, 1.0, 0.0]]','NORMALIZATION':0,'ORIGIN':'-1, 1','BANDSTATS':True,'DTYPE':6,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0})
        self.assertEqual(rasterhash(output['OUTPUT']), '5ac60dc5a402c916105cfa410ebf873e1e0c1619f0c9cf226f0bd39b', "Shifted origin hash does not match")


if __name__ == '__main__':
    unittest.main()    