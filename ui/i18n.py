from qgis.PyQt.QtCore import QCoreApplication

def tr(msg):
    return QCoreApplication.translate("@default", msg)