# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-03-03
        copyright            : (C) 2024 by Florian Neukirchen
        email                : mail@riannek.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Florian Neukirchen'
__date__ = '2024-03-03'
__copyright__ = '(C) 2024 by Florian Neukirchen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from osgeo import gdal
from scipy import linalg
import numpy as np
import json
import enum
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterString,
                       QgsProcessingLayerPostProcessorInterface,
                       QgsProcessingParameterBoolean,
                       QgsProcessingException,
                        )

from .scipy_algorithm_baseclasses import groups


class SciPyPCAAlgorithm(QgsProcessingAlgorithm):
    """
    Calculate PCA (using scipy.svd)
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    NCOMPONENTS = 'NCOMPONENTS'
    PERCENTVARIANCE = 'PERCENTVARIANCE'

    
    _name = 'pca'
    _displayname = 'Principal Component Analysis (PCA)'
    # Output layer name: If set to None, the displayname is used 
    # Can be changed while getting the parameters.
    _outputname = 'PCA'
    _groupid = "pca" 
    _help = """
            Help
            """
    
    # Init Algorithm
    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Add parameters
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Input layer'),
            )
        )

        self.addParameter(QgsProcessingParameterNumber(
            self.NCOMPONENTS,
            self.tr('Number of components to keep. Set to 0 for all components.'),
            QgsProcessingParameterNumber.Type.Integer,
            defaultValue=0, 
            optional=True, 
            minValue=0, 
            # maxValue=100
            ))      
    

        self.addParameter(QgsProcessingParameterNumber(
            self.PERCENTVARIANCE,
            self.tr('Percentage of Variance (if set and > 0: overwrites number of components)'),
            QgsProcessingParameterNumber.Type.Double,
            defaultValue=0, 
            optional=True, 
            minValue=0, 
            maxValue=100
            ))      
    

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
            self.tr(self._outputname)))
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Get Parameters
        self.inputlayer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        self.output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT,context)

        self.ncomponents = self.parameterAsInt(parameters, self.NCOMPONENTS,context)
        self.percentvariance = self.parameterAsDouble(parameters, self.PERCENTVARIANCE,context)
        # Open Raster with GDAL
        self.ds = gdal.Open(self.inputlayer.source())

        if not self.ds:
            raise Exception("Failed to open Raster Layer")
        
        self.bandcount = self.ds.RasterCount
        self.indatatype = self.ds.GetRasterBand(1).DataType


        if feedback.isCanceled():
            return {}
        
        feedback.setProgress(0)

        # Start the actual work
        a = self.ds.ReadAsArray().astype(np.float32)

        # shape is bands, RasterYSize, RasterXSize
        orig_shape = a.shape
        flattened = a.reshape(orig_shape[0], -1)

        flattened = flattened.T
        # Now shape is number of pixels, bands

        # substract mean

        col_mean = flattened.mean(axis=0)

        centered = flattened - col_mean[np.newaxis, :]

        n_pixels = flattened.shape[0]

        # Get loadings with SVD

        # For info on relation of SVD and PCA see:
        # https://stats.stackexchange.com/a/134283
        # https://scentellegher.github.io/machine-learning/2020/01/27/pca-loadings-sklearn.html

        U, S, VT = linalg.svd(centered,full_matrices=False)

        loadings = VT.T @ np.diag(S) / np.sqrt(n_pixels - 1)

        # variance_explained = eigenvalues
        # and they can be calculated from the singular values (S)
        # See point 3 in https://stats.stackexchange.com/a/134283

        variance_explained = S * S / (n_pixels - 1)
        variance_explained_cumsum = variance_explained.cumsum()


        if feedback.isCanceled():
            return {}

        # Rotate component vectors by 180° if sum of loadings is < 0
        # Otherwise dark will be bright, and vica versa

        for i in range(loadings.shape[1]):
            if loadings[:,i].sum() < 0:
                loadings[:,i] = loadings[:,i] * -1

        # Give feedback
        
        feedback.pushInfo("Singular values (of SVD):")
        feedback.pushInfo(str(S))
        feedback.pushInfo("Variance explained (Eigenvalues):")
        feedback.pushInfo(str(variance_explained))
        feedback.pushInfo("Cumulated sum of variance explained:")
        feedback.pushInfo(str(variance_explained_cumsum))
        feedback.pushInfo("Loadings:")
        feedback.pushInfo(str(loadings))

        if feedback.isCanceled():
            return {}

        # Transform the data using the loadings
        # (before rotating the loadings, this would have been
        # the same as: centered @ VT.T)
                
        new_array = centered @ loadings

        # Reshape to original shape
        new_array = new_array.T.reshape(orig_shape)

        # How many bands to keep?
        bands = self.bandcount

        if 0 < self.percentvariance <= 100:
            fraction = self.percentvariance / 100
            print(fraction)
            # get index with at least fraction
            bands = np.argmax(variance_explained_cumsum >= fraction) 
            bands = int(bands)
        elif 0 < self.ncomponents < self.bandcount:
            bands = self.ncomponents 

        # Prepare output and write file
        etype = gdal.GDT_Float32

        driver = gdal.GetDriverByName('GTiff')
        self.out_ds = driver.Create(self.output_raster,
                                    xsize=self.ds.RasterXSize,
                                    ysize=self.ds.RasterYSize,
                                    bands=bands,
                                    eType=etype)

        self.out_ds.SetGeoTransform(self.ds.GetGeoTransform())
        self.out_ds.SetProjection(self.ds.GetProjection())

        self.out_ds.WriteArray(new_array[0:bands,:,:])    

        # Close the dataset to write file to disk
        self.out_ds = None 

        encoded = json.dumps({
                'singular values': S.tolist(),
                'loadings': loadings.tolist(),
                'variance explained': variance_explained.tolist(),
                'variance explained cumsum': variance_explained_cumsum.tolist(),
                'band mean': col_mean.tolist(),
                })

        # Save loadings etc as json in the metadata abstract of the layer
        global updatemetadata
        updatemetadata = self.UpdateMetadata(encoded)
        context.layerToLoadOnCompletionDetails(self.output_raster).setPostProcessor(updatemetadata)

        return {self.OUTPUT: self.output_raster,
                'singular values': S,
                'loadings': loadings,
                'variance explained': variance_explained,
                'variance explained cumsum': variance_explained_cumsum,
                'band mean': col_mean,
                'json': encoded}


    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        # PCA only possible with more than 1 bands
        if layer.bandCount() == 1:
            return (False, self.tr("PCA only possible if input layer has more than 1 bands"))
            
        return super().checkParameterValues(parameters, context)
    
    class UpdateMetadata(QgsProcessingLayerPostProcessorInterface):
        """
        To rename output layer name in the postprocessing step.
        """
        def __init__(self, abstract):
            self.abstract = abstract
            super().__init__()
            
        def postProcessLayer(self, layer, context, feedback):
            meta = layer.metadata()
            meta.setAbstract(self.abstract)
            print(self.abstract)
            layer.setMetadata(meta)
    

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self._name

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self._displayname)

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        if self._groupid == "":
            return ""
        s = groups.get(self._groupid)
        if not s:
            # If group ID is not in dictionary group, return error message for debugging
            return "Displayname of group must be set in groups dictionary"
        return self.tr(s)

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self._groupid
    
    def shortHelpString(self):
        """
        Returns the help string that is shown on the right side of the 
        user interface.
        """
        return self.tr(self._help)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SciPyPCAAlgorithm()  
    