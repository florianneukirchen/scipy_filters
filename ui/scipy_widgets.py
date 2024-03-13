# https://github.com/qgis/QGIS/blob/master/python/plugins/processing/algs/qgis/ui/HeatmapWidgets.py

import os
import json
import numpy as np
from processing.gui.wrappers import WidgetWrapper
from processing.tools import dataobjects
from qgis.PyQt import uic

from qgis.core import *


uipath = os.path.dirname(__file__)

WIDGET, BASE = uic.loadUiType(
    os.path.join(uipath, 'SizesWidget.ui'))



class SciPyParameterSizes(QgsProcessingParameterString):
    def __init__(self, name, description="", defaultValue=None, multiLine=False, optional=False, parent_layer=None):
        self.parent_layer = parent_layer
        self.isoptional = optional

        super().__init__(name, description, defaultValue, multiLine, optional)

    def clone(self):
        return SciPyParameterSizes(self.name, self.description, self.defaultValue, self.multiLine, self.isoptional, self.parent_layer)



class SizesWidget(BASE, WIDGET):
    def __init__(self, odd=False):
        self.odd = odd # Used by Wiener
        self.context = dataobjects.createContext()
        self.ndim = 3
        self.clearvalue = 3
        super().__init__(None)
        self.setupUi(self)

        self.mSizeQgsSpinBox.setValue(self.clearvalue)
        self.mSizeQgsSpinBox.setClearValue(self.clearvalue)
        self.mSizeRowsQgsSpinBox.setClearValue(self.clearvalue)
        self.mSizeColsQgsSpinBox.setClearValue(self.clearvalue)
        self.mSizeBandsQgsSpinBox.setClearValue(0)

        self.mSizeQgsSpinBox.valueChanged.connect(self.sizeAllChanged)

        if self.odd:
            self.mSizeQgsSpinBox.setSingleStep(2)
            self.mSizeRowsQgsSpinBox.setSingleStep(2)
            self.mSizeColsQgsSpinBox.setSingleStep(2)
            self.mSizeBandsQgsSpinBox.setSingleStep(2)


    def setParentLayer(self, source):
        if not source:
            return
        self.parent_layer = QgsProcessingUtils.mapLayerFromString(source, self.context)
        if self.parent_layer.bandCount() > 1:
            self.ndim = 3
            self.mSizeBandsQgsSpinBox.setDisabled(False)
        else:
            self.ndim = 2
            self.mSizeBandsQgsSpinBox.setDisabled(True)

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

    def postInitialize(self, wrappers):

        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == "INPUT":
                self.parentLayerChanged(wrapper)
                wrapper.widgetValueHasChanged.connect(self.parentLayerChanged)

    def createWidget(self):
        return SizesWidget()
    
    def parentLayerChanged(self, wrapper):
        source = wrapper.parameterValue()
        self.widget.setParentLayer(source)

   
    def value(self):
        return self.widget.value()


class OddSizesWidgetWrapper(SizesWidgetWrapper):
    def createWidget(self):
        return SizesWidget(odd=True)    




def str_to_int_or_list(s):
    """
    Allow to have parameters for axes (one or several) or size (for all or each dimension)
    """
    out = None
    try:
        out = int(s)
    except ValueError:
        pass
    if out:
        return out
    
    if not (s[0] == "[" and s[-1] == "]"):
        s = "[" + s + "]"

    try:
        decoded = json.loads(s)
        a = np.array(decoded, dtype=np.int32)
    except (json.decoder.JSONDecodeError, ValueError, TypeError):
        raise ValueError('Can not parse string to array!')
    
    if a.ndim != 1:
        raise ValueError('Wrong dimensions!')
    
    return a.tolist()