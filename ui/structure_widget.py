import os
import numpy as np

from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QPlainTextEdit, QAction

from qgis.core import *

from .dim_widget import DimsWidgetWrapper

from ..helpers import array_to_str


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
        self.setupUi(self)

        self.toolButton.setPopupMode(QToolButton.InstantPopup) 
        self.toolButton.setText('...')

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


    def menu_triggered(self, checked):
        self.plainTextEdit.setPlainText(checked.data())

    def value(self):
        return self.plainTextEdit.toPlainText()


class StructureWidgetWrapper(WidgetWrapper):

    def createWidget(self):
        examples = self.param.examples
        try:
            to_int = self.param.to_int
        except AttributeError:
            to_int=None
            print("error")
        widget = StructureWidget(examples, to_int)
        return widget

    def value(self):
        return self.widget.value()
    





footprintexamples = {
    "3 × 3 Square": np.ones((3,3)),
    "5 × 5 Square": np.ones((5,5)),
}
