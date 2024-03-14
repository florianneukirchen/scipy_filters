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


    def __init__(self, odd=False):
        self.odd = odd # Used by Wiener
        self.context = dataobjects.createContext()
        self.ndim = None
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
                # TODO remove
                # self.dimensionwrapper = wrapper
                # self.dimensionChanged(wrapper)
                wrapper.valueChanged.connect(self.dimensionChanged)
            

    def createWidget(self):
        return SizesWidget()
    

    def dimensionChanged(self, dim_option):
        if dim_option == 1: # 3D; see enum im basclass
            self.widget.setDim(3)
        else:
            self.widget.setDim(2)


    def value(self):
        return self.widget.value()


class OddSizesWidgetWrapper(SizesWidgetWrapper):
    def createWidget(self):
        return SizesWidget(odd=True)    



