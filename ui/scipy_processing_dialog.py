from qgis.gui import (
    QgsProcessingAlgorithmDialogBase, 
    QgsPanelWidget, 
    QgsMapLayerComboBox,
    QgsProcessingLayerOutputDestinationWidget,
    QgsCollapsibleGroupBox,
)
from qgis.PyQt.QtWidgets import (
   QWidget, QVBoxLayout, QLabel,
   QSpinBox, QCheckBox, QLineEdit, QComboBox,
   QDoubleSpinBox, 
)
from qgis.core import (
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
    QgsProcessingDestinationParameter,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsMapLayerProxyModel,
    QgsProviderRegistry,
    QgsProcessingContext,
    QgsProcessing,
    QgsProcessingOutputRasterLayer,
    QgsProperty,
    QgsProcessingUtils,
    QgsProject,
)
from qgis import processing 
from qgis.PyQt.QtCore import QTimer
from scipy_filters.ui.sizes_widget import SizesWidget
from scipy_filters.ui.structure_widget import StructureWidget, SciPyParameterStructure
from scipy_filters.ui.origin_widget import SciPyParameterOrigin, OriginWidget
from datetime import datetime


class ScipyProcessingDialog(QgsProcessingAlgorithmDialogBase):
    """
    Custom dialog that dynamically generates widgets
    for each algorithm parameter.
    """

    def __init__(self, alg, parent=None):
        super().__init__(parent)

        self._alg = alg
        

        print("init", type(alg))

        self.widgets = {}   # key: param name → value: widget instance
        self._sizewidget = None
        self.context = QgsProcessingContext()
        self.panel = QgsPanelWidget(self.parent())
        self.layout = QVBoxLayout()
        self.panel.setLayout(self.layout)
        self.advancedBox = QgsCollapsibleGroupBox(self.tr("Advanced parameters"))
        self.advancedLayout = QVBoxLayout()
        self.advancedBox.setLayout(self.advancedLayout)
        QTimer.singleShot(0, self.buildUI)
        



    def buildUI(self):
        self.setAlgorithm(self._alg)
        output_params = []
        
        for param in self._alg.parameterDefinitions():
            if isinstance(param, QgsProcessingDestinationParameter):
                output_params.append(param)
                continue
            if param.flags() & QgsProcessingParameterDefinition.Flag.FlagHidden:
                continue

            label, widget = self.createWidgetForParameter(param)
            self.add_widget(label, widget, param)

        self.layout.addWidget(self.advancedBox)

        for param in output_params:
            label, widget = self.createWidgetForParameter(param)
            self.add_widget(label, widget, param)
            widget.destinationChanged.connect(lambda name=param.name(): self.outputDestinationChanged(name))

        self.layout.addStretch()
        self.setMainWidget(self.panel)

        # Connect the origin widgets to the correct structure widget
        for _, widget in self.widgets.items():
            if isinstance(widget, OriginWidget):
                for name, w in self.widgets.items():
                    if name == widget.watch:
                        print(name)
                        w.valueChanged.connect(widget.setShape)
                        w.checknow()


    def add_widget(self, label, widget, param):
        if widget is None:
            return

        if param.flags() & QgsProcessingParameterDefinition.Flag.FlagAdvanced:
            target = self.advancedLayout
        else:
            target = self.layout

        if label is not None:
            target.addWidget(QLabel(label)) 

        name = param.name()
        self.widgets[name] = widget

        target.addWidget(widget)

    def createWidgetForParameter(self, param: QgsProcessingParameterDefinition):
        """Return (label, widget) for any supported parameter."""
        label = param.description()

        if isinstance(param, QgsProcessingParameterRasterLayer):
            w = QgsMapLayerComboBox()
            w.setFilters(QgsMapLayerProxyModel.Filter.RasterLayer)
            if param.defaultValue():
                w.setLayer(param.defaultValue())
            w.layerChanged.connect(self.inputLayerChanged)
            return label, w

        if isinstance(param, QgsProcessingParameterRasterDestination):
            w = QgsProcessingLayerOutputDestinationWidget(param, True, parent=self.panel)
            w.addOpenAfterRunningOption()
            w.setContext(self.context)
            return label, w

        if isinstance(param, QgsProcessingParameterEnum):
            w = QComboBox()
            for opt in param.options():
                w.addItem(opt)
            if param.defaultValue() is not None:
                w.setCurrentIndex(param.defaultValue())
            if param.name() == "DIMENSION":
                self._dimension = w
                self._dimension.currentIndexChanged.connect(self.dimensionChanged)
            return label, w

        if isinstance(param, QgsProcessingParameterNumber):
            if param.dataType() == QgsProcessingParameterNumber.Type.Integer:

                w = QSpinBox()
                if param.minimum() is not None:
                    w.setMinimum(int(param.minimum()))
                if param.maximum() is not None:
                    w.setMaximum(int(param.maximum()))
                if param.defaultValue() is not None:
                    w.setValue(int(param.defaultValue()))
                return label, w
            else:
                # Float
                w = QDoubleSpinBox()
                if param.minimum() is not None:
                    w.setMinimum(param.minimum())
                if param.maximum() is not None:
                    w.setMaximum(param.maximum())
                if param.defaultValue() is not None:
                    w.setValue(float(param.defaultValue()))
                return label, w
        
        if isinstance(param, SciPyParameterOrigin):
            w = OriginWidget(param.watch)
            self._dimension.currentIndexChanged.connect(w.dimensionChanged)
            return label, w

        if isinstance(param, SciPyParameterStructure):
            examples = param.examples
            try:
                to_int = param.to_int
            except AttributeError:
                to_int=None
            defaultValue = param.defaultValue()
            optional = param.isoptional
            w = StructureWidget(examples, to_int, defaultValue=defaultValue, isoptional=optional)
            self._dimension.currentIndexChanged.connect(w.dimensionChanged)
            return label, w

        if isinstance(param, QgsProcessingParameterString):
            if param.name() == "SIZES":
                meta = param.metadata()
                meta = meta.get("my_flags", {})
                if meta:
                    odd = meta.get("odd", False)
                    gtz = meta.get("positive", False)
                else:
                    odd = False 
                    gtz = False
                w = SizesWidget(odd, gtz)
                if param.defaultValue():
                    w.setValue(str(param.defaultValue()))
                self._sizewidget = w

            else:
                w = QLineEdit()

                if param.defaultValue():
                    w.setText(str(param.defaultValue()))
            return label, w
        

        # Fallback
        ptype = param.type()

        if ptype == "int":
            spin = QSpinBox()
            spin.setValue(param.defaultValue() or 0)
            spin.setRange(-999999999, 999999999)
            return label, spin

        if ptype == "boolean":
            chk = QCheckBox(label)
            chk.setChecked(bool(param.defaultValue()))
            return None, chk

        if ptype == "string":
            edit = QLineEdit()
            if param.defaultValue():
                edit.setText(str(param.defaultValue()))
            return label, edit

        print(label, "-", ptype, param)
        return None, None

    def outputDestinationChanged(self, param_name):
        widget = self.widgets[param_name]
        if widget and not widget.value():  # or appropriate check
            widget.setValue(QgsProcessing.TEMPORARY_OUTPUT)


    def getParameters(self) -> dict:
        params = {}
        for name, widget in self.widgets.items():

            # Raster layer selector
            if isinstance(widget, QgsMapLayerComboBox):
                # Use the layer's data source string; Processing algorithms
                # accept that as the raster layer parameter value.
                layer = widget.currentLayer()
                params[name] = layer.source() if layer is not None else None
                continue

            # Enum
            if isinstance(widget, QComboBox):
                params[name] = widget.currentIndex()
                continue

            # Raster destination output
            if isinstance(widget, QgsProcessingLayerOutputDestinationWidget):
                out_def = widget.value()

                sink = getattr(out_def, 'sink', None)

                if isinstance(sink, QgsProperty):
                    sinkvalue = sink.staticValue()
                else:
                    sinkvalue = ""

                if sinkvalue:
                    params[name] = out_def
                else:
                    params[name] = QgsProcessing.TEMPORARY_OUTPUT

                continue

            # Integer/float spin boxes etc.
            if hasattr(widget, "value"):  
                params[name] = widget.value()
                continue

            # Boolean
            if isinstance(widget, QCheckBox):
                params[name] = widget.isChecked()
                continue

            # Text
            if isinstance(widget, QLineEdit):
                params[name] = widget.text()
                continue

            # Fallback
            params[name] = widget

        print(params)

        return params

    def inputLayerChanged(self, layer):
        if not layer:
            return
        if layer.bandCount() > 1:
            self._dimension.setEnabled(True)
        else:
            self._dimension.setCurrentIndex(0)
            self._dimension.setEnabled(False)

    def dimensionChanged(self, dim_option):
        if self._sizewidget is not None:
            if dim_option == 1: # 3D; see enum in baseclass
                self._sizewidget.setDim(3)
            else:
                self._sizewidget.setDim(2)

    def runAlgorithm(self):
        print("Run")
        params = self.getParameters()
        if hasattr(self, "transformParameters"):
            params = self.transformParameters(params)

        valid, msg = self._alg.checkParameterValues(params, self.context)
        if not valid:
            self.messageBar().pushWarning(self.tr("Invalid Parameter"), msg)  
            return  
    
        feedback = self.createFeedback()
        self.showLog()

        feedback.pushVersionInfo()
        ts = datetime.now().isoformat(timespec='seconds')
        feedback.pushInfo(f"Algorithm {self._alg.displayName()} started at: {ts}")
        feedback.pushInfo("")
        feedback.pushInfo("Parameters:")
        feedback.pushInfo(str(params))

        try:
            results = processing.run(self._alg, params, context=self.context, feedback=feedback)
            self.setResults(results)

        except Exception as e:
            import traceback
            self.pushInfo(f"Algorithm failed: {e}")
            print(traceback.format_exc())


        for name, widget in self.widgets.items():
            if isinstance(widget, QgsProcessingLayerOutputDestinationWidget):
                if widget.openAfterRunning():     # User ticked the checkbox
                    output_path = results.get(name)
                    if output_path:
                        param = self._alg.parameterDefinition(name)
                        label = param.description() 
                        self.openOutputLayer(output_path, label)

    def openOutputLayer(self, path, name):
        """Load the output layer into QGIS."""
        layer = QgsProcessingUtils.mapLayerFromString(path, self.context)
        if layer:
            layer.setName(name)
            QgsProject.instance().addMapLayer(layer)