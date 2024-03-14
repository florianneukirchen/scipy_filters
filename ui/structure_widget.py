import os
import numpy as np

from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QPlainTextEdit, QAction

from qgis.core import *

from .dim_widget import DimsWidgetWrapper

from ..helpers import array_to_str, check_structure


uipath = os.path.dirname(__file__)

WIDGET, BASE = uic.loadUiType(
    os.path.join(uipath, 'StructureWidget.ui'))



class SciPyParameterStructure(QgsProcessingParameterString):
    def __init__(self, name, description="", defaultValue=None, multiLine=False, optional=False, examples=None, to_int=False):
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

    def __init__(self, examples, to_int=False):
        super().__init__(None)
        self.examples = examples
        self.to_int = to_int
        self.ndim = 2
        self.ok_txt = "OK"
        self.setupUi(self)

        self.toolButton.setPopupMode(QToolButton.InstantPopup) 
        self.toolButton.setText('Load')

        tool_btn_menu = QMenu(self)

        for k, v in self.examples.items():
            action = QAction(k, self)
            if isinstance(v, np.ndarray):
                if self.to_int:
                    v = array_to_str(v.astype("int"))
                else:
                    v = array_to_str(v)
                
            action.setData(v)
            tool_btn_menu.addAction(action)


        tool_btn_menu.triggered.connect(self.menu_triggered)

        self.toolButton.setMenu(tool_btn_menu)
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setText(self.ok_txt)

        self.plainTextEdit.textChanged.connect(self.checknow)


    def menu_triggered(self, checked):
        self.plainTextEdit.setPlainText(checked.data())

    def value(self):
        return self.plainTextEdit.toPlainText()

    def setDim(self, dims):
        self.ndim = dims
        self.checknow()

    def checknow(self):
        print("now")
        text = self.plainTextEdit.toPlainText()
        ok, s = check_structure(text, dims=self.ndim)
        if ok:
            self.statusLabel.setText(self.ok_txt)
        else:
            self.statusLabel.setText(s)
        


class StructureWidgetWrapper(WidgetWrapper):

    def postInitialize(self, wrappers):

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

        widget = StructureWidget(examples, to_int)
        return widget

    def value(self):
        return self.widget.value()
    





footprintexamples = {
    "3 × 3 Square": np.ones((3,3)),
    "5 × 5 Square": np.ones((5,5)),
}
