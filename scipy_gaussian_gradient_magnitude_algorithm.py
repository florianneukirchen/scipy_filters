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
from scipy import ndimage
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBand,
                        )


class SciPyGaussianGradientMagnitudeAlgorithm(QgsProcessingAlgorithm):
    """
    Gradient magnitude using Gaussian derivatives.


    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'

    SIGMA = 'SIGMA'
    MODE = 'MODE'
    CVAL = 'CVAL'




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
            self.SIGMA,
            self.tr('Sigma'),
            QgsProcessingParameterNumber.Type.Double,
            defaultValue=5, 
            optional=False, 
            minValue=0, 
            maxValue=100
            ))


        self.modes = ['reflect', 'constant', 'nearest', 'mirror', 'wrap']

        self.addParameter(QgsProcessingParameterEnum(
            self.MODE,
            self.tr('Border Mode'),
            self.modes,
            defaultValue=0)) 
        
        self.addParameter(QgsProcessingParameterNumber(
            self.CVAL,
            self.tr('Constant value past edges for border mode "constant"'),
            QgsProcessingParameterNumber.Type.Double,
            defaultValue=0, 
            optional=True, 
            minValue=0, 
            # maxValue=100
            ))        



        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
            self.tr("Gaussian Gradient Magnitude")))
        



    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Get Parameters
        kargs = {}
        inputlayer = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        self.output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT,context)
        kargs['sigma'] = self.parameterAsDouble(parameters, self.SIGMA, context)
        mode = self.parameterAsInt(parameters, self.MODE, context) 
        kargs['mode'] = self.modes[mode]

        cval = self.parameterAsDouble(parameters, self.CVAL, context)
        if cval:
            kargs['cval'] = cval


        # Open Raster with GDAL
        self.ds = gdal.Open(inputlayer.source())

        if not self.ds:
            raise Exception("Failed to open Raster Layer")
        

        self.bandcount = self.ds.RasterCount
        

        # Prepare output
        driver = gdal.GetDriverByName('GTiff')
        self.out_ds = driver.CreateCopy(self.output_raster, self.ds, strict=0)

        # Iterate over bands and calculate gaussian

        for i in range(1, self.bandcount + 1):
            a = self.ds.GetRasterBand(i).ReadAsArray()
            filtered = ndimage.gaussian_filter(a, **kargs)
            self.out_ds.GetRasterBand(i).WriteArray(filtered)

            feedback.setProgress(i * 100 / self.bandcount)
            if feedback.isCanceled():
                return {}

        # Close the dataset to write file to disk
        self.out_ds = None 

        return {self.OUTPUT: self.output_raster}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'gaussian_gradient_magnitude'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Gaussian gradient magnitude')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Edges'
    
    def shortHelpString(self):
      
        h =  """
             Gradient magnitude using Gaussian derivatives
             Border mode: Determine how input is extended around the edges. 
             """
		
        return self.tr(h)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SciPyGaussianGradientMagnitudeAlgorithm()