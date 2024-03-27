# -*- coding: utf-8 -*-

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


from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt.QtWidgets import QComboBox

from qgis.core import QgsProcessingParameterEnum, QgsProcessingUtils

class SciPyParameterDims(QgsProcessingParameterEnum):
    def __init__(self, name, description="", options=None, allowMultiple=False, defaultValue=None, optional=False, usesStaticStrings=False, parent_layer=None):
        self.parent_layer = parent_layer
        self.isoptional = optional
        super().__init__(name, description, options, allowMultiple, defaultValue, optional, usesStaticStrings)

    def clone(self):
        return SciPyParameterDims(self.name, self.description, self.options, self.allowMultiple, self.defaultValue, self.isoptional, self.usesStaticStrings, self.parent_layer)
    

class DimsWidgetWrapper(WidgetWrapper):
    def __init__(self,  param, dialog, row=0, col=0, **kwargs):
        self.context = dataobjects.createContext()
        self.parentLayer = None

        super().__init__(param, dialog, row=0, col=0, **kwargs)



    def postInitialize(self, wrappers):

        self.valueChanged = self.widget.currentIndexChanged

        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == "INPUT":
                self.parentLayerChanged(wrapper)
                wrapper.widgetValueHasChanged.connect(self.parentLayerChanged)



    def parentLayerChanged(self, wrapper):
        source = wrapper.parameterValue()
        self.parent_layer = QgsProcessingUtils.mapLayerFromString(source, self.context)

        if not self.parent_layer:
            return
        
        if self.parent_layer.bandCount() > 1:
            self.widget.model().item(1).setEnabled(True)
        else:
            # 3D not possible with only one band
            self.widget.setCurrentIndex(0)
            self.widget.model().item(1).setEnabled(False)

    def setValue(self, value):
        return self.widget.setCurrentIndex(value)

    def value(self):
        return self.widget.currentIndex()

    def createWidget(self):
        options = self.param.options()
        defaultValue = self.param.defaultValue()
        widget = QComboBox()
        widget.insertItems(0, options)
        widget.setCurrentIndex(defaultValue)

        return widget