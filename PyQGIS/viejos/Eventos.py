from qgis.gui import QgsMapTool, QgsMapMouseEvent
from PyQt5.QtCore import Qt

class CustomMapTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

    def canvasPressEvent(self, event):
        # Manejar el evento de clic del mouse
        if event.button() == Qt.LeftButton:
            print("Clic en el mapa en la posición:", event.mapPoint())

    def activate(self):
        # Cambiar el ícono del puntero al activar la herramienta
        self.canvas.setCursor(Qt.CrossCursor)
        QgsMapTool.activate(self)

    def deactivate(self):
        # Restaurar el ícono del puntero al desactivar la herramienta
        self.canvas.unsetCursor()
        QgsMapTool.deactivate(self)

# Crear una instancia de la herramienta personalizada
custom_map_tool = CustomMapTool(iface.mapCanvas())
iface.mapCanvas().setMapTool(custom_map_tool)
