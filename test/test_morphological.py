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
testmask = os.path.join(dir_path, "testimage_mask.tif")


class TestMorphologicalBinary(unittest.TestCase):
    def test_binary_dilation(self):
        output = processing.run("scipy_filters:binary_morphology", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':0,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','ITERATIONS':1,'BORDERVALUE':0,'MASK':None})
        self.assertEqual(rasterhash(output['OUTPUT']), '45360b6647610d8f7dadf694dfdb4f5dcb8f035627756f89a4803dc9', "Binary Dilation hash does not match")

    def test_binary_erosion(self):
        output = processing.run("scipy_filters:binary_morphology", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':1,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','ITERATIONS':1,'BORDERVALUE':0,'MASK':None})
        self.assertEqual(rasterhash(output['OUTPUT']), '617651d936805b5de1a296bc53f91e75f602227c01a0d0d3efd62408', "Binary Erosion hash does not match")

    def test_binary_closing(self):
        output = processing.run("scipy_filters:binary_morphology", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':2,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','ITERATIONS':1,'BORDERVALUE':0,'MASK':None})
        self.assertEqual(rasterhash(output['OUTPUT']), 'b9972490e0d53475a11aa28dad671da904b15ff1f9ed775481b988b0', "Binary Closing hash does not match")

    def test_binary_opening(self):
        output = processing.run("scipy_filters:binary_morphology", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':2,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','ITERATIONS':1,'BORDERVALUE':0,'MASK':None})
        self.assertEqual(rasterhash(output['OUTPUT']), 'b9972490e0d53475a11aa28dad671da904b15ff1f9ed775481b988b0', "Binary Opening hash does not match")


class TestMorphologicalGrey(unittest.TestCase):
    def test_grey_dilation(self):
        output = processing.run("scipy_filters:grey_morphology", {'INPUT':testfile,'DIMENSION':0,'ALGORITHM':0,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '8f55542f57328ecb18231496bfa4f0ad195653dd45423e3560e85e49', "Grey Dilation hash does not match")

    def test_grey_erosion(self):
        output = processing.run("scipy_filters:grey_morphology", {'INPUT':testfile,'DIMENSION':0,'ALGORITHM':1,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '560fc2763883a2503d8ad92d865eae18eb8e012b388b6ae81e0a4600', "Grey Erosion hash does not match")

    def test_grey_closing(self):
        output = processing.run("scipy_filters:grey_morphology", {'INPUT':testfile,'DIMENSION':0,'ALGORITHM':2,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '0273d6d87db25ec7f9d9a504ab2db595bdf2e7b6dcc409ff1deb4f6c', "Grey Closing hash does not match")

    def test_grey_opening(self):
        output = processing.run("scipy_filters:grey_morphology", {'INPUT':testfile,'DIMENSION':0,'ALGORITHM':3,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '398a0a40510f7b1b6a290275f91f017815a8b52a33be940d04ead408', "Grey Opening hash does not match")



class TestTophat(unittest.TestCase):
    def test_white_tophat(self):
        output = processing.run("scipy_filters:tophat", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':0,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '94bee87002678a06615290d4d22609ea33a02f520a662d0889f93a94', "White Tophat hash does not match")

    def test_black_tophat(self):
        output = processing.run("scipy_filters:tophat", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':1,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '7ea2aef80df3a81e2246341a6ddf8a5f94b3fe6ffc899d7c331fc818', "Black Tophat hash does not match")

    def test_morph_gradient(self):
        output = processing.run("scipy_filters:tophat", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':2,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), '1b4db52a32e8544311ebbd4f2028fc5bee29c5608b75144e61ee571d', "Morphol Gradient hash does not match")

    def test_morph_laplace(self):
        output = processing.run("scipy_filters:tophat", {'INPUT':testmask,'DIMENSION':0,'ALGORITHM':3,'STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0','BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','SIZES':'3, 3','MODE':0,'CVAL':0,'FOOTPRINT':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'cd28744da21baf362d516fa378dac21b938e7e5a810359bbf66c20bc', "Morphol Laplace hash does not match")


class TestFillHoles(unittest.TestCase):
    def test_fill_holes(self):
        output = processing.run("scipy_filters:fill_holes", {'INPUT':testmask,'DIMENSION':0,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','STRUCTURE':'[[0, 1, 0],\n[1, 1, 1],\n[0, 1, 0]]','ORIGIN':'0, 0'})
        self.assertEqual(rasterhash(output['OUTPUT']), 'd054fffd6b2276306c25978c87236e9d3587093efbae1aa2b4c86f9d', "Fill Holes hash does not match")

class TestHitMiss(unittest.TestCase):
    def test_hitmiss(self):
        output = processing.run("scipy_filters:hit_or_miss", {'INPUT':testmask,'DIMENSION':0,'BANDSTATS':True,'DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','STRUCTURE1':'[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]','STRUCTURE2':'','ORIGIN1':'0, 0','ORIGIN2':'0, 0'})
        self.assertEqual(rasterhash(output['OUTPUT']), '246f0f3a04d47483af4f310dd11d69b049231d5b59c4cca8b2dbb00a', "Hit Miss hash does not match")


if __name__ == '__main__':
    unittest.main()     