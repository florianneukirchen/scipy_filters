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

# Helpful example on how to use widget wrapper:
# https://github.com/qgis/QGIS/blob/master/python/plugins/processing/algs/qgis/ui/HeatmapWidgets.py

import os

from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt import uic

from qgis.core import *

from .dim_widget import DimsWidgetWrapper

uipath = os.path.dirname(__file__)

WIDGET, BASE = uic.loadUiType(
    os.path.join(uipath, 'SizesWidget.ui'))



class SizesWidget(BASE, WIDGET):

    ndim = None


    def __init__(self, odd=False, gtz=False):
        self.odd = odd # Used by Wiener
        self.gtz = gtz # Used by estimate variance / std
        self.context = dataobjects.createContext()
        self.clearvalue = 3
        super().__init__(None)
        self.setupUi(self)

        self.mSizeQgsSpinBox.setValue(self.clearvalue)
        self.mSizeRowsQgsSpinBox.setValue(self.clearvalue)
        self.mSizeColsQgsSpinBox.setValue(self.clearvalue)
        self.mSizeBandsQgsSpinBox.setValue(self.clearvalue)


        self.mSizeQgsSpinBox.setClearValue(self.clearvalue)
        self.mSizeRowsQgsSpinBox.setClearValue(self.clearvalue)
        self.mSizeColsQgsSpinBox.setClearValue(self.clearvalue)
        self.mSizeBandsQgsSpinBox.setClearValue(0)

        if self.gtz:
            self.mSizeBandsQgsSpinBox.setClearValue(1)
            self.mSizeBandsQgsSpinBox.setMinimum(1)
            self.mSizeRowsQgsSpinBox.setMinimum(1)
            self.mSizeColsQgsSpinBox.setMinimum(1)
            self.mSizeQgsSpinBox.setMinimum(1)


        self.mSizeQgsSpinBox.valueChanged.connect(self.sizeAllChanged)

        if self.odd:
            self.mSizeQgsSpinBox.setSingleStep(2)
            self.mSizeRowsQgsSpinBox.setSingleStep(2)
            self.mSizeColsQgsSpinBox.setSingleStep(2)
            self.mSizeBandsQgsSpinBox.setSingleStep(2)

        self.setDim(2)


    def setDim(self, dims):
        self.ndim = dims
        # Disable bands axis if dims == 2, otherwise enable
        self.mSizeBandsQgsSpinBox.setDisabled(dims == 2)
        self.sizeBandsLabel.setDisabled(dims == 2)

    def sizeAllChanged(self):
        size = self.mSizeQgsSpinBox.value()
        self.mSizeRowsQgsSpinBox.setValue(size)
        self.mSizeColsQgsSpinBox.setValue(size)
        self.mSizeBandsQgsSpinBox.setValue(size)

        self.mSizeRowsQgsSpinBox.setClearValue(size)
        self.mSizeColsQgsSpinBox.setClearValue(size)

    def value(self):
        rows = self.mSizeRowsQgsSpinBox.value()
        cols = self.mSizeColsQgsSpinBox.value()
        bands = self.mSizeBandsQgsSpinBox.value()
        if self.ndim == 2:
            return f"{cols}, {rows}"
        else:
            return f"{bands}, {cols}, {rows}"


class SizesWidgetWrapper(WidgetWrapper):
    # dimensionwrapper = None

    def postInitialize(self, wrappers):

        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == "DIMENSION":
                wrapper.valueChanged.connect(self.dimensionChanged)
            

    def createWidget(self):
        return SizesWidget()
    

    def dimensionChanged(self, dim_option):
        if dim_option == 1: # 3D; see enum in baseclass
            self.widget.setDim(3)
        else:
            self.widget.setDim(2)


    def value(self):
        return self.widget.value()


class OddSizesWidgetWrapper(SizesWidgetWrapper):
    def createWidget(self):
        return SizesWidget(odd=True) 


class GreaterZeroSizesWidgetWrapper(SizesWidgetWrapper):
    """Sizes must be > 0 for estimate local variance / std"""
    def createWidget(self):
        return SizesWidget(gtz=True)   

