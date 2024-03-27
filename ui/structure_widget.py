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
import numpy as np
import json

from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QAction

from qgis.core import QgsProcessingParameterString


from ..helpers import array_to_str, check_structure, tr


uipath = os.path.dirname(__file__)

WIDGET, BASE = uic.loadUiType(
    os.path.join(uipath, 'StructureWidget.ui'))



class SciPyParameterStructure(QgsProcessingParameterString):
    def __init__(self, name, description="", defaultValue=None, multiLine=False, optional=True, examples=None, to_int=False):
        self.examples = examples
        self.isoptional = optional
        self.to_int = to_int

        super().__init__(name, description, defaultValue, multiLine, optional)

    def clone(self):
        return SciPyParameterStructure(self.name, 
                                       self.description, 
                                       self.defaultValue, 
                                       self.multiLine, 
                                       self.isoptional, 
                                       self.examples, 
                                       self.to_int)


class StructureWidget(BASE, WIDGET):


    def __init__(self, examples, to_int=False, defaultValue="", isoptional=True):
        super().__init__(None)
        self.examples = examples
        self.isoptional = isoptional
        self.to_int = to_int
        self.ndim = 2
        self.ok_txt = tr("OK")
        self.three_d_items = []
        self.setupUi(self)

        self.plainTextEdit.setPlainText(defaultValue)

        self.toolButton.setPopupMode(QToolButton.InstantPopup) 

        tool_btn_menu = QMenu(self)

        for k, v in self.examples.items():
            if isinstance(v, str) and v == "---":
                tool_btn_menu.addSeparator()
                continue

            action = QAction(tr(k), self)
            if isinstance(v, np.ndarray):
                if self.to_int:
                    v = array_to_str(v.astype("int"))
                else:
                    v = array_to_str(v)
                
            action.setData(v)

            if self.is3d(v):
                self.three_d_items.append(action)

            tool_btn_menu.addAction(action)


        tool_btn_menu.triggered.connect(self.menu_triggered)

        self.toolButton.setMenu(tool_btn_menu)
        self.threeDEnabled(False)
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setText(self.ok_txt)

        self.plainTextEdit.textChanged.connect(self.checknow)

    def is3d(self, check):
        """check string or np.array, return bool"""
        if isinstance(check, str):
            check = json.loads(check)
            a = np.array(check)
        if a.ndim == 3:
            return True
        return False


    def menu_triggered(self, checked):
        self.plainTextEdit.setPlainText(checked.data())

    def setValue(self, s):
        self.plainTextEdit.setPlainText(s)


    def value(self):
        return self.plainTextEdit.toPlainText()

    def setDim(self, dims):
        self.ndim = dims
        self.checknow()
        self.threeDEnabled(dims == 3)

    def checknow(self):
        text = self.plainTextEdit.toPlainText()
        ok, s, shape = check_structure(text, dims=self.ndim, optional=self.isoptional)
        if ok:
            self.statusLabel.setText(self.ok_txt)
        else:
            self.statusLabel.setText(s)
        
    def threeDEnabled(self, yes):
        for action in self.three_d_items:
            action.setEnabled(yes)


class StructureWidgetWrapper(WidgetWrapper):

    def postInitialize(self, wrappers):
        # Enable to connect from origin widget
        self.valueChanged = self.widget.plainTextEdit.textChanged

        # Watch dimension
        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == "DIMENSION":
                self.dimensionwrapper = wrapper
                wrapper.valueChanged.connect(self.dimensionChanged)

    def dimensionChanged(self, dim_option):
        if dim_option == 1: # 3D; see enum im basclass
            self.widget.setDim(3)
        else:
            self.widget.setDim(2)

    def createWidget(self):
        examples = self.param.examples
        try:
            to_int = self.param.to_int
        except AttributeError:
            to_int=None
        defaultValue = self.param.defaultValue()

        optional = self.param.isoptional
        widget = StructureWidget(examples, to_int, defaultValue=defaultValue, isoptional=optional)
        return widget

    def setValue(self, value):
        return self.widget.setValue(value)
    
    def value(self):
        return self.widget.value()
    





