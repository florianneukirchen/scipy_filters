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
                      
from ..scipy_algorithm_baseclasses import SciPyAlgorithm


class SciPyPixelMinAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics Minimum

    """


    # Overwrite constants of base class
    _name = 'pixel_min'
    _displayname = 'Pixel minimum filter'
    _outputname = 'Pixel minimum'
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel minimum filter

            Returns minimum of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        return np.min(a, **kwargs).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        
    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
        
    def createInstance(self):
        return SciPyPixelMinAlgorithm()
    


class SciPyPixelMaxAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics Maximum

    """


    # Overwrite constants of base class
    _name = 'pixel_max'
    _displayname = 'Pixel maximum filter'
    _outputname = 'Pixel maximum'
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel maximum filter

            Returns maximum of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        return np.max(a, **kwargs).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        

    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyPixelMaxAlgorithm()
    


class SciPyPixelMeanAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics mean

    """


    # Overwrite constants of base class
    _name = 'pixel_mean'
    _displayname = 'Pixel mean filter'
    _outputname = 'Pixel mean'
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel mean filter

            Returns mean of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        return np.mean(a, **kwargs).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)

    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)        

    def createInstance(self):
        return SciPyPixelMeanAlgorithm()
    

class SciPyPixelMedianAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics median

    """

    # Overwrite constants of base class
    _name = 'pixel_median'
    _displayname = 'Pixel median filter'
    _outputname = 'Pixel median'
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel mean filter

            Returns mean of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        return np.median(a, **kwargs).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        
    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyPixelMedianAlgorithm()
    

class SciPyPixelStdAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics standard deviation

    """

    # Overwrite constants of base class
    _name = 'pixel_std'
    _displayname = 'Pixel standard deviation'
    _outputname = 'Pixel std'
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel standard deviation

            Returns standard deviation of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        return np.std(a, **kwargs).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        
    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyPixelStdAlgorithm()


class SciPyPixelVarAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics variance

    """

    # Overwrite constants of base class
    _name = 'pixel_variance'
    _displayname = 'Pixel variance'
    _outputname = None
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel variance

            Returns variance of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        return np.var(a, **kwargs).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        
    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyPixelVarAlgorithm()

class SciPyPixelRangeAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics range

    """

    # Overwrite constants of base class
    _name = 'pixel_range'
    _displayname = 'Pixel range filter'
    _outputname = 'Pixel range'
    _groupid = "pixel" 
    _outbands = 1
    _help = """
            Pixel range filter

            Returns difference of max and min of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")
        minimum = np.min(a, **kwargs)
        maximum = np.max(a, **kwargs)
        return  (maximum - minimum).astype(dtype)
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        
    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyPixelRangeAlgorithm()
    

    
class SciPyPixelMinMaxMeanAlgorithm(SciPyAlgorithm):
    """
    Pixel Statistics 

    """

    # Overwrite constants of base class
    _name = 'pixel_all'
    _displayname = 'Complete pixel statistics'
    _outputname = None
    _groupid = "pixel" 
    _outbands = 5
    _band_desc = ["Min", "Max", "Mean", "Median", "Std"]
    _help = """
            Complete pixel statistics

            Returns min, max, mean, median and std of all bands for each individual pixel
            """
    
    # The function to be called, to be overwritten
    def get_fct(self):
        return self.myfnct
    
    def myfnct(self, a, **kwargs):
        kwargs["axis"] = 0
        dtype = kwargs.pop("output")

        out = np.zeros((5, a.shape[1], a.shape[2]), dtype)

        out[0] = np.min(a, **kwargs)
        out[1] = np.max(a, **kwargs)
        out[2] = np.mean(a, **kwargs)
        out[3] = np.median(a, **kwargs)
        out[4] = np.std(a, **kwargs)
        
        return  out
    

    def initAlgorithm(self, config):
        # Set dimensions to 3
        self._dimension = self.Dimensions.threeD
        super().initAlgorithm(config)
        
    def checkParameterValues(self, parameters, context):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if layer.bandCount() == 1:
            return (False, self.tr("Pixel statistics only possible if layer has more than 1 band."))
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyPixelMinMaxMeanAlgorithm()