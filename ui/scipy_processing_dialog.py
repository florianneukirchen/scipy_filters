from qgis.gui import QgsProcessingAlgorithmDialogBase, QgsPanelWidget
from qgis.PyQt.QtWidgets import (
   QWidget, QVBoxLayout, QHBoxLayout, QLabel,
   QSpinBox, QCheckBox, QLineEdit, QComboBox
)
from qgis.core import QgsProcessingParameterDefinition# , QgsProcessingContext
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
       # self.context = QgsProcessingContext()
        self.panel = QgsPanelWidget(self.parent())
        self.layout = QVBoxLayout()
        self.panel.setLayout(self.layout)
        self.buildUI()



    def buildUI(self):
        


        for param in self._alg.parameterDefinitions():
            label, widget = self.createWidgetForParameter(param)

            if widget is None:
                continue

            if label is not None:
                self.layout.addWidget(QLabel(label)) 

            self.widgets[param.name()] = widget

            self.layout.addWidget(widget)

        self.setMainWidget(self.panel)

    def createWidgetForParameter(self, param: QgsProcessingParameterDefinition):
        """Factory to create widgets based on parameter type."""

        ptype = param.type()
        label = param.description()

        # Integer
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

        # Let QGIS insert its own standard widget: return None
        return None, None




    def getParameters(self) -> dict:
        params = {}
        for name, widget in self.widgets.items():
            if hasattr(widget, "value"):
                params[name] = widget.value()
            elif hasattr(widget, "isChecked"):
                params[name] = widget.isChecked()
            elif hasattr(widget, "text"):
                params[name] = widget.text()
        return params
    

    def runAlgorithm(self):
        params = self.getParameters()
        if hasattr(self, "transformParameters"):
            params = self.transformParameters(params)

        feedback = self.createFeedback()

        try:
            print("h", type(self.algorithm()))
            print("b", type(self._alg))
            results = processing.run(self.algorithm(), params, context=self.context, feedback=feedback)
            self.setResults(results)
        except Exception as e:
            self.pushInfo(f"Algorithm failed: {e}")