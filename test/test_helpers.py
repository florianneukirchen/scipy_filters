"""Helpers test.

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
from scipy_filters.helpers import *
from scipy_filters.scipy_filters_provider import SciPyFiltersProvider
import processing
from processing.core.Processing import Processing

app = QgsApplication([], True)
app.setPrefixPath("/usr", True)
app.initQgis()

 
Processing.initialize()
provider = SciPyFiltersProvider()
QgsApplication.processingRegistry().addProvider(provider)


class TestNoDataHelpers(unittest.TestCase):
    def test_minimumvalue(self):
        self.assertEqual(minimumvalue(np.int16), -32768, "Minimum value for int16 does not match")
        self.assertEqual(minimumvalue(np.uint16), 0, "Minimum value for uint16 does not match")
        self.assertEqual(minimumvalue(np.float32), -np.inf, "Minimum value for float32 does not match")

    def test_maximumvalue(self):
        self.assertEqual(maximumvalue(np.int16), 32767, "Maximum value for int16 does not match")
        self.assertEqual(maximumvalue(np.uint16), 65535, "Maximum value for uint16 does not match")
        self.assertEqual(maximumvalue(np.float32), np.inf, "Maximum value for float32 does not match")

    def test_centralvalue(self):
        self.assertEqual(centralvalue(np.int16), 0, "Central value for int16 does not match")
        self.assertEqual(centralvalue(np.uint16), 32767, "Central value for uint16 does not match")
        self.assertEqual(centralvalue(np.float32), 0, "Central value for float32 does not match")




if __name__ == '__main__':
    unittest.main()     