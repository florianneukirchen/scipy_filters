"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
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


import os

from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt import uic

from qgis.core import QgsProcessingParameterString

from scipy_filters.helpers import check_structure, str_to_int_or_list

uipath = os.path.dirname(__file__)

WIDGET, BASE = uic.loadUiType(
    os.path.join(uipath, 'OriginWidget.ui'))


class SciPyParameterOrigin(QgsProcessingParameterString):
    def __init__(self, name, description="", defaultValue=None, multiLine=False, optional=True, watch=""):
        self.isoptional = optional
        self.watch = watch


        super().__init__(name, description, defaultValue, multiLine, optional)

    def clone(self):
        return SciPyParameterOrigin(self.name, 
                                       self.description, 
                                       self.defaultValue, 
                                       self.multiLine, 
                                       self.isoptional, 
                                       self.watch)
    

class OriginWidget(BASE, WIDGET):

    ndim = None
    shape = None

    def __init__(self, watch):
        self.context = dataobjects.createContext()
        super().__init__(None)
        self.watch = watch # name (str)
        self.watch_structure = None
        self.setupUi(self)

        self.mOriginRowsQgsSpinBox.setValue(0)
        self.mOriginColsQgsSpinBox.setValue(0)
        self.mOriginBandsQgsSpinBox.setValue(0)


        self.mOriginRowsQgsSpinBox.setClearValue(0)
        self.mOriginColsQgsSpinBox.setClearValue(0)
        self.mOriginBandsQgsSpinBox.setClearValue(0)

        self.setDim(2)


    def dimensionChanged(self, dim_option):
        if dim_option == 1: # 3D; see enum im basclass
            self.setDim(3)
        else:
            self.setDim(2)

    def setDim(self, dims):
        self.ndim = dims
        # Disable bands axis if dims == 2, otherwise enable
        self.mOriginBandsQgsSpinBox.setDisabled(dims == 2)
        self.originBandsLabel.setDisabled(dims == 2)

    # def structureChanged(self, shape):
    #     self.setShape(shape)

    def setShape(self, shape):
        self.shape = shape
        if shape == None:
            # Disable all spinboxes if no valid structure
            self.mOriginRowsQgsSpinBox.setDisabled(True)
            self.originRowsLabel.setDisabled(True)
        
            self.mOriginColsQgsSpinBox.setDisabled(True)
            self.originColsLabel.setDisabled(True)
            
            self.mOriginBandsQgsSpinBox.setDisabled(True)
            self.originBandsLabel.setDisabled(True)

            return

        # Enable spinboxes
        self.mOriginRowsQgsSpinBox.setDisabled(False)
        self.originRowsLabel.setDisabled(False)
    
        self.mOriginColsQgsSpinBox.setDisabled(False)
        self.originColsLabel.setDisabled(False)
        
        self.mOriginBandsQgsSpinBox.setDisabled(self.ndim == 2)
        self.originBandsLabel.setDisabled(self.ndim == 2)

        # origin must satisfy -(weights.shape[k] // 2) <= origin[k] <= (weights.shape[k]-1) // 2

        self.mOriginRowsQgsSpinBox.setMinimum(-(shape[-2] // 2))
        self.mOriginRowsQgsSpinBox.setMaximum((shape[-2]-1) // 2)
        # with 0, max and min is -1 instead of 0
        if shape[-2] == 0:
            self.mOriginRowsQgsSpinBox.setMaximum(0)
            self.mOriginRowsQgsSpinBox.setMinimum(0)

        self.mOriginColsQgsSpinBox.setMinimum(-(shape[-1] // 2))
        self.mOriginColsQgsSpinBox.setMaximum((shape[-1]-1) // 2)
        if shape[-1] == 0:
            self.mOriginColsQgsSpinBox.setMaximum(0)
            self.mOriginColsQgsSpinBox.setMinimum(0)

        if self.ndim == 3 and len(shape) == 3 and shape[1] != 0:
            self.mOriginBandsQgsSpinBox.setMinimum(-(shape[1] // 2))
            self.mOriginBandsQgsSpinBox.setMaximum((shape[1]-1) // 2)
        else:
            self.mOriginBandsQgsSpinBox.setMinimum(0)
            self.mOriginBandsQgsSpinBox.setMaximum(0)

    def setValue(self, s):
        if not s:
            return False
        try:
            l = str_to_int_or_list(s)
        except ValueError:
            return False
        
        if isinstance(l, int):
            self.mOriginColsQgsSpinBox.setValue(l)
            self.mOriginRowsQgsSpinBox.setValue(l)
            self.mOriginBandsQgsSpinBox.setValue(l)
            return True
        
        if not 1 < len(l) < 4:
            return False
        self.mOriginColsQgsSpinBox.setValue(l[-1])
        self.mOriginRowsQgsSpinBox.setValue(l[-2])
        if len(l) == 3:
            self.mOriginBandsQgsSpinBox.setValue(l[0])
        return True


    def value(self):
        if self.ndim == None:
            return "0"
        
        rows = self.mOriginRowsQgsSpinBox.value()
        cols = self.mOriginColsQgsSpinBox.value()
        bands = self.mOriginBandsQgsSpinBox.value()
        if self.ndim == 2:
            return f"{cols}, {rows}"
        else:
            return f"{bands}, {cols}, {rows}"


class OriginWidgetWrapper(WidgetWrapper):

    structurewrapper = None

    def postInitialize(self, wrappers):

        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == "DIMENSION":
                wrapper.valueChanged.connect(self.dimensionChanged)
            if wrapper.parameterDefinition().name() == self.param.watch:
                self.structurewrapper = wrapper
                wrapper.valueChanged.connect(self.structureChanged)
        
        self.structureChanged()

            

    def createWidget(self):
        return OriginWidget()
    

    def dimensionChanged(self, dim_option):
        if dim_option == 1: # 3D; see enum im basclass
            self.widget.setDim(3)
        else:
            self.widget.setDim(2)

    def setValue(self, value):
        return self.widget.setValue(value)

    def value(self):
        return self.widget.value()
    
    def structureChanged(self):
        if not self.structurewrapper:
            return
        structure = self.structurewrapper.value()

        ok, s, shape = check_structure(structure, dims=self.widget.ndim, optional=True)

        self.widget.setShape(shape)






