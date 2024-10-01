"""PCA algorithms test.

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

class TestPCA(unittest.TestCase):

    def test_pca_alg(self):
        # input
        rlayer = QgsRasterLayer(testfile, "landsat lowres")

        self.assertTrue(rlayer.isValid())

        output = processing.run("scipy_filters:pca", {'INPUT':rlayer ,'STANDARDSCALER':False,'NCOMPONENTS':0,'PERCENTVARIANCE':0,'BANDSTATS':True,'DTYPE':0,'PLOT':'TEMPORARY_OUTPUT','OUTPUT':'TEMPORARY_OUTPUT'})

        self.assertEqual(rasterhash(output['OUTPUT']), '0824a9ad47383157220dab7b5229d56ec2601ad78b74f02a0df767aa', "PCA hash does not match")

        bandmean = np.array([10734.228, 12619.677, 14582.811, 15160.854, 15226.158]).astype(np.float32)
        npt.assert_array_equal(output['band mean'].astype(np.float32), bandmean, "Band mean does not match")

        singuarvalues = np.array([689999.7 , 230689.  ,  70001.92,  39620.43,  17569.02]).astype(np.float32)
        npt.assert_array_equal(output['singular values'].astype(np.float32), singuarvalues, "Singular values does not match")

        varianceexplained = np.array([38256292.0, 4276208.5, 393754.03125, 126137.28125, 24802.767578125]).astype(np.float32)
        npt.assert_array_equal(output['variance explained'].astype(np.float32), varianceexplained, "Variance explained does not match")

        eigenvectors = np.array([[0.3541675806045532, 0.49545255303382874, 0.6546452641487122, -0.32868078351020813, 0.30413928627967834], [0.4028194546699524, 0.3980104923248291, 0.030837714672088623, 0.4688003361225128, -0.67719966173172], [0.45966294407844543, 0.1553959995508194, -0.45246773958206177, 0.4084472060203552, 0.6269018650054932], [0.5003699064254761, -0.059508271515369415, -0.46246832609176636, -0.6902268528938293, -0.236217200756073], [0.5006410479545593, -0.7539399266242981, 0.38972383737564087, 0.17015543580055237, -0.00977662205696106]]).astype(np.float32)   
        npt.assert_array_almost_equal(output['eigenvectors'].astype(np.float32), eigenvectors, decimal=5, err_msg="Eigenvectors does not match")

        loadings = np.array([[2190.585693359375, 1024.546142578125, 410.78875732421875, -116.733642578125, 47.89857864379883], [2491.505859375, 823.0457153320312, 19.350610733032227, 166.49822998046875, -106.6514663696289], [2843.092041015625, 321.34332275390625, -283.9226989746094, 145.06333923339844, 98.73011016845703], [3094.87158203125, -123.05712127685547, -290.19805908203125, -245.13966369628906, -37.201595306396484], [3096.548583984375, -1559.072021484375, 244.551025390625, 60.43208312988281, -1.5397099256515503]])
        npt.assert_array_almost_equal(output['loadings'].astype(np.float32), loadings, decimal=5, err_msg="Loadings does not match")



    def test_pca_nodata(self):
        rlayer = QgsRasterLayer(testfile, "landsat lowres")

        orig_mask = processing.run("scipy_filters:no_data_mask", {'INPUT':rlayer,'SEPARATE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
        pca_out = processing.run("scipy_filters:pca", {'INPUT':rlayer,'STANDARDSCALER':False,'NCOMPONENTS':0,'PERCENTVARIANCE':0,'BANDSTATS':True,'DTYPE':0,'PLOT':'TEMPORARY_OUTPUT','OUTPUT':'TEMPORARY_OUTPUT'})
        pca_mask = processing.run("scipy_filters:no_data_mask", {'INPUT':rlayer,'SEPARATE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(orig_mask['OUTPUT']), rasterhash(pca_mask['OUTPUT']), "No data mask does not match")

        to_output = processing.run("scipy_filters:transform_to_PC", {'INPUT':testfile,'EIGENVECTORS':str(pca_out['eigenvectors'].tolist()),'BANDMEAN':'','BANDSTD':'','DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','PARAMETERLAYER':None,'NCOMPONENTS':0,'FALSEMEAN':False})
        to_mask = processing.run("scipy_filters:no_data_mask", {'INPUT':to_output['OUTPUT'],'SEPARATE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
        self.assertEqual(rasterhash(orig_mask['OUTPUT']), rasterhash(to_mask['OUTPUT']), "No data mask of Transform To PCA does not match")


    def test_pca_roundtrip_filled_nodata(self):
        rlayer = QgsRasterLayer(testfile, "landsat lowres")

        filled = processing.run("scipy_filters:fill_no_data", {'INPUT':testfile,'MODE':0,'VALUE':0,'OUTPUT':'TEMPORARY_OUTPUT'})

        pca_out = processing.run("scipy_filters:pca", {'INPUT':filled['OUTPUT'],'STANDARDSCALER':False,'NCOMPONENTS':0,'PERCENTVARIANCE':0,'BANDSTATS':True,'DTYPE':0,'PLOT':'TEMPORARY_OUTPUT','OUTPUT':'TEMPORARY_OUTPUT'})
        from_output = processing.run("scipy_filters:transform_from_PC", {'INPUT':pca_out['OUTPUT'],'EIGENVECTORS': str(pca_out['eigenvectors'].tolist()),'BANDMEAN': str(pca_out['band mean'].tolist()),'BANDSTD':'','DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT'})
        to_output = processing.run("scipy_filters:transform_to_PC", {'INPUT':filled['OUTPUT'],'EIGENVECTORS':str(pca_out['eigenvectors'].tolist()),'BANDMEAN':'','BANDSTD':'','DTYPE':0,'OUTPUT':'TEMPORARY_OUTPUT','PARAMETERLAYER':None,'NCOMPONENTS':0,'FALSEMEAN':False})

        ds = gdal.Open(pca_out['OUTPUT'])
        data_pca = ds.ReadAsArray().astype(np.float32)

        ds = gdal.Open(from_output['OUTPUT'])
        data_from_pca = ds.ReadAsArray().astype(np.float32)

        ds = gdal.Open(to_output['OUTPUT'])
        data_to_pca = ds.ReadAsArray().astype(np.float32)

        ds = gdal.Open(testfile)
        data_orig = ds.ReadAsArray().astype(np.float32)


        npt.assert_array_almost_equal(data_from_pca, data_orig, decimal=2, err_msg="Transform from PCA does not match original data")
        npt.assert_array_almost_equal(data_pca, data_to_pca, decimal=2, err_msg="Transform to PCA does not match PCA")

        

if __name__ == '__main__':
    unittest.main()           



