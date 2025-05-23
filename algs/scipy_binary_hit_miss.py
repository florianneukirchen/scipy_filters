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

from qgis.core import (QgsProcessingParameterDefinition,
                       QgsProcessingException,)

from scipy_filters.scipy_algorithm_baseclasses import SciPyAlgorithm

from scipy_filters.ui.origin_widget import (OriginWidgetWrapper, 
                               SciPyParameterOrigin,)

from scipy_filters.ui.structure_widget import (StructureWidgetWrapper, 
                                  SciPyParameterStructure,)

from scipy_filters.helpers import (str_to_int_or_list, 
                      check_structure, 
                      str_to_array, 
                      morphostructexamples)

from scipy_filters.ui.i18n import tr

class SciPyBinaryHitMissAlgorithm(SciPyAlgorithm):
    """
    Preserves pixels whose neighbourhood matches structure1, but does not match the (disjoint) structure2.  
    Calculated with binary_hit_or_miss from 
    `scipy.ndimage <https://docs.scipy.org/doc/scipy/reference/ndimage.html>`_.

    .. note:: No data cells within the filter radius are filled with 0.

    **Dimension** Calculate for each band separately (2D) 
    or use all bands as a 3D datacube and perform filter in 3D. 
    
    .. note:: bands will be the first axis of the datacube.

    **Structure 1** String representation of array. 
    **Structure 2** String representation of array, disjoint to structure 1. 
    If no value is provided, the complementary of structure1 is taken.

    Both structures must have 2 dimensions if *dimension* is set to 2D. 
    Should have 3 dimensions if *dimension* is set to 3D, 
    but a 2D array is also excepted (a new axis is added as first 
    axis and the result is the same as calculating each band 
    seperately).
    """

    STRUCTURE1 = 'STRUCTURE1'
    STRUCTURE2 = 'STRUCTURE2'
    ORIGIN1 = 'ORIGIN1'
    ORIGIN2 = 'ORIGIN2'
    
    # Overwrite constants of base class
    _name = 'hit_or_miss'
    _displayname = tr('Morphological (binary) hit or miss')
    _outputname = tr("Hit or miss") # If set to None, the displayname is used 
    _groupid = 'morphological'
    
    # The function to be called
    def get_fct(self):
        return ndimage.binary_hit_or_miss
 
    def initAlgorithm(self, config):
        super().initAlgorithm(config)


        struct1_param = SciPyParameterStructure(
            self.STRUCTURE1,
            tr('Structure 1'),
            defaultValue="[[1, 1, 1],\n[1, 1, 1],\n[1, 1, 1]]",
            multiLine=True,
            optional=True,
            to_int=True,
            examples=morphostructexamples,
            )
        
        struct1_param.setMetadata({
            'widget_wrapper': {
                'class': StructureWidgetWrapper
            }
        })

        self.addParameter(struct1_param)        

        struct2_param = SciPyParameterStructure(
            self.STRUCTURE2,
            tr('Structure 2 (if empty: use complementary of structure 1)'),
            defaultValue="",
            multiLine=True,
            optional=True,
            to_int=True,
            examples=morphostructexamples,
            )
        
        struct2_param.setMetadata({
            'widget_wrapper': {
                'class': StructureWidgetWrapper
            }
        })

        self.addParameter(struct2_param)

        origin1_param = SciPyParameterOrigin(
            self.ORIGIN1,
            tr('Origin Structure 1'),
            defaultValue="0",
            optional=False,
            watch="STRUCTURE1"
            )
        
        origin1_param.setMetadata({
            'widget_wrapper': {
                'class': OriginWidgetWrapper
            }
        })

        origin1_param.setFlags(origin1_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)

        self.addParameter(origin1_param)

        origin2_param = SciPyParameterOrigin(
            self.ORIGIN2,
            tr('Origin Structure 2'),
            defaultValue="0",
            optional=False,
            watch="STRUCTURE2"
            )
        
        origin2_param.setMetadata({
            'widget_wrapper': {
                'class': OriginWidgetWrapper
            }
        })

        origin2_param.setFlags(origin2_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)

        self.addParameter(origin2_param)


    def get_parameters(self, parameters, context):
        kwargs = super().get_parameters(parameters, context)
        sizelist = [3] # used for margin

        structure1 = self.parameterAsString(parameters, self.STRUCTURE1, context)
        if structure1.strip() != "":
            kwargs['structure1'] = str_to_array(structure1, self._ndim)
            sizelist.extend(kwargs['structure1'].shape)


        structure2 = self.parameterAsString(parameters, self.STRUCTURE2, context)
        if structure2.strip() != "":
            kwargs['structure2'] = str_to_array(structure2, self._ndim)
            sizelist.extend(kwargs['structure2'].shape)

        origin1 = self.parameterAsString(parameters, self.ORIGIN1, context)
        kwargs['origin1'] = str_to_int_or_list(origin1)

        origin2 = self.parameterAsString(parameters, self.ORIGIN2, context)
        kwargs['origin2'] = str_to_int_or_list(origin2)

        self.margin = max(sizelist)

        return kwargs
    
    
    def checkParameterValues(self, parameters, context): 
        dims = self.getDimsForCheck(parameters, context)

        structure = self.parameterAsString(parameters, self.STRUCTURE1, context)
        ok, s, shape = check_structure(structure, dims)
        if not ok:
            s = tr("Could not parse structure 1 or dimensions do not match")
            return (ok, s)
        
        structure = self.parameterAsString(parameters, self.STRUCTURE2, context)
        ok, s, shape = check_structure(structure, dims)
        if not ok:
            s = tr("Could not parse structure 2 or dimensions do not match")
            return (ok, s)
        
        origin = self.parameterAsString(parameters, self.ORIGIN1, context)
        origin = str_to_int_or_list(origin)

        if isinstance(origin, list):          
            if len(origin) != dims:
                return (False, tr("Origin 1 does not match number of dimensions"))
            for i in range(dims):
                if shape[i] != 0 and not (-(shape[i] // 2) <= origin[i] <= (shape[i]-1) // 2):
                    return (False, tr("Origin 1 out of bounds of structure"))


        origin = self.parameterAsString(parameters, self.ORIGIN2, context)
        origin = str_to_int_or_list(origin)

        if isinstance(origin, list):          
            if len(origin) != dims:
                return (False, tr("Origin 2 does not match number of dimensions"))
            for i in range(dims):
                if shape[i] != 0 and not (-(shape[i] // 2) <= origin[i] <= (shape[i]-1) // 2):
                    return (False, tr("Origin 2 out of bounds of structure"))

        
        return super().checkParameterValues(parameters, context)
    
    def createInstance(self):
        return SciPyBinaryHitMissAlgorithm()