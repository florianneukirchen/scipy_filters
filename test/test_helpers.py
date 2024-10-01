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

    def test_is_in_dtype_range(self):
        self.assertTrue(is_in_dtype_range(0, np.int16), "0 is not in int16 range")
        self.assertTrue(is_in_dtype_range(-32768, np.int16), "-32768 is not in int16 range")
        self.assertTrue(is_in_dtype_range(32767, np.int16), "32767 is not in int16 range")
        self.assertFalse(is_in_dtype_range(-32769, np.int16), "-32769 is in int16 range")
        self.assertFalse(is_in_dtype_range(32768, np.int16), "32768 is in int16 range")

        self.assertTrue(is_in_dtype_range(0, np.uint16), "0 is not in uint16 range")
        self.assertTrue(is_in_dtype_range(65535, np.uint16), "65535 is not in uint16 range")
        self.assertFalse(is_in_dtype_range(-1, np.uint16), "-1 is in uint16 range")
        self.assertFalse(is_in_dtype_range(65536, np.uint16), "65536 is in uint16 range")

        self.assertTrue(is_in_dtype_range(0, np.float32), "0 is not in float32 range")
        self.assertTrue(is_in_dtype_range(-np.inf, np.float32), "-np.inf is not in float32 range")
        self.assertTrue(is_in_dtype_range(np.inf, np.float32), "np.inf is not in float32 range")

class TestStructures(unittest.TestCase):
    def test_checkstructure_codes(self):
        ok, s, shape = check_structure("square", 2)
        self.assertTrue(ok)
        self.assertEqual(shape, (3, 3))

        ok, s, shape = check_structure("square", 3)
        self.assertTrue(ok)

        ok, s, shape = check_structure("sfsdf", 2)
        self.assertFalse(ok)
        self.assertIsNot(s, "")

        ok, s, shape = check_structure("cube", 3)
        self.assertTrue(ok)
        self.assertEqual(shape, (3, 3, 3))

        ok, s, shape = check_structure("cube", 2)
        self.assertFalse(ok)
        self.assertIsNot(s, "")

    def test_structure(self):
        kernel = "[[1, 2, 1],[2, 4, 2],[1, 2, 1]]"

        ok, s, shape = check_structure(kernel, 2)
        self.assertTrue(ok)
        self.assertEqual(shape, (3, 3))

        ok, s, shape = check_structure(kernel, 3)
        self.assertTrue(ok)
        self.assertEqual(shape, (1, 3, 3))

        kernel = "[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]"
        ok, s, shape = check_structure(kernel, 2)
        self.assertTrue(ok)
        self.assertEqual(shape, (3, 3))

        kernel = "[[1, 2, 1],[2, 4, 2],[1, 2, 1]"
        ok, s, shape = check_structure(kernel, 2)
        self.assertFalse(ok)
        self.assertIsNot(s, "")

        kernel = "[[1, 2, 1],[2, 4, 2],[1,  1]]"
        self.assertFalse(ok)

        kernel = '[[[1.0, 1.0, 1.0],[1.0, 1.0, 1.0],[1.0, 1.0, 1.0]],[[1.0, 1.0, 1.0],[1.0, 1.0, 1.0],[1.0, 1.0, 1.0]],[[1.0, 1.0, 1.0],[1.0, 1.0, 1.0],[1.0, 1.0, 1.0]]]'
        ok, s, shape = check_structure(kernel, 3)
        self.assertTrue(ok)
        self.assertEqual(shape, (3, 3, 3))

        ok, s, shape = check_structure(kernel, 2)
        self.assertFalse(ok)

    def test_odd_structure(self):
        kernel = "[[1, 2, 1],[2, 4, 2],[1, 2, 1]]"
        ok, s, shape = check_structure(kernel, 2, odd=True)
        self.assertFalse(ok)

        kernel = "[[1, 3, 1],[3, 5, 3],[1, 3, 1]]"
        ok, s, shape = check_structure(kernel, 2, odd=True)
        self.assertTrue(ok)

    # TODO test for check origin

    def test_str_to_int_or_list(self):
        self.assertEqual(str_to_int_or_list("2"), 2)
        self.assertEqual(str_to_int_or_list("0"), 0)
        self.assertEqual(str_to_int_or_list("[1,2,1]"), [1, 2, 1])
        self.assertEqual(str_to_int_or_list("1,2,1"), [1, 2, 1])

        with self.assertRaises(ValueError):
            str_to_int_or_list("[[1,2,1],[2,4,2],[1,2,1]]")

        with self.assertRaises(ValueError):
            str_to_int_or_list("gssfsfsr")

if __name__ == '__main__':
    unittest.main()     

