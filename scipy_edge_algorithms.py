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

import numpy as np
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
from .scipy_algorithm_baseclasses import (SciPyAlgorithm,
                                          SciPyAlgorithmWithMode,
                                          SciPyAlgorithmWithModeAxis,)



class SciPyLaplaceAlgorithm(SciPyAlgorithmWithMode):
    # Overwrite constants of base class
    _name = 'laplace'
    _displayname = 'Laplace'
    _outputname = None # If set to None, the displayname is used 
    _groupid = "edges" 
    _help = """
            Multidimensional Laplace filter based on approximate second derivatives.\
            Calculated with gaussian_laplace from \
            <a href="https://docs.scipy.org/doc/scipy/reference/ndimage.html">scipy.ndimage</a>.

            <b>Dimension</b> Calculate for each band separately (2D) \
            or use all bands as a 3D datacube and perform filter in 3D. \
            Note: bands will be the first axis of the datacube.

            <b>Border mode</b> determines how input is extended around \
            the edges: <i>Reflect</i> (input is extended by reflecting at the edge), \
            <i>Constant</i> (fill around the edges with a <b>constant value</b>), \
            <i>Nearest</i> (extend by replicating the nearest pixel), \
            <i>Mirror</i> (extend by reflecting about the center of last pixel), \
            <i>Wrap</i> (extend by wrapping around to the opposite edge).
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return ndimage.laplace

    def createInstance(self):
        return SciPyLaplaceAlgorithm()    


class SciPySobelAlgorithm(SciPyAlgorithmWithModeAxis):
    # Overwrite constants of base class
    _name = 'sobel'
    _displayname = 'Sobel'
    _outputname = None # If set to None, the displayname is used 
    _groupid = "edges" 
    _help = """
            Sobel filter. \
            Calculated with sobel from \
            <a href="https://docs.scipy.org/doc/scipy/reference/ndimage.html">scipy.ndimage</a>.

            <b>Dimension</b> Calculate for each band separately (2D) \
            or use all bands as a 3D datacube and perform filter in 3D. \
            Note: bands will be the first axis of the datacube.

            <b>Axis</b>: Find horizontal or vertical edges or in case \
            of 3D edges across the bands. Magnitude: all axes combined \
            with hypothenuse of the triangle.
            <b>Border mode</b> determines how input is extended around \
            the edges: <i>Reflect</i> (input is extended by reflecting at the edge), \
            <i>Constant</i> (fill around the edges with a <b>constant value</b>), \
            <i>Nearest</i> (extend by replicating the nearest pixel), \
            <i>Mirror</i> (extend by reflecting about the center of last pixel), \
            <i>Wrap</i> (extend by wrapping around to the opposite edge).
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfunction

    def myfunction(self, input, **kwargs):
        if self.axis_mode == 3: # Magnitude
            horiz = ndimage.sobel(input, axis=-2, **kwargs)
            vertical = ndimage.sobel(input, axis=-1, **kwargs)
            magnitude = np.hypot(horiz, vertical)
            if self._dimension == self.Dimensions.threeD:
                third = ndimage.sobel(input, axis=-3, **kwargs)
                magnitude = np.hypot(magnitude, third)
            return magnitude
        else:
            kwargs['axis'] = self.axis
            return ndimage.sobel(input, **kwargs)

    def createInstance(self):
        return SciPySobelAlgorithm()  


class SciPyPrewittAlgorithm(SciPyAlgorithmWithModeAxis):
    # Overwrite constants of base class
    _name = 'prewitt'
    _displayname = 'Prewitt'
    _outputname = None # If set to None, the displayname is used 
    _groupid = "edges" 
    _help = """
            Prewitt filter.\
            Calculated with prewitt from \
            <a href="https://docs.scipy.org/doc/scipy/reference/ndimage.html">scipy.ndimage</a>.

            <b>Dimension</b> Calculate for each band separately (2D) \
            or use all bands as a 3D datacube and perform filter in 3D. \
            Note: bands will be the first axis of the datacube.

            <b>Axis</b>: Find horizontal or vertical edges or in case \
            of 3D edges across the bands. Magnitude: all axes combined \
            with hypothenuse of the triangle.
            <b>Border mode</b> determines how input is extended around \
            the edges: <i>Reflect</i> (input is extended by reflecting at the edge), \
            <i>Constant</i> (fill around the edges with a <b>constant value</b>), \
            <i>Nearest</i> (extend by replicating the nearest pixel), \
            <i>Mirror</i> (extend by reflecting about the center of last pixel), \
            <i>Wrap</i> (extend by wrapping around to the opposite edge).
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfunction

    def myfunction(self, input, **kwargs):

        if self.axis_mode == 3: # Magnitude
            horiz = ndimage.prewitt(input, axis=-2, **kwargs)
            vertical = ndimage.prewitt(input, axis=-1, **kwargs)
            magnitude = np.hypot(horiz, vertical)
            if self._dimension == self.Dimensions.threeD:
                third = ndimage.prewitt(input, axis=-3, **kwargs)
                magnitude = np.hypot(magnitude, third)
            return magnitude
        else:
            kwargs['axis'] = self.axis
            return ndimage.prewitt(input, **kwargs)
        
    def createInstance(self):
        return SciPyPrewittAlgorithm()  
    