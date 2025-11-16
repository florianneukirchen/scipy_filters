from qgis.gui import (
    QgsProcessingAlgorithmDialogBase, 
    QgsPanelWidget, 
    QgsMapLayerComboBox,
    QgsProcessingLayerOutputDestinationWidget,
)
from qgis.PyQt.QtWidgets import (
   QWidget, QVBoxLayout, QHBoxLayout, QLabel,
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
    QgsMapLayerProxyModel,
    QgsProviderRegistry,
    QgsProcessingContext,
    QgsProcessing,
    QgsProcessingOutputRasterLayer,
    QgsProperty,
)

from qgis import processing 

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
        self.context = QgsProcessingContext()
        self.panel = QgsPanelWidget(self.parent())
        self.layout = QVBoxLayout()
        self.panel.setLayout(self.layout)
        self.buildUI()



    def buildUI(self):

        output_params = []
        
        for param in self._alg.parameterDefinitions():
            if isinstance(param, QgsProcessingDestinationParameter):
                output_params.append(param)
                continue

            label, widget = self.createWidgetForParameter(param)
            self.add_widget(label, widget, param.name())

        for param in output_params:
            label, widget = self.createWidgetForParameter(param)
            self.add_widget(label, widget, param.name())
            widget.destinationChanged.connect(lambda name=param.name(): self.outputDestinationChanged(name))

        self.setMainWidget(self.panel)

    def add_widget(self, label, widget, name):
        if widget is None:
            return

        if label is not None:
            self.layout.addWidget(QLabel(label)) 

        self.widgets[name] = widget

        self.layout.addWidget(widget)

    def createWidgetForParameter(self, param: QgsProcessingParameterDefinition):
        """Return (label, widget) for any supported parameter."""
        label = param.description()

        if isinstance(param, QgsProcessingParameterRasterLayer):
            w = QgsMapLayerComboBox()
            w.setFilters(QgsMapLayerProxyModel.RasterLayer)
            if param.defaultValue():
                w.setLayer(param.defaultValue())
            return label, w

        if isinstance(param, QgsProcessingParameterRasterDestination):
            w = QgsProcessingLayerOutputDestinationWidget(param, True, parent=self.panel)
            return label, w

        if isinstance(param, QgsProcessingParameterEnum):
            w = QComboBox()
            for opt in param.options():
                w.addItem(opt)
            if param.defaultValue() is not None:
                w.setCurrentIndex(param.defaultValue())
            return label, w

        if isinstance(param, QgsProcessingParameterNumber):
            if param.dataType() == QgsProcessingParameterNumber.Integer:

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

        ptype = param.type()

        # Integer fallback
        if ptype == "int":
            spin = QSpinBox()
            spin.setValue(param.defaultValue() or 0)
            spin.setRange(-999999999, 999999999)
            return label, spin

        # Boolean
        if ptype == "boolean":
            chk = QCheckBox(label)
            chk.setChecked(bool(param.defaultValue()))
            return None, chk

        # String
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
                print("s", sink, type(sink))

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

    

    def runAlgorithm(self):
        print("Run")
        params = self.getParameters()
        if hasattr(self, "transformParameters"):
            params = self.transformParameters(params)

        feedback = self.createFeedback()

        try:
            results = processing.run(self._alg, params, context=self.context, feedback=feedback)
            self.setResults(results)
        except Exception as e:
            import traceback
            self.pushInfo(f"Algorithm failed: {e}")
            print(traceback.format_exc())
