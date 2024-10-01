"""Blur algorithms test.

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

class TestGaussian(unittest.TestCase):
    def test_gaussian(self):
        output = processing.run("scipy_filters:gaussian", {'INPUT':testfile,'DIMENSION':0,'SIGMA':5,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0,'ORDER':0,'TRUNCATE':4})
        self.assertEqual(rasterhash(output['OUTPUT']), '39c89579e688caea39ab5b8bc46be57576889c8577e48938df696956', "Gaussian hash does not match")

    def test_gaussian_3D(self):
        output = processing.run("scipy_filters:gaussian", {'INPUT':testfile,'DIMENSION':1,'SIGMA':3,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0,'ORDER':0,'TRUNCATE':4})
        self.assertEqual(rasterhash(output['OUTPUT']), '4a62a4395180cdfed6f5b1ee49956074a1a05b136a391ee97a3151a0', "3D Gaussian hash does not match")

    def test_gaussian_firstorder(self):
        output = processing.run("scipy_filters:gaussian", {'INPUT':testfile,'DIMENSION':0,'SIGMA':5,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0,'ORDER':1,'TRUNCATE':4})
        self.assertEqual(rasterhash(output['OUTPUT']), '3c5a932f2947e1612fb43cf561d89b4b8b6e7988d8c778cdaa957f19', "First Order Gaussian hash does not match")

class TestUniform(unittest.TestCase):
    def test_uniform(self):
        output = processing.run("scipy_filters:uniform", {'INPUT':testfile,'DIMENSION':0,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','MODE':0,'CVAL':0,'SIZES':'3, 3'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'c0bb557f8bbe1d0c56758a5ad48b69a3b09b910944e1e5ccb91271cd', "Uniform hash does not match")

class TestFourierEllipsoid(unittest.TestCase):
    def test_fourier_ellipsoid(self):
        output = processing.run("scipy_filters:fourier_ellipsoid", {'INPUT':testfile,'DIMENSION':0,'SIZES':'2, 4','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), '2e1d61edc392619dc73bae7e5b002bd20591607b8d01887ee3c22b58', "Fourier Ellipsoid hash does not match")

class TestFourierGaussian(unittest.TestCase):
    def test_fourier_ellipsoid(self):
        output = processing.run("scipy_filters:fourier_gaussian", {'INPUT':testfile,'DIMENSION':0,'SIGMA':5,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'c965c6e83a80becf727493a73ee6ed91d7f8688e90fd0fda5e1512fc', "Fourier Gaussian hash does not match")

class TestFourierUniform(unittest.TestCase):
    def test_fourier_ellipsoid(self):
        output = processing.run("scipy_filters:fourier_uniform", {'INPUT':testfile,'DIMENSION':0,'SIZES':'3, 3','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'c03814e6f6b9db195e723f1526e22a8b096683a0dd8769497ce3b73a', "Fourier Gaussian hash does not match")



if __name__ == '__main__':
    unittest.main()    