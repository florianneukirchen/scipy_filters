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

from scipy_filters.helpers import RasterWizard, RasterWindow

import scipy.ndimage as ndimage

app = QgsApplication([], True)
app.setPrefixPath("/usr", True)
app.initQgis()

 
Processing.initialize()
provider = SciPyFiltersProvider()
QgsApplication.processingRegistry().addProvider(provider)

testfile = os.path.join(dir_path, "testimage_landsat.tif")

class TestWizard(unittest.TestCase):

    def test_wizard(self):
        rlayer = QgsRasterLayer(testfile, "landsat lowres")

        wizard = RasterWizard(rlayer)

        self.assertEqual(wizard[0,0][0], 8265)
        self.assertEqual(wizard.shape, (5, 103, 121))
        self.assertEqual(wizard.nodata, 0)
        self.assertEqual(wizard.crs_id, 'EPSG:32619')
        self.assertEqual(wizard.name, "landsat lowres")
        self.assertEqual(wizard.countbands, 5)
        self.assertEqual(wizard.ndim, 3)

        a = wizard.toarray()
        a = a / 2
        l = wizard.tolayer(a)
        self.assertEqual(rasterhash(l), '5899fdb7b1a964b84438284b0ad7b7c20621f9283754937e25918406')

        ds = gdal.Open(l.source())
        dtype = ds.GetRasterBand(1).DataType
        self.assertEqual(dtype, "Float64")



class TestWizard(unittest.TestCase):

    def test_wizard_window(self):
        rlayer = QgsRasterLayer(testfile, "landsat lowres")

        wizard = RasterWizard(rlayer)

        wizard.set_out_ds()

        for win in wizard.get_windows(windowsize=2048, margin=1):
            a = wizard.toarray(win=win)
            a = ndimage.maximum_filter(a, size=3)
            wizard.write_window(a, win)

        l = wizard.load_output()
        self.assertEqual(rasterhash(l), 'd535e2697ca22b2c7c26990ba36d8f0396ed12ead8ca0f650f798b8d')


if __name__ == '__main__':
    unittest.main()           
