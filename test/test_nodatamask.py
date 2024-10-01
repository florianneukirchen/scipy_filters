"""No Data Mask algorithms test.

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


class TestNoDataMask(unittest.TestCase):

    def test_nodatamask(self):
        mask = processing.run("scipy_filters:no_data_mask", {'INPUT':testfile,'SEPARATE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(mask['OUTPUT']), '7c57dbce4a606e071180e21ad26abd14fcb7e7c33ef8b55e977f690f', "No Data mask hash does not match")

        # Fill with exact band mean
        filled = processing.run("scipy_filters:fill_no_data", {'INPUT':testfile,'MODE':3,'VALUE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(filled['OUTPUT']), 'e91eb65245d553af8cab0587960b8803fbd006b5a33e51b8de776c50', "Filled no data hash does not match")

        applied = processing.run("scipy_filters:apply_no_data_mask", {'INPUT':filled['OUTPUT'],'MASK':mask['OUTPUT'],'NODATA':0,'CHANGE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(applied['OUTPUT']), 'ee2b119caa35d8b1bea8908346ddb20d05c2e85cd4dcb0876be2dcb9', "Applied no data mask hash does not match")

        ds_applied = gdal.Open(applied['OUTPUT'])
        self.assertEqual(ds_applied.GetRasterBand(1).GetNoDataValue(), 0, "No data value not set correctly")

    def test_fillnodata(self):
        # Fill with 0
        filled = processing.run("scipy_filters:fill_no_data", {'INPUT':testfile,'MODE':0,'VALUE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(filled['OUTPUT']), 'b9b57188d2c9b3fc8c0229e06985644eddbf9b20f35374fdad3251fd', "Fill No Data with 0, hash does not match")


        # Value 9999
        filled = processing.run("scipy_filters:fill_no_data", {'INPUT':testfile,'MODE':1,'VALUE':9999,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(filled['OUTPUT']), '2d41ceccb0e607f91178fe80c0c9470df844bceddfa617489cb0deff', "Fill No Data with 9999, hash does not match")

        # Central value
        filled = processing.run("scipy_filters:fill_no_data", {'INPUT':testfile,'MODE':6,'VALUE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(filled['OUTPUT']), '781fd404477f8fcd2087af32f3f0d6f3393185b63a84240853148e2e', "Fill No Data with central value, hash does not match")

if __name__ == '__main__':
    unittest.main()           