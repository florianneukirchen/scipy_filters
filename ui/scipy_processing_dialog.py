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
        self.buildUI()



    def buildUI(self):
        
        layout = QVBoxLayout()
        self.panel.setLayout(layout)

        for param in self._alg.parameterDefinitions():
            widget = self.createWidgetForParameter(param)

            if widget is None:
                continue

            self.widgets[param.name()] = widget

            row = QHBoxLayout()
            row.addWidget(QLabel(param.description()))
            row.addWidget(widget)

            layout.addLayout(row)

        self.setMainWidget(self.panel)

    def createWidgetForParameter(self, param: QgsProcessingParameterDefinition):
        """Factory to create widgets based on parameter type."""

        ptype = param.type()

        # Integer
        if ptype == "int":
            spin = QSpinBox()
            spin.setValue(param.defaultValue() or 0)
            spin.setRange(-999999999, 999999999)
            return spin

        # Boolean
        if ptype == "boolean":
            chk = QCheckBox()
            chk.setChecked(bool(param.defaultValue()))
            return chk

        # String
        if ptype == "string":
            edit = QLineEdit()
            if param.defaultValue():
                edit.setText(str(param.defaultValue()))
            return edit

        # Let QGIS insert its own standard widget: return None
        return None




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