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

from scipy import ndimage
from qgis.core import (QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,)

from ..scipy_algorithm_baseclasses import SciPyAlgorithmWithMode


class SciPyAlgorithmWithSigma(SciPyAlgorithmWithMode):
    """
    Base class with mode and sigma for any algorithm using gaussian.
    """

    SIGMA = 'SIGMA'

    def insert_parameters(self, config):

        self.addParameter(QgsProcessingParameterNumber(
            self.SIGMA,
            self.tr('Sigma'),
            QgsProcessingParameterNumber.Type.Double,
            defaultValue=5, 
            optional=False, 
            minValue=0, 
            maxValue=100
            ))
        
        super().insert_parameters(config)

    
    def get_parameters(self, parameters, context):
        kwargs = super().get_parameters(parameters, context)
        kwargs['sigma'] = self.parameterAsDouble(parameters, self.SIGMA, context)
        return kwargs


class SciPyGaussianLaplaceAlgorithm(SciPyAlgorithmWithSigma):
    """
    Gradient magnitude using Gaussian derivatives.


    """

    # Overwrite constants of base class
    _name = 'gaussian_laplace'
    _displayname = 'Gaussian Laplace'
    _outputname = None # If set to None, the displayname is used 
    _groupid = "edges" 

    _default_dtype = 6 # Optionally change default output dtype (value = idx of combobox)

    _help = """
            Laplace filter using Gaussian second derivatives. \
            Calculated with gaussian_laplace from \
            <a href="https://docs.scipy.org/doc/scipy/reference/ndimage.html">scipy.ndimage</a>.

            <b>Dimension</b> Calculate for each band separately (2D) \
            or use all bands as a 3D datacube and perform filter in 3D. \
            Note: bands will be the first axis of the datacube.

            <b>Sigma</b> Standard deviation of the gaussian filter.
            <b>Border mode</b> determines how input is extended around \
            the edges: <i>Reflect</i> (input is extended by reflecting at the edge), \
            <i>Constant</i> (fill around the edges with a <b>constant value</b>), \
            <i>Nearest</i> (extend by replicating the nearest pixel), \
            <i>Mirror</i> (extend by reflecting about the center of last pixel), \
            <i>Wrap</i> (extend by wrapping around to the opposite edge).

            <b>Dtype</b> Data type of output. Beware of clipping \
            and potential overflow errors if min/max of output does \
            not fit. Default is Float32.
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return ndimage.gaussian_laplace
    
    def checkAndComplain(self, feedback):
        if self._outdtype in (1,2,4):
            msg = self.tr(f"WARNING: Output contains negative values, but output data type is unsigned integer!")
            feedback.reportError(msg, fatalError = False)

    def createInstance(self):
        return SciPyGaussianLaplaceAlgorithm()


class SciPyGaussianAlgorithm(SciPyAlgorithmWithSigma):
    """
    Gaussian Filter (Blur) using scipy.ndimage.gaussian_filter


    """

    TRUNCATE = 'TRUNCATE'
    ORDER = 'ORDER'

    # Overwrite constants of base class
    _name = 'gaussian'
    _displayname = 'Gaussian filter (blur)'
    _outputname = 'Gaussian' 
    _groupid = "blur" 
    _help = """
            Gaussian filter (blur with a gaussian kernel). \
            Calculated with gaussian_filter from \
            <a href="https://docs.scipy.org/doc/scipy/reference/ndimage.html">scipy.ndimage</a>.
            <b>Dimension</b> Calculate for each band separately (2D) \
            or use all bands as a 3D datacube and perform filter in 3D. \
            Note: bands will be the first axis of the datacube.

            <b>Sigma</b> Standard deviation of a gaussian kernel.

            <b>Border mode</b> determines how input is extended around \
            the edges: <i>Reflect</i> (input is extended by reflecting at the edge), \
            <i>Constant</i> (fill around the edges with a <b>constant value</b>), \
            <i>Nearest</i> (extend by replicating the nearest pixel), \
            <i>Mirror</i> (extend by reflecting about the center of last pixel), \
            <i>Wrap</i> (extend by wrapping around to the opposite edge).

            <b>Order</b> Optionally use first, second or third derivative of gaussian.
            <b>Truncate</b> Radius of kernel in standard deviations.
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return ndimage.gaussian_filter
    
    def initAlgorithm(self, config):
        # Call the super function first
        # (otherwise input is not the first parameter in the GUI)
        super().initAlgorithm(config)

        self.order_options = ["0 (Gaussian)", 
                              "1 (First derivative of Gaussian)", 
                              "2 (Second derivative of Gaussian)", 
                              "3 (Third derivative of Gaussian)"]
        
        self.addParameter(QgsProcessingParameterEnum(
            self.ORDER,
            self.tr('Order'),
            self.order_options,
            defaultValue=0)) 
        
        self.addParameter(QgsProcessingParameterNumber(
            self.TRUNCATE,
            self.tr('Truncate filter at x standard deviations'),
            QgsProcessingParameterNumber.Type.Double,
            defaultValue=4, 
            optional=True, 
            minValue=1, 
            # maxValue=100
            ))    
        
    def get_parameters(self, parameters, context):
        kwargs = super().get_parameters(parameters, context)

        kwargs['order'] = self.parameterAsInt(parameters, self.ORDER, context) 
       
        truncate = self.parameterAsDouble(parameters, self.TRUNCATE, context)
        if truncate and truncate > 0:
            kwargs['truncate'] = truncate

        return kwargs

   

    def createInstance(self):
        return SciPyGaussianAlgorithm()
    


class SciPyGaussianGradientMagnitudeAlgorithm(SciPyAlgorithmWithSigma):
    """
    Gradient magnitude using Gaussian derivatives.


    """

    # Overwrite constants of base class
    _name = 'gaussian_gradient_magnitude'
    _displayname = 'Gaussian gradient magnitude'
    _outputname = None # If set to None, the displayname is used 
    _groupid = "edges" 

    _default_dtype = 6 # Optionally change default output dtype (value = idx of combobox)
    
    _help = """
            Gradient magnitude using Gaussian derivatives. \
            Calculated with gaussian_gradient_magnitude from \
            <a href="https://docs.scipy.org/doc/scipy/reference/ndimage.html">scipy.ndimage</a>.

            <b>Dimension</b> Calculate for each band separately (2D) \
            or use all bands as a 3D datacube and perform filter in 3D. \
            Note: bands will be the first axis of the datacube.

            <b>Sigma</b> Standard deviation of the gaussian filter.
            <b>Border mode</b> determines how input is extended around \
            the edges: <i>Reflect</i> (input is extended by reflecting at the edge), \
            <i>Constant</i> (fill around the edges with a <b>constant value</b>), \
            <i>Nearest</i> (extend by replicating the nearest pixel), \
            <i>Mirror</i> (extend by reflecting about the center of last pixel), \
            <i>Wrap</i> (extend by wrapping around to the opposite edge).

            <b>Dtype</b> Data type of output. Beware of clipping \
            and potential overflow errors if min/max of output does \
            not fit. Default is Float32.
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return ndimage.gaussian_gradient_magnitude
    
    def checkAndComplain(self, feedback):
        if self._outdtype in (1,2,4):
            msg = self.tr(f"WARNING: Output contains negative values, but output data type is unsigned integer!")
            feedback.reportError(msg, fatalError = False)

    def createInstance(self):
        return SciPyGaussianGradientMagnitudeAlgorithm()